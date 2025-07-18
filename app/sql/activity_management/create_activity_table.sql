USE activity_service_dev;   /*Change to your database name*/
GO

-- Create table with lower_snake_case columns and upper-case table name
CREATE TABLE [dbo].[ACTIVITY] (
    id              INT            IDENTITY(1,1) NOT NULL
       CONSTRAINT pk_activity PRIMARY KEY,
    is_deleted      BIT            NOT NULL CONSTRAINT df_activity_is_deleted DEFAULT (0),
    title           NVARCHAR(200)  NOT NULL,
    description     NVARCHAR(255)  NULL,
    created_date    DATETIME2(3)   NOT NULL CONSTRAINT df_activity_created_date DEFAULT SYSUTCDATETIME(),
    modified_date   DATETIME2(3)   NOT NULL CONSTRAINT df_activity_modified_date DEFAULT SYSUTCDATETIME(),
    created_by_id   NVARCHAR(50)   NULL,
    modified_by_id  NVARCHAR(50)   NULL
);
GO