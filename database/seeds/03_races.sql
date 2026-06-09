-- =====================================================================
-- Seed: fantasy races + their drink / vibe affinities
-- Run after 00_vibes.sql and 02_drinks.sql so all FK slugs resolve.
-- =====================================================================

BEGIN;

-- ── Races ────────────────────────────────────────────────────────
INSERT INTO races (slug, name, title, description, primary_color, icon_url) VALUES
    ('human',     'Human',     'The Adaptable',
     'Versatile and curious — at home in any bar, comfortable with any drink. The well-balanced everyman.',
     '#8B5E3C', NULL),
    ('elf',       'Elf',       'The Refined',
     'Long-lived, graceful, and discerning. Drawn to elegant wine bars and quiet, sophisticated atmospheres.',
     '#A7D8B5', NULL),
    ('dwarf',     'Dwarf',     'The Stout-Hearted',
     'Hard-working, loyal, and unshakable. Favours strong beers, dim halls, and the company of close friends.',
     '#8C3A1C', NULL),
    ('halfling',  'Halfling',  'The Joyful',
     'Easygoing, social, and famously fond of second breakfasts. Loves cozy pubs and a never-ending pint.',
     '#D4A24C', NULL),
    ('orc',       'Orc',       'The Bold',
     'Fearless and loud — at home where the music is louder, the crowd is bigger, and the drinks are stronger.',
     '#4F7942', NULL),
    ('gnome',     'Gnome',     'The Inventive',
     'Curious tinkerers who like to try the weird thing on the menu. Drawn to craft beer and creative mixology.',
     '#B07AA1', NULL),
    ('tiefling',  'Tiefling',  'The Mysterious',
     'Charming, sharp-witted, and a little bit dangerous. Likes dark cocktail bars and late-night vibes.',
     '#6E2C57', NULL),
    ('dragonborn','Dragonborn','The Proud',
     'Ceremonial and proud — prefers premium spirits, upscale settings, and drinks that command respect.',
     '#C0392B', NULL)
ON CONFLICT (slug) DO NOTHING;


-- ── Race ↔ Drinks affinities (weights 1-10) ─────────────────────
INSERT INTO race_drinks (race_id, drink_id, weight)
SELECT r.id, d.id, v.weight
FROM (VALUES
    -- Human: balanced, samples everything
    ('human',     'lager',            7),
    ('human',     'old-fashioned',    6),
    ('human',     'red-wine',         6),
    ('human',     'coffee',           5),

    -- Elf: wine and refined classics
    ('elf',       'white-wine',       9),
    ('elf',       'sparkling-wine',   8),
    ('elf',       'red-wine',         7),
    ('elf',       'negroni',          6),
    ('elf',       'tea',              5),

    -- Dwarf: heavy beers, whiskey
    ('dwarf',     'stout',           10),
    ('dwarf',     'porter',           9),
    ('dwarf',     'whiskey',          8),
    ('dwarf',     'ipa',              6),

    -- Halfling: cozy beers and comfort drinks
    ('halfling',  'lager',            9),
    ('halfling',  'wheat-beer',       8),
    ('halfling',  'mulled-wine',      7),
    ('halfling',  'lviv-craft',       7),

    -- Orc: strong and loud
    ('orc',       'tequila',          9),
    ('orc',       'horilka',          9),
    ('orc',       'ipa',              7),
    ('orc',       'vodka',            7),

    -- Gnome: craft and creative
    ('gnome',     'lviv-craft',      10),
    ('gnome',     'belgian-ale',      8),
    ('gnome',     'craft-soda',       7),
    ('gnome',     'espresso-martini', 6),

    -- Tiefling: dark cocktails, late-night
    ('tiefling',  'espresso-martini', 9),
    ('tiefling',  'negroni',          9),
    ('tiefling',  'old-fashioned',    8),
    ('tiefling',  'red-wine',         6),

    -- Dragonborn: premium spirits, prestige
    ('dragonborn','whiskey',         10),
    ('dragonborn','rum',              8),
    ('dragonborn','sparkling-wine',   7),
    ('dragonborn','margarita',        6)
) AS v(race_slug, drink_slug, weight)
JOIN races  r ON r.slug  = v.race_slug
JOIN drinks d ON d.slug  = v.drink_slug
ON CONFLICT (race_id, drink_id) DO NOTHING;


-- ── Race ↔ Vibes affinities ─────────────────────────────────────
INSERT INTO race_vibes (race_id, vibe_id)
SELECT r.id, vb.id
FROM (VALUES
    ('human',     'pub'),
    ('human',     'lively'),
    ('human',     'live-music'),
    ('human',     'historic'),

    ('elf',       'wine-bar'),
    ('elf',       'quiet'),
    ('elf',       'upscale'),
    ('elf',       'rooftop'),

    ('dwarf',     'pub'),
    ('dwarf',     'craft-beer'),
    ('dwarf',     'historic'),
    ('dwarf',     'cozy'),

    ('halfling',  'cozy'),
    ('halfling',  'pub'),
    ('halfling',  'student'),
    ('halfling',  'outdoor'),

    ('orc',       'sports'),
    ('orc',       'nightclub'),
    ('orc',       'lively'),
    ('orc',       'karaoke'),

    ('gnome',     'craft-beer'),
    ('gnome',     'hipster'),
    ('gnome',     'cocktails'),
    ('gnome',     'live-music'),

    ('tiefling',  'cocktails'),
    ('tiefling',  'nightclub'),
    ('tiefling',  'hookah'),
    ('tiefling',  'upscale'),

    ('dragonborn','upscale'),
    ('dragonborn','rooftop'),
    ('dragonborn','wine-bar'),
    ('dragonborn','historic')
) AS v(race_slug, vibe_slug)
JOIN races r  ON r.slug  = v.race_slug
JOIN vibes vb ON vb.slug = v.vibe_slug
ON CONFLICT (race_id, vibe_id) DO NOTHING;

COMMIT;
