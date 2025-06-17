USE fyp_dev_cebelle;
GO

-- Example seed data (assuming activity IDs for demonstration; update IDs to match your ACTIVITY table!)
-- You can get actual IDs with: SELECT id, title FROM [dbo].[ACTIVITY];

-- Lunch (compulsory, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 1, 1, 1, 60, 60, 4, '2025-06-10T12:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Lunch';

-- Breathing Exercise (compulsory, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 1, 0, 1, 30, 30, 4, '2025-06-10T11:30:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Breathing Exercise';

-- Vital Check (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 1, 1, 0, 30, 30, 1, '2025-06-10T09:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Vital Check';

-- Routine Test (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 1, 1, 0, 30, 30, 1, '2025-06-10T13:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test';

-- Tablet Game (compulsory, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 1, 0, 0, 30, 30, 1, '2025-06-10T10:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Tablet Game';

-- Tea Break (optional, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 30, 30, 4, '2025-06-10T15:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Tea Break';

-- Simple Exercise (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 30, 30, 4, '2025-06-10T14:30:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Simple Exercise';

-- Physio (optional, individual, fixed) - Monday session
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 60, 60, 1, '2025-06-09T11:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Physio';

-- Physio (optional, individual, fixed) - Tuesday session
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 60, 60, 1, '2025-06-10T11:00:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Physio';

-- Free & Easy (optional, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_compulsory, is_fixed, is_group, min_duration, max_duration, min_people_req, start_date, end_date, active, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 30, 30, 1, '2025-06-10T10:30:00', NULL, 1, NULL, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Free & Easy';

-- Add similar INSERTs for other activities as needed...

GO