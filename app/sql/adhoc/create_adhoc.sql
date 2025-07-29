USE activity_service_dev;
GO

CREATE TABLE [dbo].[ADHOC] (
    id                         INT             IDENTITY(1,1) NOT NULL CONSTRAINT pk_adhoc PRIMARY KEY,
    old_centre_activity_id     INT             NOT NULL 
                               CONSTRAINT fk_adhoc_old_centre_activity 
                               FOREIGN KEY REFERENCES [dbo].[CENTRE_ACTIVITY](id),
    new_centre_activity_id     INT             NOT NULL 
                               CONSTRAINT fk_adhoc_new_centre_activity 
                               FOREIGN KEY REFERENCES [dbo].[CENTRE_ACTIVITY](id),
    patient_id                 INT             NULL,
    is_deleted                 BIT             NOT NULL CONSTRAINT df_adhoc_is_deleted DEFAULT (0),
    status                     NVARCHAR(50)    NOT NULL,
    start_date                 DATETIME2(3)    NOT NULL,
    end_date                   DATETIME2(3)    NOT NULL,
    created_date               DATETIME2(3)    NOT NULL CONSTRAINT df_adhoc_created_date DEFAULT SYSUTCDATETIME(),
    modified_date              DATETIME2(3)    NULL,
    created_by_id              NVARCHAR(50)    NOT NULL,
    modified_by_id             NVARCHAR(50)    NULL
);
GO