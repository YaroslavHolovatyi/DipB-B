-- =====================================================================
-- Seed: vibes  (bar atmospheres)
-- Run once before seeding bars so bar_vibes FK resolves.
-- =====================================================================

INSERT INTO vibes (slug, name, description, icon_url) VALUES
    ('cozy',        'Cozy',         'Warm lighting, soft seats, feels like home',              NULL),
    ('lively',      'Lively',       'Buzzing crowd, high energy, great atmosphere',             NULL),
    ('quiet',       'Quiet',        'Low noise, great for conversations',                       NULL),
    ('craft-beer',  'Craft Beer',   'Rotating taps, local and imported craft selections',       NULL),
    ('cocktails',   'Cocktails',    'Creative mixology, skilled bartenders',                    NULL),
    ('sports',      'Sports',       'Multiple screens, match-day crowd',                        NULL),
    ('rooftop',     'Rooftop',      'Open-air terrace or rooftop with a view',                  NULL),
    ('live-music',  'Live Music',   'Regular live bands, open mic or jazz nights',              NULL),
    ('pub',         'Pub',          'Classic pub feel, darts, board games',                     NULL),
    ('hookah',      'Hookah',       'Shisha bar with a relaxed lounge vibe',                    NULL),
    ('wine-bar',    'Wine Bar',     'Curated wine list, intimate atmosphere',                   NULL),
    ('hipster',     'Hipster',      'Indie aesthetic, vinyl records, specialty coffee',         NULL),
    ('nightclub',   'Nightclub',    'Dance floor, DJ sets, late-night energy',                  NULL),
    ('karaoke',     'Karaoke',      'Private rooms or open stage karaoke',                      NULL),
    ('historic',    'Historic',     'Heritage building, old-town location, storied interiors',  NULL),
    ('outdoor',     'Outdoor',      'Patio, garden or courtyard seating',                       NULL),
    ('student',     'Student',      'Budget-friendly, popular with uni crowd',                  NULL),
    ('upscale',     'Upscale',      'Smart-casual dress code, premium drinks, refined setting', NULL)
ON CONFLICT (slug) DO NOTHING;
