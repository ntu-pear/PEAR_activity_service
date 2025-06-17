USE activity_service_dev;
GO

-- Create table
CREATE TABLE [dbo].[CENTRE_ACTIVITY] (
    id                 INT           IDENTITY(1,1) NOT NULL
        CONSTRAINT pk_centre_activity PRIMARY KEY,
    activity_id        INT           NOT NULL
        CONSTRAINT fk_centre_activity_activity_id FOREIGN KEY REFERENCES [dbo].[ACTIVITY](id),
    is_compulsory      BIT           NOT NULL CONSTRAINT df_centre_activity_is_compulsory DEFAULT(0),
    is_fixed           BIT           NOT NULL CONSTRAINT df_centre_activity_is_fixed DEFAULT(0),
    is_group           BIT           NOT NULL CONSTRAINT df_centre_activity_is_group DEFAULT(0),
    min_duration       INT           NOT NULL,
    max_duration       INT           NOT NULL,
    min_people_req     INT           NOT NULL CONSTRAINT df_centre_activity_min_people_req DEFAULT(1),
    start_date         DATETIME2(3)  NOT NULL,
    end_date           DATETIME2(3)  NULL,
    active             BIT           NOT NULL CONSTRAINT df_centre_activity_active DEFAULT(1),
    created_date       DATETIME2(3)  NOT NULL CONSTRAINT df_centre_activity_created_date DEFAULT SYSUTCDATETIME(),
    modified_date      DATETIME2(3)  NOT NULL CONSTRAINT df_centre_activity_modified_date DEFAULT SYSUTCDATETIME(),
    created_by_id      NVARCHAR(50)  NULL,
    modified_by_id     NVARCHAR(50)  NULL
);
GO
