#!/usr/bin/env python3
"""
fetch_lviv_bars.py
==================
Queries OpenStreetMap via the Overpass API for bars, pubs, and nightclubs
in Lviv (or any Ukrainian city you point it at) and writes a PostgreSQL seed
file that matches the Beer & Beverages schema exactly.

Usage
-----
    pip install requests
    python scripts/fetch_lviv_bars.py                        # Lviv (default)
    python scripts/fetch_lviv_bars.py --city "Kyiv" --area-id 421866  # Kyiv
    python scripts/fetch_lviv_bars.py --out database/seeds/lviv_bars.sql

Output
------
    database/seeds/01_lviv_bars.sql   (or whatever --out points to)

The script is idempotent: it wraps everything in ON CONFLICT DO NOTHING so
you can re-run it safely as OSM data improves.

Overpass area IDs
-----------------
    Lviv  : 3602032280  (relation 2032280 → area = 3602032280)
    Kyiv  : 2804876
    Odesa : 1831151
    Kharkiv: 1830985
Tip: find the OSM relation ID at https://nominatim.openstreetmap.org/
     then add 3_600_000_000 to get the Overpass area ID.
"""

import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone

import requests

# ── configuration ────────────────────────────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

DEFAULT_CITY_SLUG = "lviv"
DEFAULT_CITY_NAME = "Lviv"
DEFAULT_AREA_ID   = 3_602_032_280   # OSM relation 2032280 (Lviv) + 3.6B

OSM_AMENITY_TAGS = ["bar", "pub", "nightclub", "biergarten"]

# Map OSM price tier tags → our enum
PRICE_MAP = {
    "1": "budget",
    "2": "mid",
    "3": "premium",
    "4": "luxury",
}

# OSM weekday abbreviations → our JSONB keys
OSM_DAY_MAP = {
    "Mo": "mon", "Tu": "tue", "We": "wed",
    "Th": "thu", "Fr": "fri", "Sa": "sat", "Su": "sun",
}

DAY_ABBR = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
DAY_KEY  = ["mon","tue","wed","thu","fri","sat","sun"]

# Vibe heuristics based on OSM tags
def guess_vibes(tags: dict) -> list[str]:
    vibes = []
    amenity   = tags.get("amenity", "")
    live_music = tags.get("live_music") or tags.get("music")
    if amenity == "nightclub":
        vibes.append("nightclub")
    if amenity in ("pub",):
        vibes.append("pub")
    if live_music in ("yes", "live"):
        vibes.append("live-music")
    if tags.get("outdoor_seating") == "yes":
        vibes.append("outdoor")
    if tags.get("sport") or tags.get("tvs") == "yes":
        vibes.append("sports")
    craft = tags.get("craft_beer") or tags.get("microbrewery")
    if craft == "yes":
        vibes.append("craft-beer")
    if tags.get("karaoke") == "yes":
        vibes.append("karaoke")
    rooftop = tags.get("roof") or tags.get("rooftop")
    if rooftop == "yes":
        vibes.append("rooftop")
    # default fallback so every bar has at least one vibe
    if not vibes:
        vibes.append("lively")
    return vibes


# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "bar"


def ensure_unique_slug(slug: str, seen: set) -> str:
    base, n = slug, 2
    while slug in seen:
        slug = f"{base}-{n}"
        n += 1
    seen.add(slug)
    return slug


