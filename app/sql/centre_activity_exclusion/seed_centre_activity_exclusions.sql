INSERT INTO CENTRE_ACTIVITY_EXCLUSION (
    centre_activity_id,
    patient_id,
    is_deleted,
    exclusion_remarks,
    start_date,
    end_date,
    created_date,
    created_by_id,
    modified_date,
    modified_by_id
)
SELECT
    ca.id                                   AS centre_activity_id,
    p.patient_id                            AS patient_id,
    0                                       AS is_deleted,
    'Test exclusion for patient ' + CAST(p.patient_id AS varchar(10)) AS exclusion_remarks,
    ca.start_date,
    ca.end_date,
    GETDATE()                               AS created_date,
    'system'                                AS created_by_id,   
    GETDATE()                               AS modified_date,
    NULL                                    AS modified_by_id
FROM CENTRE_ACTIVITY ca
CROSS JOIN (VALUES (1), (2)) AS p(patient_id) -- Patient 1 and 2 for now
WHERE ca.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM CENTRE_ACTIVITY_EXCLUSION e
      WHERE e.centre_activity_id = ca.id
        AND e.patient_id = p.patient_id
        AND ISNULL(e.is_deleted, 0) = 0
  );