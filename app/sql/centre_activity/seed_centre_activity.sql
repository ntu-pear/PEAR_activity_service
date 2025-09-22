USE activity_service_dev;
GO

-- Lunch (compulsory, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 1, '2025-07-28T12:00:00', '2999-01-01T00:00:00', 60, 60, 4, '0-3,1-3,2-3,3-3,4-3', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY] 
WHERE title = N'lunch'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Breathing exercise AM (compulsory, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 1, '2025-07-28T11:30:00', '2999-01-01T00:00:00', 60, 60, 4, '0-0,1-0,2-0,3-0,4-0', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'breathing exercise AM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Vital check (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 0, '2025-07-28T09:00:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'Vital check'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Routine Test One (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 0, '2025-07-28T13:00:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'Routine Test One'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Routine Test Two (compulsory, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 1, 0, '2025-07-28T11:00:00', '2999-01-01T00:00:00', 60, 60, 1, '0-6,1-6,2-6,3-6,4-6', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'Routine Test Two'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Tablet game (compulsory, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, 0, 0, '2025-07-28T10:00:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'tablet game'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Tea break (optional, group, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 1, '2025-07-28T15:00:00', '2999-01-01T00:00:00', 60, 60, 4, '1-1,3-1', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'tea break'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- Simple exercise PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T14:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'Simple exercise PM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- sing along AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'sing along AM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- sing along PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'sing along PM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- art & craft AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'art & craft AM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- art & craft PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'art & craft PM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- reminiscence AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'reminiscence AM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- reminiscence PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'reminiscence PM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- board game AM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T11:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'board game AM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- board game PM (optional, group, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 1, '2025-07-28T13:30:00', '2999-01-01T00:00:00', 60, 60, 4, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'board game PM'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Mon 11am (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-28T11:00:00', '2999-01-01T00:00:00', 60, 60, 1, '0-1,1-2,2-1,3-4,4-5', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Mon 11am'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Tue 11am (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-29T11:00:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Tue 11am'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Wed 2pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-30T14:00:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Wed 2pm'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Thu 130pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T13:30:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Thu 130pm'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Thu 230pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T14:30:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Thu 230pm'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- physio Thu 330pm (optional, individual, fixed)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 1, 0, '2025-07-31T15:30:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'physio Thu 330pm'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );

-- free & easy (optional, individual, flexible)
INSERT INTO [dbo].[CENTRE_ACTIVITY] (
    activity_id, is_deleted, is_compulsory, is_fixed, is_group, start_date, end_date, min_duration, max_duration, min_people_req, fixed_time_slots, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, 0, 0, '2025-07-28T10:30:00', '2999-01-01T00:00:00', 60, 60, 1, '', SYSDATETIME(), NULL, 'system', NULL
FROM [dbo].[ACTIVITY]
WHERE title = N'free & easy'
  AND NOT EXISTS (
      SELECT 1 FROM [dbo].[CENTRE_ACTIVITY] ca WHERE ca.activity_id = [dbo].[ACTIVITY].id
  );
GO