USE activity_service_dev; /*Change to your database name*/
GO

IF NOT EXISTS (
    SELECT 1
      FROM [dbo].[ACTIVITY]
     WHERE TITLE = N'Morning Walk'
)
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (
        ACTIVE,
        IS_DELETED,
        TITLE,
        DESCRIPTION,
        START_DATE,
        END_DATE,
        CREATED_BY_ID,
        MODIFIED_BY_ID
    ) VALUES (
        1,                       
        0,                      
        N'Morning Walk',         
        N'Gentle stroll around the garden',  
        '2025-06-10T09:00:00',   
        NULL,                    
        NULL,                    
        NULL                     
    );
END
GO

IF NOT EXISTS (
    SELECT 1
      FROM [dbo].[ACTIVITY]
     WHERE TITLE = N'Group Yoga'
)
BEGIN
    INSERT INTO [dbo].[ACTIVITY] (
        ACTIVE,
        IS_DELETED,
        TITLE,
        DESCRIPTION,
        START_DATE,
        END_DATE,
        CREATED_BY_ID,
        MODIFIED_BY_ID
    ) VALUES (
        1,                       
        0,                       
        N'Group Yoga',           
        N'Yoga session—up to 8 participants',  
        '2025-06-11T08:00:00',   
        NULL,                    
        NULL,                    
        NULL                     
    );
END
GO