def sq(s) -> str:
    """Escape a value for a SQL string literal."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def parse_opening_hours(oh: str | None) -> dict:
    """
    Convert an OSM opening_hours string into our JSONB format:
        {"mon":{"open":"12:00","close":"23:00"}, ...}

    This is a *best-effort* parser that handles common patterns:
        Mo-Fr 12:00-23:00
        Sa-Su 14:00-00:00
        Mo-Su 10:00-02:00
        24/7
    Complex rules with semicolons are split and each piece is tried in turn.
    """
    if not oh:
        return {}

    oh = oh.strip()
    if oh == "24/7":
        return {day: {"open": "00:00", "close": "24:00"} for day in DAY_KEY}

    result: dict = {}

    # Split on '; ' to handle compound rules like "Mo-Fr 12:00-22:00; Sa 14:00-23:00"
    for rule in re.split(r";\s*", oh):
        rule = rule.strip()
        # Match "Mo-Fr 09:00-22:00" or "Sa 10:00-23:00" or "Mo,We,Fr 11:00-20:00"
        m = re.match(
            r"^([A-Z][a-z](?:[,-][A-Z][a-z])*)\s+"
            r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$",
            rule,
        )
        if not m:
            continue
        days_str, open_t, close_t = m.group(1), m.group(2), m.group(3)
        # Expand ranges like Mo-Fr into individual day abbreviations
        expanded: list[str] = []
        for part in days_str.split(","):
            if "-" in part:
                start_abbr, end_abbr = part.split("-")
                if start_abbr in DAY_ABBR and end_abbr in DAY_ABBR:
                    s = DAY_ABBR.index(start_abbr)
                    e = DAY_ABBR.index(end_abbr)
                    expanded.extend(DAY_ABBR[s: e + 1])
            elif part in DAY_ABBR:
                expanded.append(part)
        for abbr in expanded:
            idx = DAY_ABBR.index(abbr)
            result[DAY_KEY[idx]] = {"open": open_t, "close": close_t}

    return result


# ── Overpass fetch ────────────────────────────────────────────────────────────

def fetch_bars(area_id: int, amenity_tags: list[str]) -> list[dict]:
    """Return a list of OSM element dicts (nodes + ways with centre coords)."""
    tag_union = "\n    ".join(
        f'nwr["amenity"="{tag}"](area.searchArea);'
        for tag in amenity_tags
    )
    query = f"""
[out:json][timeout:60];
area({area_id})->.searchArea;
(
    {tag_union}
);
out center tags;
"""
    headers = {
        "User-Agent": "BeerAndBeveragesApp/1.0 (yaroslavgolovatyy@gmail.com)",
        "Accept": "application/json",
    }
    print(f"  Querying Overpass API (area {area_id}) …", flush=True)
    for attempt in range(3):
        try:
            r = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=90)
            r.raise_for_status()
            data = r.json()
            elements = data.get("elements", [])
            print(f"  → {len(elements)} OSM elements returned")
            return elements
        except Exception as exc:
            if attempt == 2:
                raise
            wait = 10 * (attempt + 1)
            print(f"  Overpass error ({exc}), retrying in {wait}s …")
            time.sleep(wait)
    return []


# ── SQL builder ──────────────────────────────────────────────────────────────

def build_sql(
    elements: list[dict],
    city_slug: str,
    city_name: str,
) -> str:
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00")

    lines.append("-- =================================================================")
    lines.append(f"-- Seed: bars in {city_name}  —  generated {now}")
    lines.append(f"-- Source: OpenStreetMap Overpass API  (area id query)")
    lines.append(f"-- Records: {len(elements)} OSM elements")
    lines.append("-- =================================================================")
    lines.append("")
    lines.append("BEGIN;")
    lines.append("")

    # ── 1. City row ────────────────────────────────────────────────────────
    lines.append("-- ── City ─────────────────────────────────────────────────────────")
    lines.append(f"""INSERT INTO cities (slug, name, country_code, timezone)
