USE fyp_dev_zihao; /*Change to your database name*/
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[activity] WHERE id = '11111111-1111-1111-1111-111111111111')
BEGIN
    INSERT INTO [dbo].[activity] (
        id, title, description,
        start_date, end_date,
        is_fixed, is_compulsory, is_group,
        min_duration, max_duration, min_people_required
    ) VALUES (
        '11111111-1111-1111-1111-111111111111',
        N'Morning Walk',
        N'Gentle stroll around the garden',
        '2025-06-10T09:00:00',
        NULL,
        0, 0, 0,
        30, 60, 1
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[activity] WHERE id = '22222222-2222-2222-2222-222222222222')
BEGIN
    INSERT INTO [dbo].[activity] (
        id, title, description,
        start_date, end_date,
        is_fixed, is_compulsory, is_group,
        min_duration, max_duration, min_people_required
    ) VALUES (
        '22222222-2222-2222-2222-222222222222',
        N'Group Yoga',
        N'Yoga session—up to 8 participants',
        '2025-06-11T08:00:00',
        NULL,
        1, 0, 1,
        60, 60, 8
    );
END
GO