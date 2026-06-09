-- =====================================================================
-- Seed: drinks  (catalog used by race affinities and later menus)
-- Run after 00_vibes.sql.
-- =====================================================================

INSERT INTO drinks (slug, name, type, description) VALUES
    -- Beers
    ('lager',            'Lager',                'beer',          'Crisp, light pale lager — the universal pub default'),
    ('ipa',              'IPA',                  'beer',          'Hoppy India Pale Ale, bitter and aromatic'),
    ('stout',            'Stout',                'beer',          'Dark, roasted, full-bodied beer'),
    ('wheat-beer',       'Wheat Beer',           'beer',          'Pale, cloudy, citrus-forward wheat beer'),
    ('porter',           'Porter',               'beer',          'Dark malt, chocolate and coffee notes'),
    ('belgian-ale',      'Belgian Ale',          'beer',          'Strong, fruity, slightly sweet'),
    ('lviv-craft',       'Lviv Craft',           'beer',          'Local Lviv craft beer flight'),
    -- Spirits
    ('whiskey',          'Whiskey',              'spirit',        'Single malt, bourbon or rye'),
    ('vodka',            'Vodka',                'spirit',        'Neat or with a chaser'),
    ('rum',              'Rum',                  'spirit',        'Aged or spiced rum'),
    ('gin',              'Gin',                  'spirit',        'Juniper-led classic gin'),
    ('tequila',          'Tequila',              'spirit',        'Blanco, reposado or añejo'),
    ('horilka',          'Horilka',              'spirit',        'Ukrainian honey-pepper horilka'),
    -- Cocktails
    ('old-fashioned',    'Old Fashioned',        'cocktail',      'Whiskey, sugar, bitters'),
    ('negroni',          'Negroni',              'cocktail',      'Gin, Campari, sweet vermouth'),
    ('mojito',           'Mojito',               'cocktail',      'Rum, lime, mint, soda'),
    ('margarita',        'Margarita',            'cocktail',      'Tequila, triple sec, lime'),
    ('espresso-martini', 'Espresso Martini',     'cocktail',      'Vodka, coffee liqueur, espresso'),
    ('aperol-spritz',    'Aperol Spritz',        'cocktail',      'Aperol, prosecco, soda'),
    -- Wine
    ('red-wine',         'Red Wine',             'wine',          'Full-bodied or light red — by glass or bottle'),
    ('white-wine',       'White Wine',           'wine',          'Crisp, dry or off-dry white'),
    ('sparkling-wine',   'Sparkling Wine',       'wine',          'Prosecco, cava or champagne'),
    ('mulled-wine',      'Mulled Wine',          'wine',          'Hot spiced wine — winter classic'),
    -- Non-alcoholic
    ('mocktail',         'Mocktail',             'non_alcoholic', 'Alcohol-free cocktail of the day'),
    ('craft-soda',       'Craft Soda',           'non_alcoholic', 'House-made artisan soda'),
    ('coffee',           'Coffee',               'non_alcoholic', 'Espresso, latte or pour-over'),
    ('tea',              'Tea',                  'non_alcoholic', 'Black, green or herbal tea')
ON CONFLICT (slug) DO NOTHING;
