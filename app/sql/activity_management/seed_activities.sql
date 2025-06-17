-- Seed the unique activities
IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Lunch')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Lunch', N'Daily lunch period', '2025-06-10T12:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Breathing Exercise')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Breathing Exercise', N'Breathing exercises', '2025-06-10T11:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Vital Check')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Vital Check', N'Patient vital signs check', '2025-06-10T09:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Routine Test', N'Routine test activity for patient', '2025-06-10T13:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Tablet Game')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Tablet Game', N'Tablet-based games', '2025-06-10T10:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Tea Break')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Tea Break', N'Daily tea break', '2025-06-10T15:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Simple Exercise')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Simple Exercise', N'Simple exercise sessions', '2025-06-10T14:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Sing Along')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Sing Along', N'Group singing sessions', '2025-06-10T11:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Art & Craft')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Art & Craft', N'Art and craft activities', '2025-06-10T11:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Reminiscence')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Reminiscence', N'Reminiscence therapy sessions', '2025-06-10T11:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Board Game')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Board Game', N'Board games', '2025-06-10T11:30:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Physio')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Physio', N'Physiotherapy sessions', '2025-06-09T11:00:00', NULL, NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Free & Easy')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (active, is_deleted, title, description, start_date, end_date, created_by_id, modified_by_id)
    VALUES (1, 0, N'Free & Easy', N'Free and easy period', '2025-06-10T10:30:00', NULL, NULL, NULL);
END
GO