USE activity_service_dev;
GO

-- Example seed data (assuming activity IDs for demonstration; update IDs to match your ACTIVITY table!)
-- You can get actual IDs with: SELECT id, title FROM [dbo].[ACTIVITY];

-- Vital Check (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 0, '2025-05-10T12:00:00', NULL, 30, 30, 1, '2025-06-10T09:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Vital Check';

-- Breathing Exercise (compulsory, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 1, '2025-05-10T12:00:00', NULL, 30, 30, 4, '2025-06-10T09:30:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Breathing Exercise AM';

-- Tablet Game (compulsory, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 0, '2025-05-10T12:00:00', NULL, 30, 30, 1, '2025-06-10T10:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Tablet Game';

-- Free & Easy (optional, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 0, '2025-05-10T12:00:00', NULL, 30, 30, 1, '2025-06-10T10:30:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Free & Easy';

-- Physio (optional, individual, fixed) - Monday session
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-05-10T12:00:00', NULL, 60, 60, 1, '2025-06-09T11:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Physio Tue 11am';

-- Lunch (compulsory, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 1, '2025-05-10T12:00:00', NULL, 60, 60, 4, '2025-06-10T12:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Lunch';

-- -- Routine Test (compulsory, individual, fixed)
-- INSERT INTO [dbo].[CENTRE_ACTIVITY] (
--     activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
-- )
-- SELECT id, 0, 1, 1, 0, '2025-05-10T12:00:00', NULL, 30, 30, 1, '2025-06-10T13:00:00', NULL, 1, NULL
-- FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test One';

-- Simple Exercise (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-05-10T12:00:00', NULL, 30, 30, 4, '2025-06-10T14:30:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Simple Exercise PM';

-- Tea Break (optional, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 1, '2025-05-10T12:00:00', NULL, 30, 60, 4, '2025-06-10T15:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Tea Break';

-- Physio (optional, individual, fixed) - Tuesday session
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-05-10T12:00:00', NULL, 60, 60, 1, '2025-06-10T16:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'art & craft PM';

-- Lunch (compulsory, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 1, '2025-05-10T12:00:00', NULL, 60, 60, 4, '2025-06-10T17:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Dinner';

-- Free & Easy (optional, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 0, '2025-05-10T12:00:00', NULL, 90, 90, 1, '2025-06-10T18:00:00', NULL, 1, NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Free & Easy';

-- Add similar INSERTs for other activities as needed...

GO