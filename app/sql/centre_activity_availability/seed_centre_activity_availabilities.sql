-- Daily centre activity availabilities
DECLARE @startDate DATE = '2025-12-01';
DECLARE @CreateDate DATETIME = '2025-05-10T12:00:00';
DECLARE @i INT = 0;
DECLARE @startTime DATETIME;
DECLARE @endTime DATETIME;

-- Vital Check Monday to Sunday 9am to 9:30am
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 9, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(MINUTE, 30, @startTime); -- 30 minute duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 4

    SET @i = @i + 1;
END
SET @i = 0;

-- Breathing Exercise in the morning 9:30am to 10:00am
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 9, MINUTE, 30, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(MINUTE, 30, @startTime); -- 30 minute duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 3

    SET @i = @i + 1;
END
SET @i = 0;

-- Lunch Monday to Sunday 12pm to 1pm
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 12, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 1

    SET @i = @i + 1;
END
SET @i = 0;

-- Simple Exercise PM 2PM to 2:30PM
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 14, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(MINUTE, 30, @startTime); -- 30 minute duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 7

    SET @i = @i + 1;
END
SET @i = 0;

-- Tea Break 3pm to 3:30pm
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 15, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(MINUTE, 30, @startTime); -- 30 minute duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 6

    SET @i = @i + 1;
END
SET @i = 0;

-- Dinner Monday to Sunday 5pm to 6pm
WHILE @i < 7
BEGIN
    SET @startTime = DATEADD(HOUR, 17, CAST(DATEADD(DAY, @i, CAST(@startDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, @startTime, @endTime, @CreateDate, NULL, 'supervisor1', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 2

    SET @i = @i + 1;
END
SET @i = 0;

-- Monday timetable


-- Tuesday timetable
-- Tablet Game
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T9:30:00', '2025-12-02T10:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 5

-- Physio 11AM tuesday session
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T11:00:00', '2025-12-02T12:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 17

-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T13:00:00', '2025-12-02T13:30:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22

-- Art & Craft PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T13:30:00', '2025-12-02T14:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 11

-- Board Game PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T14:30:00', '2025-12-02T15:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 15

-- Sing Along PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T15:30:00', '2025-12-02T16:30:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 9

-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-02T16:30:00', '2025-12-02T17:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22


-- Wednesday timetable
-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-01T09:30:00', '2025-12-01T10:30:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22

-- Tablet Game
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-01T10:30:00', '2025-12-01T11:00:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 5

-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, '2025-12-01T11:00:00', '2025-12-01T11:30:00', '2025-05-10T12:00:00', NULL, supervisor1, NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22