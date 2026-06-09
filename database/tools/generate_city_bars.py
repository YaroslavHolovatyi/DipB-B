#!/usr/bin/env python3
"""
Generate a bars seed file for Ukrainian cities from OpenStreetMap.

WHY THIS SCRIPT EXISTS
----------------------
The Lviv seed (``database/seeds/01_lviv_bars.sql``) was produced once from the
OpenStreetMap Overpass API. This script reproduces that pipeline for every
other city already present in ``00_cities.sql`` so their bar lists are no
longer empty.

It only uses the Python standard library (urllib, hashlib, json) — no pip
installs required. It must run somewhere with outbound internet access
(your laptop), because it calls the public Overpass API.

USAGE
-----
    python3 database/tools/generate_city_bars.py
    # or limit to specific cities:
    python3 database/tools/generate_city_bars.py kyiv kharkiv odesa

Output: ``database/seeds/01z_more_cities_bars.sql``.
Then load everything with ``./database/load_seeds.sh``.

NOTES
-----
* Bars are matched by ``amenity in (bar, pub, nightclub)`` within a radius of
  each city centre (the centre coords come from ``00_cities.sql``).
* Slugs are prefixed with the city slug so they never collide with Lviv's
  un-prefixed slugs or with each other.
* ``price_category`` uses the same deterministic weighted spread as the Lviv
  seed (budget 28 / mid 45 / premium 19 / luxury 8).
* The bars upsert uses ``ON CONFLICT (slug) DO UPDATE SET price_category`` so
  re-running is safe and refreshes prices.
* Overpass is a shared free service — the script sleeps between cities. Please
  don't hammer it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUT_FILE = Path(__file__).resolve().parents[1] / "seeds" / "01z_more_cities_bars.sql"

# slug -> (display name, lat, lon, search radius in metres)
# Lviv is intentionally excluded — it already has its own seed.
CITIES: dict[str, tuple[str, float, float, int]] = {
    "kyiv":            ("Kyiv",            50.4501, 30.5234, 16000),
    "kharkiv":         ("Kharkiv",         49.9935, 36.2304, 12000),
    "odesa":           ("Odesa",           46.4825, 30.7233, 12000),
    "dnipro":          ("Dnipro",          48.4647, 35.0462, 12000),
    "donetsk":         ("Donetsk",         48.0159, 37.8028, 11000),
    "zaporizhzhia":    ("Zaporizhzhia",    47.8388, 35.1396, 11000),
    "kryvyi-rih":      ("Kryvyi Rih",      47.9105, 33.3910, 14000),
    "mykolaiv":        ("Mykolaiv",        46.9750, 31.9946, 10000),
    "mariupol":        ("Mariupol",        47.0951, 37.5497, 10000),
    "luhansk":         ("Luhansk",         48.5740, 39.3078, 10000),
    "vinnytsia":       ("Vinnytsia",       49.2331, 28.4682,  9000),
    "simferopol":      ("Simferopol",      44.9521, 34.1024,  9000),
    "sevastopol":      ("Sevastopol",      44.6166, 33.5253,  9000),
    "kherson":         ("Kherson",         46.6354, 32.6169,  9000),
    "poltava":         ("Poltava",         49.5883, 34.5514,  9000),
    "chernihiv":       ("Chernihiv",       51.4982, 31.2893,  9000),
    "cherkasy":        ("Cherkasy",        49.4444, 32.0598,  9000),
    "khmelnytskyi":    ("Khmelnytskyi",    49.4229, 26.9871,  8000),
    "chernivtsi":      ("Chernivtsi",      48.2921, 25.9358,  8000),
    "zhytomyr":        ("Zhytomyr",        50.2547, 28.6587,  8000),
    "sumy":            ("Sumy",            50.9077, 34.7981,  8000),
    "rivne":           ("Rivne",           50.6199, 26.2516,  8000),
    "ivano-frankivsk": ("Ivano-Frankivsk", 48.9226, 24.7111,  8000),
    "ternopil":        ("Ternopil",        49.5535, 25.5948,  8000),
    "lutsk":           ("Lutsk",           50.7472, 25.3254,  8000),
    "uzhhorod":        ("Uzhhorod",        48.6208, 22.2879,  8000),
    "kropyvnytskyi":   ("Kropyvnytskyi",   48.5079, 32.2623,  8000),
}

VIBES = {
    "cozy", "lively", "quiet", "craft-beer", "cocktails", "sports", "rooftop",
    "live-music", "pub", "hookah", "wine-bar", "hipster", "nightclub",
    "karaoke", "historic", "outdoor", "student", "upscale",
}

# Cyrillic (Ukrainian + Russian) -> Latin, for building ASCII slugs.
TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia", "ё": "e",
    "ы": "y", "э": "e", "ъ": "",
}


def slugify(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch in TRANSLIT:
            out.append(TRANSLIT[ch])
        elif ch.isalnum() and ch.isascii():
            out.append(ch)
        else:
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") or "bar"


def price_for(slug: str) -> str:
    h = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 100
    if h < 28:
        return "budget"
    if h < 73:
        return "mid"
    if h < 92:
        return "premium"
    return "luxury"


def vibes_for(slug: str, tags: dict) -> list[str]:
    picked: list[str] = []

    def add(v: str) -> None:
        if v in VIBES and v not in picked:
            picked.append(v)

    amenity = tags.get("amenity", "")
    name_l = tags.get("name", "").lower()
    blob = " ".join(f"{k}={v}".lower() for k, v in tags.items())

    if amenity == "pub":
        add("pub")
    if amenity == "nightclub":
        add("nightclub")
    if "microbrewery" in blob or "craft" in blob or "beer" in name_l or "пив" in name_l:
        add("craft-beer")
    if "wine" in blob or "вин" in name_l:
        add("wine-bar")
    if "cocktail" in blob or "кокте" in name_l:
        add("cocktails")
    if "karaoke" in blob or "карао" in name_l:
        add("karaoke")
    if tags.get("outdoor_seating") == "yes":
        add("outdoor")
    if "hookah" in blob or "shisha" in blob or "кальян" in name_l:
        add("hookah")
    if "rooftop" in blob:
        add("rooftop")
    if "live_music" in blob or "music" in name_l:
        add("live-music")

    # Always end with at least one, at most two — deterministic fallback.
    pool = sorted(VIBES)
    h = int(hashlib.md5((slug + "v").encode()).hexdigest(), 16)
    if not picked:
        add(pool[h % len(pool)])
    if len(picked) < 2:
        add(pool[(h // 7) % len(pool)])
    return picked[:2]


def sql_str(value) -> str:
    if value is None or value == "":
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def overpass_query(lat: float, lon: float, radius: int) -> str:
    return (
        "[out:json][timeout:90];("
        f"nwr[amenity=bar](around:{radius},{lat},{lon});"
        f"nwr[amenity=pub](around:{radius},{lat},{lon});"
        f"nwr[amenity=nightclub](around:{radius},{lat},{lon});"
        ");out center tags;"
    )


def fetch_city(lat: float, lon: float, radius: int) -> list[dict]:
    data = urllib.parse.urlencode(
        {"data": overpass_query(lat, lon, radius)}
    ).encode()
    req = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "diploma-project-seed-generator/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    return payload.get("elements", [])


def main(argv: list[str]) -> int:
    wanted = [a.lower() for a in argv[1:]] or list(CITIES)
    unknown = [c for c in wanted if c not in CITIES]
    if unknown:
        print(f"Unknown city slug(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Valid: {', '.join(CITIES)}", file=sys.stderr)
        return 2

    bar_rows: list[str] = []     # (slug, name, address, lat, lon, phone, website, price, work_hours)
    vibe_rows: list[str] = []    # (bar_slug, vibe_slug)
    per_city_counts: dict[str, int] = {}

    for ci, slug_city in enumerate(wanted):
        name, lat, lon, radius = CITIES[slug_city]
        print(f"[{ci+1}/{len(wanted)}] {name}: querying Overpass...", flush=True)
        try:
            elements = fetch_city(lat, lon, radius)
        except urllib.error.HTTPError as e:
            print(f"  ! HTTP {e.code} — Overpass busy, skipping {name}", file=sys.stderr)
            continue
        except Exception as e:  # noqa: BLE001
            print(f"  ! {type(e).__name__}: {e} — skipping {name}", file=sys.stderr)
            continue

        seen: set[str] = set()
        n = 0
        for el in elements:
            tags = el.get("tags", {})
            disp = tags.get("name") or tags.get("name:en")
            if not disp:
                continue
            la = el.get("lat") or el.get("center", {}).get("lat")
            lo = el.get("lon") or el.get("center", {}).get("lon")
            if la is None or lo is None:
                continue

            base = f"{slug_city}-{slugify(disp)}"
            slug = base
            k = 2
            while slug in seen:
                slug = f"{base}-{k}"
                k += 1
            seen.add(slug)

            addr = None
            street = tags.get("addr:street")
            house = tags.get("addr:housenumber")
            if street:
                addr = f"{street} {house}".strip() if house else street
            phone = tags.get("phone") or tags.get("contact:phone")
            website = tags.get("website") or tags.get("contact:website")
            price = price_for(slug)

            bar_rows.append(
                f"    ({sql_str(slug)}, {sql_str(disp)}, "
                f"(SELECT id FROM cities WHERE slug = {sql_str(slug_city)}), "
                f"{sql_str(addr)}, "
                f"ST_SetSRID(ST_MakePoint({lo}, {la}), 4326)::geography, "
                f"{sql_str(phone)}, {sql_str(website)}, "
                f"{sql_str(price)}::price_category, '{{}}'::jsonb, TRUE)"
            )
            for vibe in vibes_for(slug, tags):
                vibe_rows.append(f"    ({sql_str(slug)}, {sql_str(vibe)})")
            n += 1

        per_city_counts[slug_city] = n
        print(f"  -> {n} bars", flush=True)
        if ci < len(wanted) - 1:
            time.sleep(3)  # be polite to the shared Overpass instance

    if not bar_rows:
        print("No bars collected — nothing written.", file=sys.stderr)
        return 1

    parts: list[str] = []
    parts.append("-- =================================================================")
    parts.append("-- Seed: bars for all Ukrainian cities (except Lviv)")
    parts.append("-- Source: OpenStreetMap Overpass API")
    parts.append(f"-- Generated by database/tools/generate_city_bars.py")
    parts.append(f"-- Cities: {', '.join(per_city_counts)}")
    parts.append("-- =================================================================\n")
    parts.append("BEGIN;\n")
    parts.append("-- Cities themselves are seeded by 00_cities.sql; bars reference them.\n")
    parts.append("INSERT INTO bars")
    parts.append("    (slug, name, city_id, address, location,")
    parts.append("     phone, website, price_category, work_hours, is_active)")
    parts.append("VALUES")
    parts.append(",\n".join(bar_rows))
    parts.append("ON CONFLICT (slug) DO UPDATE")
    parts.append("    SET price_category = EXCLUDED.price_category;\n")

    if vibe_rows:
        parts.append("-- ── Bar ↔ Vibe associations ──────────────────────────────────────")
        parts.append("INSERT INTO bar_vibes (bar_id, vibe_id)")
        parts.append("SELECT b.id, v.id")
        parts.append("FROM (VALUES")
        parts.append(",\n".join(vibe_rows))
        parts.append(") AS pairs(bar_slug, vibe_slug)")
        parts.append("JOIN bars  b ON b.slug  = pairs.bar_slug")
        parts.append("JOIN vibes v ON v.slug = pairs.vibe_slug")
        parts.append("ON CONFLICT DO NOTHING;\n")

    parts.append("COMMIT;")
    parts.append(f"\n-- Total bars: {len(bar_rows)}  |  bar_vibes rows: {len(vibe_rows)}")
    OUT_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")

    print()
    print(f"Wrote {len(bar_rows)} bars / {len(vibe_rows)} vibe links to:")
    print(f"  {OUT_FILE}")
    print("Per-city:", {k: v for k, v in per_city_counts.items()})
    print("\nNext: ./database/load_seeds.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
