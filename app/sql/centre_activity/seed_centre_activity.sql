USE activity_service_dev;
GO

-- Lunch (compulsory, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 1, '2025-07-28T12:00:00', NULL, 60, 60, 4, '0-3,1-3,2-3,3-3,4-3', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'lunch';

-- Breathing exercise AM (compulsory, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 1, '2025-07-28T11:30:00', NULL, 30, 30, 4, '0-0,1-0,2-0,3-0,4-0', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'breathing exercise AM';

-- Vital check (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 0, '2025-07-28T09:00:00', NULL, 30, 30, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Vital check';

-- -- Routine Test One (compulsory, individual, fixed)
-- INSERT INTO [dbo].[CENTRE_ACTIVITY] (
--     activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
-- )
-- SELECT id, 0, 1, 1, 0, '2025-07-28T13:00:00', NULL, 30, 30, 1, '', SYSDATETIME(), NULL, 'system', NULL
-- FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test One';

-- -- Routine Test Two (compulsory, individual, fixed)
-- INSERT INTO [dbo].[CENTRE_ACTIVITY] (
--     activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
-- )
-- SELECT id, 0, 1, 1, 0, '2025-07-28T11:00:00', NULL, 60, 60, 1, '0-6,1-6,2-6,3-6,4-6', SYSDATETIME(), NULL, 'system', NULL
-- FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test Two';

-- Tablet game (compulsory, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 0, '2025-07-28T10:00:00', NULL, 30, 30, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'tablet game';

-- Tea break (optional, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 1, '2025-07-28T15:00:00', NULL, 30, 30, 4, '1-1,3-1', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'tea break';

-- Simple exercise PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T14:30:00', NULL, 30, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'Simple exercise PM';

-- sing along AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'sing along AM';

-- sing along PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'sing along PM';

-- art & craft AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'art & craft AM';

-- art & craft PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'art & craft PM';

-- reminiscence AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'reminiscence AM';

-- reminiscence PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'reminiscence PM';

-- board game AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'board game AM';

-- board game PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', NULL, 30, 30, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'board game PM';

-- physio Mon 11am (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-28T11:00:00', NULL, 60, 60, 1, '0-1,1-2,2-1,3-4,4-5', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Mon 11am';

-- physio Tue 11am (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-29T11:00:00', NULL, 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Tue 11am';

-- physio Wed 2pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-30T14:00:00', NULL, 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Wed 2pm';

-- physio Thu 130pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T13:30:00', NULL, 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 130pm';

-- physio Thu 230pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T14:30:00', NULL, 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 230pm';

-- physio Thu 330pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T15:30:00', NULL, 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 330pm';

-- free & easy (optional, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 0, '2025-07-28T10:30:00', NULL, 30, 30, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] WHERE title = N'free & easy';

-- dinner (compulsory, group, fixed)
-- INSERT INTO [dbo].[CENTRE_ACTIVITY] (
--     activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
-- )
-- SELECT id, 0, 1, 1, 1, '2025-07-31T19:30:00', NULL, 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
-- FROM [dbo].[ACTIVITY] WHERE title = N'dinner';
-- GO