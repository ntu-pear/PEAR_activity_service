-- Seed the activities with new structure
IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'lunch')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'lunch', N'daily lunch 12nn-1pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'breathing exercise AM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'breathing exercise AM', N'daily 30 minutes before lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Vital check')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'Vital check', N'check patient vitals daily 9am-9:30am', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test One')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'Routine Test One', N'Routine activity for patient Test One - Mon to Fri 1pm-130pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Routine Test Two')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'Routine Test Two', N'Routine activity for patient Test Two - Fri 11am-12nn', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'tablet game')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'tablet game', N'30 minute session', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'tea break')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'tea break', N'daily tea break 3pm - 330pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'Simple exercise PM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'Simple exercise PM', N'daily 30 minutes after 2pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'sing along AM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'sing along AM', N'available daily 30 minutes before lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'sing along PM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'sing along PM', N'available daily 30 minutes after lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'art & craft AM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'art & craft AM', N'available daily 30 minutes before lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'art & craft PM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'art & craft PM', N'available daily 30 minutes after lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'reminiscence AM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'reminiscence AM', N'available daily 30 minutes before lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'reminiscence PM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'reminiscence PM', N'available daily 30 minutes after lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'board game AM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'board game AM', N'available daily 30 minutes before lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'board game PM')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'board game PM', N'available daily 30 minutes after lunch', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Mon 11am')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Mon 11am', N'physio Mon 11am-12nn', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Tue 11am')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Tue 11am', N'physio Tue 11am-12nn', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Wed 2pm')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Wed 2pm', N'physio Wed 2pm-3pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 130pm')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Thu 130pm', N'physio Thu 130pm-230pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 230pm')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Thu 230pm', N'physio Thu 230pm-330pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'physio Thu 330pm')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'physio Thu 330pm', N'physio Thu 330pm-430pm', NULL, NULL);
END

IF NOT EXISTS (SELECT 1 FROM [dbo].[ACTIVITY] WHERE title = N'free & easy')
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (is_deleted, title, description, created_by_id, modified_by_id)
    VALUES (0, N'free & easy', N'free & easy for 30 minutes', NULL, NULL);
END
GO