VALUES ({sq(city_slug)}, {sq(city_name)}, 'UA', 'Europe/Kyiv')
ON CONFLICT (slug) DO NOTHING;
""")

    # ── 2. Bars ────────────────────────────────────────────────────────────
    lines.append("-- ── Bars ─────────────────────────────────────────────────────────")

    seen_slugs: set = set()
    bar_vibes_rows: list[tuple[str, str]] = []  # (bar_slug, vibe_slug)
    bar_rows: list[dict] = []

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:uk") or tags.get("name:en")
        if not name:
            continue  # skip unnamed venues

        # Coordinates (nodes have lat/lon directly; ways have centre)
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue

        slug = ensure_unique_slug(slugify(name), seen_slugs)

        address = (
            tags.get("addr:full")
            or ", ".join(filter(None, [
                tags.get("addr:street"),
                tags.get("addr:housenumber"),
            ]))
            or None
        )

        phone   = tags.get("phone") or tags.get("contact:phone") or None
        website = tags.get("website") or tags.get("contact:website") or None

        price_raw = tags.get("pricerate") or tags.get("price_level")
        price_cat = PRICE_MAP.get(str(price_raw), "mid")

        work_hours = parse_opening_hours(tags.get("opening_hours"))
        work_hours_json = json.dumps(work_hours, ensure_ascii=False)

        vibes = guess_vibes(tags)
        for v in vibes:
            bar_vibes_rows.append((slug, v))

        bar_rows.append(dict(
            slug=slug, name=name, address=address,
            lat=lat, lon=lon,
            phone=phone, website=website,
            price_cat=price_cat,
            work_hours_json=work_hours_json,
        ))

    # Bulk INSERT for bars (one per line for readability)
    if bar_rows:
        lines.append("INSERT INTO bars")
        lines.append("    (slug, name, city_id, address, location,")
        lines.append("     phone, website, price_category, work_hours, is_active)")
        lines.append("SELECT")
        lines.append("    v.slug, v.name,")
        lines.append(f"    (SELECT id FROM cities WHERE slug = {sq(city_slug)}),")
        lines.append("    v.address,")
        lines.append("    ST_SetSRID(ST_MakePoint(v.lon, v.lat), 4326)::geography,")
        lines.append("    v.phone, v.website,")
        lines.append("    v.price_category::price_category,")
        lines.append("    v.work_hours::jsonb,")
        lines.append("    TRUE")
        lines.append("FROM (VALUES")

        value_lines = []
        for r in bar_rows:
            value_lines.append(
                f"    ({sq(r['slug'])}, {sq(r['name'])}, "
                f"{sq(r['address'])}, {r['lat']}, {r['lon']}, "
                f"{sq(r['phone'])}, {sq(r['website'])}, "
                f"{sq(r['price_cat'])}, {sq(r['work_hours_json'])})"
            )
        lines.append(",\n".join(value_lines))
        lines.append(") AS v(slug, name, address, lat, lon, phone, website, price_category, work_hours)")
        lines.append("ON CONFLICT (slug) DO NOTHING;")
        lines.append("")

    # ── 3. bar_vibes ──────────────────────────────────────────────────────
    if bar_vibes_rows:
        lines.append("-- ── Bar ↔ Vibe associations ──────────────────────────────────────")
        lines.append("INSERT INTO bar_vibes (bar_id, vibe_id)")
        lines.append("SELECT b.id, v.id")
        lines.append("FROM (VALUES")

        bv_lines = [
            f"    ({sq(bar_slug)}, {sq(vibe_slug)})"
            for bar_slug, vibe_slug in bar_vibes_rows
        ]
        lines.append(",\n".join(bv_lines))
        lines.append(") AS pairs(bar_slug, vibe_slug)")
        lines.append("JOIN bars  b ON b.slug = pairs.bar_slug")
        lines.append("JOIN vibes v ON v.slug = pairs.vibe_slug")
        lines.append("ON CONFLICT DO NOTHING;")
        lines.append("")

    lines.append("COMMIT;")
    lines.append("")
    lines.append(f"-- Total bars inserted (if first run): {len(bar_rows)}")
    lines.append(f"-- Total bar_vibes rows: {len(bar_vibes_rows)}")

    return "\n".join(lines) + "\n"


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch OSM bars and generate seed SQL")
    parser.add_argument("--city",    default=DEFAULT_CITY_NAME, help="Human-readable city name")
    parser.add_argument("--slug",    default=DEFAULT_CITY_SLUG, help="City slug for DB")
    parser.add_argument("--area-id", type=int, default=DEFAULT_AREA_ID,
                        help="Overpass area ID (OSM relation + 3_600_000_000)")
    parser.add_argument("--out",     default="database/seeds/01_lviv_bars.sql",
                        help="Output SQL file path (relative to project root)")
    args = parser.parse_args()

    print(f"Beer & Beverages — Bar seeder")
    print(f"  City    : {args.city}  (slug: {args.slug})")
    print(f"  Area ID : {args.area_id}")
    print(f"  Output  : {args.out}")
    print()

    elements = fetch_bars(args.area_id, OSM_AMENITY_TAGS)
    if not elements:
        print("No elements returned — check area ID or network.", file=sys.stderr)
        sys.exit(1)

    sql = build_sql(elements, city_slug=args.slug, city_name=args.city)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(sql)

    # Count unique named bars
    named = sum(
        1 for el in elements
        if el.get("tags", {}).get("name")
        or el.get("tags", {}).get("name:uk")
        or el.get("tags", {}).get("name:en")
    )
    print(f"\n✓ Done — {named} named venues written to {args.out}")
    print(f"  (skipped {len(elements) - named} unnamed/no-name elements)")
    print()
    print("Next steps:")
    print(f"  1. Review {args.out}")
    print(f"  2. psql -U app -d beer_and_beverages -f database/seeds/00_vibes.sql")
    print(f"  3. psql -U app -d beer_and_beverages -f {args.out}")


if __name__ == "__main__":
    main()
