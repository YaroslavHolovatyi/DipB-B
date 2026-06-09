-- =====================================================================
-- Seed: dnd_class_info — the twelve 5e classes shown in Tavern Tales
-- character creation. PK is the dnd_class enum value.
-- =====================================================================

INSERT INTO dnd_class_info (slug, name, description, hit_die, primary_ability) VALUES
    ('barbarian', 'Barbarian',
     'A fierce warrior who can enter a battle rage. High HP, brutal damage.',
     12, 'Strength'),
    ('bard',      'Bard',
     'A magical performer whose music inspires allies and bewilders foes.',
     8,  'Charisma'),
    ('cleric',    'Cleric',
     'A priestly champion who wields divine magic in service to a higher power.',
     8,  'Wisdom'),
    ('druid',     'Druid',
     'A priest of nature, wielding elemental power and shape-shifting into beasts.',
     8,  'Wisdom'),
    ('fighter',   'Fighter',
     'A master of martial combat — skilled with weapons and armour.',
     10, 'Strength or Dexterity'),
    ('monk',      'Monk',
     'A martial artist who uses ki to perform supernatural feats.',
     8,  'Dexterity & Wisdom'),
    ('paladin',   'Paladin',
     'A holy warrior bound by sacred oath, blending martial and divine magic.',
     10, 'Strength & Charisma'),
    ('ranger',    'Ranger',
     'A skilled hunter and tracker with a bond to nature and a chosen enemy.',
     10, 'Dexterity & Wisdom'),
    ('rogue',     'Rogue',
     'A scoundrel who uses stealth, cunning, and sneak attacks to win the day.',
     8,  'Dexterity'),
    ('sorcerer',  'Sorcerer',
     'A spellcaster who draws magic from an innate bloodline or magical accident.',
     6,  'Charisma'),
    ('warlock',   'Warlock',
     'A wielder of magic granted by a pact with an extraplanar patron.',
     8,  'Charisma'),
    ('wizard',    'Wizard',
     'A scholarly magic-user capable of manipulating the structures of reality.',
     6,  'Intelligence')
ON CONFLICT (slug) DO NOTHING;
