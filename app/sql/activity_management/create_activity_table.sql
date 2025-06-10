USE fyp_dev_zihao; /*Change to your database name*/
GO

IF NOT EXISTS (
    SELECT * 
      FROM sys.objects 
     WHERE object_id = OBJECT_ID(N'[dbo].[activity]')
       AND type = N'U'
)
BEGIN
    CREATE TABLE [dbo].[activity] (
        [id]                  UNIQUEIDENTIFIER NOT NULL
                              CONSTRAINT [PK_activity] PRIMARY KEY
                              DEFAULT NEWID(),
        [title]               NVARCHAR(200)     NOT NULL,
        [description]         NVARCHAR(MAX)     NULL,
        [start_date]          DATETIME2(3)      NOT NULL,
        [end_date]            DATETIME2(3)      NULL,
        [is_fixed]            BIT               NOT NULL CONSTRAINT [DF_activity_is_fixed] DEFAULT (0),
        [is_compulsory]       BIT               NOT NULL CONSTRAINT [DF_activity_is_compulsory] DEFAULT (0),
        [is_group]            BIT               NOT NULL CONSTRAINT [DF_activity_is_group] DEFAULT (0),
        [min_duration]        INT               NULL,
        [max_duration]        INT               NULL,
        [min_people_required] INT               NULL,
        [created_date]        DATETIME2(3)      NOT NULL CONSTRAINT [DF_activity_created_date] DEFAULT (SYSUTCDATETIME()),
        [modified_date]       DATETIME2(3)      NOT NULL CONSTRAINT [DF_activity_modified_date] DEFAULT (SYSUTCDATETIME())
    );

    EXEC('
    CREATE TRIGGER [dbo].[TRG_activity_ModifiedDate]
    ON [dbo].[activity]
    AFTER UPDATE
    AS
    BEGIN
      SET NOCOUNT ON;
      UPDATE a
        SET modified_date = SYSUTCDATETIME()
      FROM [dbo].[activity] AS a
      JOIN inserted AS i
        ON a.id = i.id;
    END
    ');
END
GO