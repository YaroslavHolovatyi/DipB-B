-- =====================================================================
-- Seed: race-assignment quiz
-- Run after 03_races.sql (answers map to race IDs by slug).
--
-- Schema recap:
--   quiz_questions(position, text, ...)
--   quiz_answers(question_id, text, position)
--   quiz_answer_races(answer_id, race_id, score)   ← scoring
--
-- Conventions:
--   * 10 questions, 4 answers each
--   * each answer awards 1-3 points to one or two races
--   * highest-total race wins
-- =====================================================================

BEGIN;

-- Truncate any prior quiz seed (idempotent re-run) — but only if no users
-- have completed it (FK from user_quiz_results points at races, not answers,
-- so this is safe but we still bail if there's quiz history).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM user_quiz_results LIMIT 1) THEN
        RAISE NOTICE 'user_quiz_results has rows — skipping quiz reseed';
    ELSE
        DELETE FROM quiz_answer_races;
        DELETE FROM quiz_answers;
        DELETE FROM quiz_questions;
    END IF;
END $$;


-- ── Questions ────────────────────────────────────────────────────
INSERT INTO quiz_questions (position, text) VALUES
    (1,  'It''s Friday night. Where are you headed?'),
    (2,  'Your drink of choice is...'),
    (3,  'What''s your ideal crowd?'),
    (4,  'Pick a setting:'),
    (5,  'When the bill comes, you usually...'),
    (6,  'Your music preference for a night out?'),
    (7,  'How adventurous are you with the menu?'),
    (8,  'Pick a moment of the night:'),
    (9,  'Your weekend vibe is...'),
    (10, 'When friends invite you out, you...');


-- ── Answers + race scoring ───────────────────────────────────────
-- A tiny helper macro: insert one answer and its race scores.
DO $seed$
DECLARE
    qid BIGINT;
    aid BIGINT;
BEGIN

----------------------------- Q1 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 1;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A cozy pub with my closest friends',   1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'halfling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'dwarf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A wine bar in the old town', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'dragonborn';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A loud sports bar — game day!', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'human';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A speakeasy with hidden cocktails', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'gnome';

----------------------------- Q2 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 2;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A pint of dark stout', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dwarf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A glass of dry white wine', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A shot of horilka, no chaser', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'An espresso martini — show me the menu', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'gnome';

----------------------------- Q3 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 3;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A small, tight-knit group I know well', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'halfling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'dwarf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A polished, smart crowd', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dragonborn';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'elf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A massive, energetic crowd — the bigger the better', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'human';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Interesting strangers who turn out to be interesting people', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'gnome';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'tiefling';

----------------------------- Q4 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 4;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Open-air rooftop with a city view', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dragonborn';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'elf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Wood-panelled cellar pub with candles', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dwarf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Smoky cocktail bar lit only by neon', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A quirky craft-beer hall full of taps', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'gnome';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'human';

----------------------------- Q5 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 5;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Split exactly by what each person ordered', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'human';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Offer to grab the whole bill', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dragonborn';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Roll the dice — whoever loses pays', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'tiefling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Just round up and split evenly', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'human';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'dwarf';

----------------------------- Q6 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 6;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Live acoustic — guitars and jazz', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'gnome';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Classic rock and stadium anthems', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'human';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'dwarf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Heavy bass and DJ sets till 4am', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'tiefling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Whatever the bar plays — I''m not picky', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

----------------------------- Q7 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 7;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'I always order the strangest item on the menu', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'gnome';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'I have one signature drink and stick to it', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dwarf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'I ask the bartender what they''d make me', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'elf';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'I read the whole menu and pick exactly the right thing', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'human';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'dragonborn';

----------------------------- Q8 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 8;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'First drink, just sitting down, the night ahead', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'human';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Last call, everyone on the dance floor', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, '2am sitting on a rooftop with my closest friend', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'dragonborn';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'A perfect quiet table, candlelight, real conversation', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

----------------------------- Q9 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 9;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Stay in, cook, chill', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'halfling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Adventure — hiking, road trip, something new', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'gnome';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'orc';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Brunch, gallery, then drinks somewhere photogenic', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'elf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'dragonborn';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Whatever the group is doing, I''m in', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'human';

----------------------------- Q10 -----------------------------
SELECT id INTO qid FROM quiz_questions WHERE position = 10;

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Suggest the bar — I have a favourite', 1) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'dwarf';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 2 FROM races WHERE slug = 'halfling';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Plan the night — bookings, route, backup plan', 2) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'human';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'dragonborn';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Just show up, see what happens', 3) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'tiefling';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'gnome';

INSERT INTO quiz_answers (question_id, text, position) VALUES
    (qid, 'Try to one-up them with somewhere wilder', 4) RETURNING id INTO aid;
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 3 FROM races WHERE slug = 'orc';
INSERT INTO quiz_answer_races (answer_id, race_id, score)
SELECT aid, id, 1 FROM races WHERE slug = 'gnome';

END;
$seed$;

COMMIT;
