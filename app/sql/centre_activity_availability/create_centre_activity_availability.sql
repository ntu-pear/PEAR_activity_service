USE activity_service_dev;
GO

CREATE TABLE [dbo].[CENTRE_ACTIVITY_AVAILABILITY](
    id                 INT           IDENTITY(1,1) NOT NULL CONSTRAINT pk_centre_activity_availability PRIMARY KEY,
	centre_activity_id INT			 NOT NULL CONSTRAINT fk_centre_activity_availability_centre_activity_id FOREIGN KEY REFERENCES [dbo].[CENTRE_ACTIVITY](id),
	is_deleted		   BIT			 NOT NULL CONSTRAINT df_centre_activity_availability_is_deleted DEFAULT (0),
	start_time         DATETIME2(3)  NOT NULL,
    end_time           DATETIME2(3)  NOT NULL,
	created_date       DATETIME2(3)  NOT NULL CONSTRAINT df_centre_activity_availability_created_date DEFAULT SYSUTCDATETIME(),
    modified_date      DATETIME2(3)  NOT NULL CONSTRAINT df_centre_activity_availability_modified_date DEFAULT SYSUTCDATETIME(),
    created_by_id      NVARCHAR(50)  NULL,
    modified_by_id     NVARCHAR(50)  NULL
);
GO