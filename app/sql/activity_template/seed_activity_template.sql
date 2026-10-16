-- Seeds the standard activity templates.
--
-- These four cover the configuration patterns already present in the live data:
-- of 30 active centre activities, 28 match one of them. The supervisor picks a
-- template, supplies the real title and time slots, and applies it.
--
-- They are deliberately generic. A template named "Physiotherapy" would be a
-- guess about what a centre offers; "Individual session" is a shape, and the
-- supervisor names the activity when applying.
--
-- Run against dev, staging and the CI test database. Idempotent: each row is
-- inserted only if a template with that name does not already exist, so
-- re-running will not duplicate or overwrite.
--
-- IMPORTANT: these rows bypass Pydantic validation, so they must satisfy the
-- rules in app/schemas/activity_rules.py by construction, or a supervisor will
-- be unable to re-save a template loaded from here. In particular:
--   - a group template needs min_people_req >= 2, an individual one exactly 1
--   - min_duration must equal max_duration, and both must be 30 or 60
--   - compulsory implies fixed, and both require fixed_time_slots
--   - every slot must parse as 'Day HH:MM'
-- tests/unit/test_activity_template_seed.py asserts all four still pass.

-- 1. Compulsory daily care
-- Matches: Breathing exercise, Vital Check AM/PM, tablet game.
-- Compulsory, so it must be fixed and must carry slots. The weekday 10:00
-- pattern is a starting point the supervisor is expected to change.
IF NOT EXISTS (SELECT 1 FROM dbo.ACTIVITY_TEMPLATE WHERE name = 'Compulsory daily care' AND is_deleted = 0)
INSERT INTO dbo.ACTIVITY_TEMPLATE
    (name, title, description, is_compulsory, is_fixed, is_group,
     start_date, end_date, min_duration, max_duration, min_people_req,
     fixed_time_slots, is_deleted, created_date, created_by_id)
VALUES
    ('Compulsory daily care', 'Daily care activity',
     'A care task every patient attends at a fixed time each weekday.',
     1, 1, 0,
     CAST(GETDATE() AS DATE), '2999-01-01', 60, 60, 1,
     'Monday 10:00,Tuesday 10:00,Wednesday 10:00,Thursday 10:00,Friday 10:00',
     0, GETDATE(), '1');

-- 2. Group session
-- Matches: Art & Craft, Board Game, Reminiscence, Sing along, Tee break.
-- Flexible by default so the Scheduler can place it; the supervisor can fix it
-- to a slot afterwards.
IF NOT EXISTS (SELECT 1 FROM dbo.ACTIVITY_TEMPLATE WHERE name = 'Group session' AND is_deleted = 0)
INSERT INTO dbo.ACTIVITY_TEMPLATE
    (name, title, description, is_compulsory, is_fixed, is_group,
     start_date, end_date, min_duration, max_duration, min_people_req,
     fixed_time_slots, is_deleted, created_date, created_by_id)
VALUES
    ('Group session', 'Group activity',
     'A shared activity run for a small group of patients.',
     0, 0, 1,
     CAST(GETDATE() AS DATE), '2999-01-01', 60, 60, 4,
     NULL,
     0, GETDATE(), '1');

-- 3. Quiet individual activity
-- Matches: Colouring, Memory Cards, Puzzle Time. The 30-minute shape, used to
-- fill short gaps in a schedule.
IF NOT EXISTS (SELECT 1 FROM dbo.ACTIVITY_TEMPLATE WHERE name = 'Quiet individual activity' AND is_deleted = 0)
INSERT INTO dbo.ACTIVITY_TEMPLATE
    (name, title, description, is_compulsory, is_fixed, is_group,
     start_date, end_date, min_duration, max_duration, min_people_req,
     fixed_time_slots, is_deleted, created_date, created_by_id)
VALUES
    ('Quiet individual activity', 'Quiet activity',
     'A short solo activity, useful for filling gaps in a schedule.',
     0, 0, 0,
     CAST(GETDATE() AS DATE), '2999-01-01', 30, 30, 1,
     NULL,
     0, GETDATE(), '1');

-- 4. Individual session
-- Matches: Physiotherapy, Gardening, Light Stretching, Music Listening,
-- Storytelling. This is the one that replaces the six separate "physio ..."
-- activities with one template applied six times.
IF NOT EXISTS (SELECT 1 FROM dbo.ACTIVITY_TEMPLATE WHERE name = 'Individual session' AND is_deleted = 0)
INSERT INTO dbo.ACTIVITY_TEMPLATE
    (name, title, description, is_compulsory, is_fixed, is_group,
     start_date, end_date, min_duration, max_duration, min_people_req,
     fixed_time_slots, is_deleted, created_date, created_by_id)
VALUES
    ('Individual session', 'Individual activity',
     'A one-to-one session, applied once per time slot it runs at.',
     0, 0, 0,
     CAST(GETDATE() AS DATE), '2999-01-01', 60, 60, 1,
     NULL,
     0, GETDATE(), '1');
