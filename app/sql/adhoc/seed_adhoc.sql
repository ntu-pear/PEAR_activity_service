USE activity_service_dev;
GO

INSERT INTO [dbo].[ADHOC]
    (
      old_centre_activity_id
    , new_centre_activity_id
    , patient_id
    , is_deleted
    , status
    , start_date
    , end_date
    , created_by_id
    , created_date
    )
VALUES
    (1,  2,     1, 0, 'PENDING',  '2025-07-28T09:00:00', '2025-07-28T10:00:00', 'supervisor1', SYSUTCDATETIME()),
    (3,  4,     2, 0, 'APPROVED','2025-07-29T11:00:00', '2025-07-29T12:30:00', 'supervisor1', SYSUTCDATETIME()),
    (5,  6,    42, 0, 'PENDING',  '2025-08-01T09:00:00', '2025-08-01T10:00:00', 'supervisor1', SYSUTCDATETIME());
GO