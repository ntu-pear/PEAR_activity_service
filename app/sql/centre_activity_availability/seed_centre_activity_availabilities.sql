USE activity_service_dev;
GO

--This script will only SEED activities from monday to wednesday.

-- Daily centre activity availabilities
DECLARE @mondayDate DATE = DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0);
DECLARE @CreateDate DATETIME = GETDATE();
DECLARE @i INT = 0;
DECLARE @startTime DATETIME;
DECLARE @endTime DATETIME;

-- Vital Check 9am to 10am
WHILE @i < 3
BEGIN
    SET @startTime = DATEADD(HOUR, 9, CAST(DATEADD(DAY, @i, CAST(@mondayDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, 1, @startTime, @endTime, @CreateDate, NULL, 'S85f3847c88b', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 4

    SET @i = @i + 1;
END
SET @i = 0;

-- Breathing Exercise in the morning 10am to 11am
WHILE @i < 3
BEGIN
    SET @startTime = DATEADD(HOUR, 10, CAST(DATEADD(DAY, @i, CAST(@mondayDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, 1, @startTime, @endTime, @CreateDate, NULL, 'S85f3847c88b', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 3

    SET @i = @i + 1;
END
SET @i = 0;

-- Lunch 12pm to 1pm
WHILE @i < 3
BEGIN
    SET @startTime = DATEADD(HOUR, 12, CAST(DATEADD(DAY, @i, CAST(@mondayDate AS DATE)) AS DATETIME));
    SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

    INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
        centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
    )
    SELECT id, 0, 1, @startTime, @endTime, @CreateDate, NULL, 'S85f3847c88b', NULL
    FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 1

    SET @i = @i + 1;
END
SET @i = 0;

-- Dinner 5pm to 6pm, Not needed since scheduler only shows up to 5PM.
-- WHILE @i < 7
-- BEGIN
--     SET @startTime = DATEADD(HOUR, 17, CAST(DATEADD(DAY, @i, CAST(@mondayDate AS DATE)) AS DATETIME));
--     SET @endTime = DATEADD(HOUR, 1, @startTime); -- 1 hour duration

--     INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
--         centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
--     )
--     SELECT id, 0, 1, @startTime, @endTime, @CreateDate, NULL, 'S85f3847c88b', NULL
--     FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 2

--     SET @i = @i + 1;
-- END
-- SET @i = 0;

-- Monday timetable
-- Physio 11AM - 12PM monday session
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('11:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('12:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 16

-- Tablet Game
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('13:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('14:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 5

-- Simple Exercise PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('14:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('15:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 7

-- Reminiscence PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('14:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('15:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 13

-- Tea Break
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('15:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('16:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 6

-- Sing Along PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('16:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('17:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 9

-- Board Game PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('16:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @mondayDate), CAST('17:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 15


-- Tuesday timetable
DECLARE @tuesdayDate DATE = DATEADD(DAY, 1, CAST(@mondayDate AS DATE))

-- Physio 11AM - 12PM tuesday session
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('11:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('12:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 17

-- Sing Along PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('13:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('14:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 9

-- Reminiscence PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('13:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('14:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 13

-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('14:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('15:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22

-- Tea Break
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('15:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('16:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 6

-- Tablet Game
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('16:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @tuesdayDate), CAST('17:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 5


-- Wednesday timetable
DECLARE @wednesdayDate DATE = DATEADD(DAY, 2, CAST(@mondayDate AS DATE))

-- Reminiscence AM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('11:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('12:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 12

-- Sing Along AM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('11:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('12:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 8

-- Free & Easy
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('13:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('14:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 22

-- Physio 2pm wednesday session
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 1, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('14:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('15:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 18

-- Tea Break
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('15:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('16:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 6

-- Board Game PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('16:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('17:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 15

-- Reminiscence PM
INSERT INTO [dbo].[CENTRE_ACTIVITY_AVAILABILITY] (
    centre_activity_id, is_deleted, is_fixed, start_time, end_time, created_date, modified_date, created_by_id, modified_by_id
)
SELECT id, 0, 0, DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('16:00:00' AS DATETIME)), DATEADD(DAY, DATEDIFF(DAY, 0, @wednesdayDate), CAST('17:00:00' AS DATETIME)), @CreateDate, NULL, 'S85f3847c88b', NULL
FROM [dbo].[CENTRE_ACTIVITY] WHERE activity_id = 13

GO