IF NOT EXISTS (
    SELECT 1 FROM [dbo].[CENTRE_ACTIVITY_EXCLUSION]
    WHERE activity_id = 1 AND patient_id = 101
)
BEGIN
    INSERT INTO [dbo].[CENTRE_ACTIVITY_EXCLUSION]
      (activity_id, patient_id, is_deleted, exclusion_remarks, start_date, end_date, created_by_id, modified_by_id)
    VALUES
      (1, 101, 0, N'Test exclusion for patient 101', '2025-01-01', '2025-01-15', NULL, NULL);
END

IF NOT EXISTS (
    SELECT 1 FROM [dbo].[CENTRE_ACTIVITY_EXCLUSION]
    WHERE activity_id = 2 AND patient_id = 102
)
BEGIN
    INSERT INTO [dbo].[CENTRE_ACTIVITY_EXCLUSION]
      (activity_id, patient_id, is_deleted, exclusion_remarks, start_date, end_date, created_by_id, modified_by_id)
    VALUES
      (2, 102, 0, N'Art therapy excluded', '2025-02-10', NULL, NULL, NULL);
END
GO