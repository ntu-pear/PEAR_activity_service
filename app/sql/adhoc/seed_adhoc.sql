INSERT INTO ADHOC (
    old_centre_activity_id,
    new_centre_activity_id,
    patient_id,
    is_deleted,
    status,
    start_date,
    end_date,
    created_date,
    modified_date,
    created_by_id,
    modified_by_id
)
SELECT
    ca.id AS old_centre_activity_id,
    ca.id AS new_centre_activity_id,    -- Put same as old ID for seeding purposes only in order to bypass NULL constraint.
    p.patient_id,
    ca.is_deleted,
    'PENDING' AS status,            
    ca.start_date,
    ca.end_date,
    GETDATE() AS created_date,
    NULL AS modified_date,
    'system' AS created_by_id,
    NULL AS modified_by_id
FROM CENTRE_ACTIVITY ca
CROSS JOIN (SELECT 1 AS patient_id UNION SELECT 2) p -- Patient 1 and 2 for now
WHERE ca.id BETWEEN 5 AND 8; -- Only for these Centre Activities for now