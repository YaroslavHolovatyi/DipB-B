-- =================================================================
-- Seed: Ukrainian cities — all 24 oblast centers + Kyiv (capital) and
-- the Autonomous Republic of Crimea / Sevastopol centers.
-- country_code defaults to 'UA', timezone to 'Europe/Kyiv'.
-- Coordinates are city-centre points (WGS84 lon/lat).
-- Idempotent: ON CONFLICT (slug) DO NOTHING.
-- =================================================================

BEGIN;

INSERT INTO cities (slug, name, country_code, timezone, location)
SELECT
    c.slug, c.name, 'UA', 'Europe/Kyiv',
    ST_SetSRID(ST_MakePoint(c.lon, c.lat), 4326)::geography
FROM (VALUES
    ('kyiv',            'Kyiv',             30.5234, 50.4501),
    ('kharkiv',         'Kharkiv',          36.2304, 49.9935),
    ('odesa',           'Odesa',            30.7233, 46.4825),
    ('dnipro',          'Dnipro',           35.0462, 48.4647),
    ('donetsk',         'Donetsk',          37.8028, 48.0159),
    ('zaporizhzhia',    'Zaporizhzhia',     35.1396, 47.8388),
    ('lviv',            'Lviv',             24.0297, 49.8397),
    ('kryvyi-rih',      'Kryvyi Rih',       33.3910, 47.9105),
    ('mykolaiv',        'Mykolaiv',         31.9946, 46.9750),
    ('mariupol',        'Mariupol',         37.5497, 47.0951),
    ('luhansk',         'Luhansk',          39.3078, 48.5740),
    ('vinnytsia',       'Vinnytsia',        28.4682, 49.2331),
    ('simferopol',      'Simferopol',       34.1024, 44.9521),
    ('sevastopol',      'Sevastopol',       33.5253, 44.6166),
    ('kherson',         'Kherson',          32.6169, 46.6354),
    ('poltava',         'Poltava',          34.5514, 49.5883),
    ('chernihiv',       'Chernihiv',        31.2893, 51.4982),
    ('cherkasy',        'Cherkasy',         32.0598, 49.4444),
    ('khmelnytskyi',    'Khmelnytskyi',     26.9871, 49.4229),
    ('chernivtsi',      'Chernivtsi',       25.9358, 48.2921),
    ('zhytomyr',        'Zhytomyr',         28.6587, 50.2547),
    ('sumy',            'Sumy',             34.7981, 50.9077),
    ('rivne',           'Rivne',            26.2516, 50.6199),
    ('ivano-frankivsk', 'Ivano-Frankivsk',  24.7111, 48.9226),
    ('ternopil',        'Ternopil',         25.5948, 49.5535),
    ('lutsk',           'Lutsk',            25.3254, 50.7472),
    ('uzhhorod',        'Uzhhorod',         22.2879, 48.6208),
    ('kropyvnytskyi',   'Kropyvnytskyi',    32.2623, 48.5079)
) AS c(slug, name, lon, lat)
ON CONFLICT (slug) DO NOTHING;

COMMIT;
