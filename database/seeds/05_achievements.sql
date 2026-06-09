-- =====================================================================
-- Seed: achievements catalog
-- Run after 03_races.sql (race-bound achievements use race IDs by slug).
--
-- Categories (from the achievement_category enum):
--   social      — friends, raids, groups, chats
--   exploration — visiting new bars/cities, distance/coverage
--   spending    — checks scanned, total amounts
--   quiz        — taking and completing the race quiz
--   kind_soul   — D20 "Choose One to Pay" outcomes
--   misc        — everything else (account age, profile completion, …)
--
-- The `requirement` JSONB is consumed by the achievement engine; shape varies
-- by `type`. Examples:
--   {"type":"check_count",       "threshold":10}
--   {"type":"kind_soul_total",   "threshold":1000, "currency":"UAH"}
--   {"type":"visited_bars",      "threshold":5}
--   {"type":"friends_count",     "threshold":10}
--   {"type":"profile_completion","required_fields":["avatar","race","city"]}
-- =====================================================================

INSERT INTO achievements (code, name, description, category, race_id, points, requirement) VALUES
    -- ── social ─────────────────────────────────────────────────
    ('FIRST_FRIEND',        'New Companion',
     'Add your first friend.',                                            'social',      NULL,  10,
     '{"type":"friends_count","threshold":1}'),
    ('PARTY_OF_FIVE',       'Party of Five',
     'Build a friend list of 5 people.',                                  'social',      NULL,  25,
     '{"type":"friends_count","threshold":5}'),
    ('GUILD_LEADER',        'Guild Leader',
     'Reach 25 friends.',                                                 'social',      NULL,  75,
     '{"type":"friends_count","threshold":25}'),
    ('FIRST_RAID',          'First Raid',
     'Join your first raid.',                                             'social',      NULL,  15,
     '{"type":"raids_joined","threshold":1}'),
    ('RAID_LEADER',         'Raid Leader',
     'Organize 5 raids of your own.',                                     'social',      NULL,  50,
     '{"type":"raids_organized","threshold":5}'),
    ('CHATTERBOX',          'Chatterbox',
     'Send 100 chat messages.',                                           'social',      NULL,  20,
     '{"type":"messages_sent","threshold":100}'),

    -- ── exploration ───────────────────────────────────────────
    ('FIRST_VISIT',         'First Tavern',
     'Visit your first bar.',                                             'exploration', NULL,  10,
     '{"type":"visited_bars","threshold":1}'),
    ('TAVERN_HOPPER',       'Tavern Hopper',
     'Visit 10 different bars.',                                          'exploration', NULL,  40,
     '{"type":"visited_bars","threshold":10}'),
    ('LVIV_SCHOLAR',        'Scholar of Lviv',
     'Visit 25 different bars in Lviv.',                                  'exploration', NULL, 100,
     '{"type":"visited_bars_in_city","threshold":25,"city_slug":"lviv"}'),
    ('FAVOURITES_5',        'Pinned to the Map',
     'Add 5 bars to your favourites.',                                    'exploration', NULL,  20,
     '{"type":"favorites_count","threshold":5}'),

    -- ── spending ──────────────────────────────────────────────
    ('FIRST_CHECK',         'First Receipt',
     'Scan your first receipt.',                                          'spending',    NULL,  10,
     '{"type":"check_count","threshold":1}'),
    ('TEN_CHECKS',          'Steady Patron',
     'Scan 10 receipts.',                                                 'spending',    NULL,  30,
     '{"type":"check_count","threshold":10}'),
    ('FIFTY_CHECKS',        'Regular Customer',
     'Scan 50 receipts.',                                                 'spending',    NULL,  75,
     '{"type":"check_count","threshold":50}'),
    ('TOTAL_5000_UAH',      'Mid-Tier Spender',
     'Track 5,000 UAH in total receipts.',                                'spending',    NULL,  50,
     '{"type":"total_spent","threshold":5000,"currency":"UAH"}'),

    -- ── quiz ──────────────────────────────────────────────────
    ('QUIZ_DONE',           'Know Thyself',
     'Complete the race quiz.',                                           'quiz',        NULL,  15,
     '{"type":"quiz_completed","threshold":1}'),
    ('QUIZ_RETAKE',         'Second Thoughts',
     'Retake the quiz at least once.',                                    'quiz',        NULL,  10,
     '{"type":"quiz_completed","threshold":2}'),

    -- ── kind_soul ─────────────────────────────────────────────
    ('KIND_SOUL_FIRST',     'Kind Soul',
     'Pay for the group once via the D20 dice game.',                     'kind_soul',   NULL,  25,
     '{"type":"kind_soul_count","threshold":1}'),
    ('KIND_SOUL_10',        'Patron of Friends',
     'Pay for the group 10 times.',                                       'kind_soul',   NULL, 100,
     '{"type":"kind_soul_count","threshold":10}'),
    ('KIND_SOUL_1000_UAH',  'Generous Heart',
     'Pay 1,000 UAH for friends via the dice game.',                      'kind_soul',   NULL,  60,
     '{"type":"kind_soul_total","threshold":1000,"currency":"UAH"}'),

    -- ── misc ──────────────────────────────────────────────────
    ('PROFILE_COMPLETE',    'Properly Dressed',
     'Fill out avatar, race, and home city.',                             'misc',        NULL,  15,
     '{"type":"profile_completion","required_fields":["avatar","race","city"]}'),
    ('ONE_YEAR',            'One Year In',
     'Account anniversary — one year since you joined.',                  'misc',        NULL,  50,
     '{"type":"account_age_days","threshold":365}'),
    ('REVIEW_FIRST',        'First Review',
     'Leave your first bar review.',                                      'misc',        NULL,  10,
     '{"type":"reviews_count","threshold":1}'),
    ('REVIEW_10',           'Trusted Voice',
     'Leave 10 bar reviews.',                                             'misc',        NULL,  40,
     '{"type":"reviews_count","threshold":10}')
ON CONFLICT (code) DO NOTHING;


-- ── Race-flavoured achievements (one per race, shows on profile) ────
INSERT INTO achievements (code, name, description, category, race_id, points, requirement)
SELECT
    upper('RACE_PROUD_' || r.slug),
    'Proud ' || r.name,
    'Unlock your fantasy race via the quiz: ' || r.name || '.',
    'quiz',
    r.id,
    20,
    jsonb_build_object('type','assigned_race','race_slug', r.slug)
FROM races r
ON CONFLICT (code) DO NOTHING;
