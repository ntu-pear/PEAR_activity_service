-- This script creates sample centre activity recommendations for testing

-- Clear existing test data (optional - uncomment if you want to reset)
-- DELETE FROM CENTRE_ACTIVITY_RECOMMENDATION WHERE created_by_id LIKE 'doctor_%';

-- Insert sample recommendations with realistic data
INSERT INTO CENTRE_ACTIVITY_RECOMMENDATION (
    centre_activity_id,
    patient_id,
    doctor_id,
    doctor_remarks,
    created_by_id,
    created_date,
    modified_by_id,
    modified_date,
    is_deleted
)
SELECT 
    ca.id AS centre_activity_id,
    p.patient_id,
    d.doctor_id,
    CASE 
        WHEN ca.id % 5 = 1 THEN 'Recommended for physical rehabilitation and strength building'
        WHEN ca.id % 5 = 2 THEN 'Excellent for social interaction and communication skills'
        WHEN ca.id % 5 = 3 THEN 'Beneficial for cognitive stimulation and memory enhancement'
        WHEN ca.id % 5 = 4 THEN 'Helps with creative expression and fine motor skills'
        ELSE 'Good for emotional wellbeing and overall wellness'
    END AS doctor_remarks,
    CONCAT('doctor_', d.doctor_id) AS created_by_id,
    DATEADD(day, -ABS(CHECKSUM(NEWID()) % 30), GETDATE()) AS created_date,
    CONCAT('doctor_', d.doctor_id) AS modified_by_id,
    DATEADD(day, -ABS(CHECKSUM(NEWID()) % 30), GETDATE()) AS modified_date,
    0 AS is_deleted
FROM CENTRE_ACTIVITY ca
CROSS JOIN (
    -- Patient IDs - adjust these based on your actual patient data
    SELECT 1 AS patient_id
    UNION SELECT 2
    UNION SELECT 3
    UNION SELECT 4
    UNION SELECT 5
) p
CROSS JOIN (
    -- Doctor IDs - adjust these based on your actual doctor data
    SELECT 1 AS doctor_id
    UNION SELECT 2
) d
WHERE ca.is_deleted = 0
AND NOT EXISTS (
    -- Prevent duplicates
    SELECT 1 FROM CENTRE_ACTIVITY_RECOMMENDATION car
    WHERE car.centre_activity_id = ca.id
    AND car.patient_id = p.patient_id
    AND car.doctor_id = d.doctor_id
    AND car.is_deleted = 0
)
-- Only create recommendations for a subset to avoid overwhelming data
AND (
    -- Create recommendations based on some logic
    (p.patient_id % 3 = 0 AND d.doctor_id <= 2) OR  -- Every 3rd patient with first 2 doctors
    (p.patient_id % 2 = 1 AND d.doctor_id IN (3, 4)) OR  -- Odd patients with doctors 3, 4
    (p.patient_id <= 5 AND d.doctor_id = 5)  -- First 5 patients with doctor 5
)
AND ca.id IN (
    -- Limit to first 5 centre activities to keep data manageable
    SELECT TOP 5 id FROM CENTRE_ACTIVITY 
    WHERE is_deleted = 0 
    ORDER BY id
);

-- Insert some additional recommendations with different statuses for testing
INSERT INTO CENTRE_ACTIVITY_RECOMMENDATION (
    centre_activity_id,
    patient_id,
    doctor_id,
    doctor_remarks,
    created_by_id,
    created_date,
    modified_by_id,
    modified_date,
    is_deleted
)
SELECT TOP 10
    ca.id AS centre_activity_id,
    (ABS(CHECKSUM(NEWID()) % 10) + 1) AS patient_id, -- Random patient 1-10
    (ABS(CHECKSUM(NEWID()) % 5) + 1) AS doctor_id,   -- Random doctor 1-5
    'Additional test recommendation for comprehensive testing' AS doctor_remarks,
    CONCAT('doctor_', (ABS(CHECKSUM(NEWID()) % 5) + 1)) AS created_by_id,
    DATEADD(day, -ABS(CHECKSUM(NEWID()) % 60), GETDATE()) AS created_date, -- Random date within last 60 days
    CONCAT('doctor_', (ABS(CHECKSUM(NEWID()) % 5) + 1)) AS modified_by_id,
    DATEADD(day, -ABS(CHECKSUM(NEWID()) % 30), GETDATE()) AS modified_date,
    0 AS is_deleted
FROM CENTRE_ACTIVITY ca
WHERE ca.is_deleted = 0
AND NOT EXISTS (
    SELECT 1 FROM CENTRE_ACTIVITY_RECOMMENDATION car
    WHERE car.centre_activity_id = ca.id
    AND car.patient_id = (ABS(CHECKSUM(NEWID()) % 10) + 1)
    AND car.doctor_id = (ABS(CHECKSUM(NEWID()) % 5) + 1)
    AND car.is_deleted = 0
);

-- Create some soft-deleted records for testing soft delete functionality
UPDATE TOP (3) CENTRE_ACTIVITY_RECOMMENDATION 
SET 
    is_deleted = 1,
    modified_date = GETDATE(),
    modified_by_id = 'system_test'
WHERE created_by_id LIKE 'doctor_%'
AND is_deleted = 0;

PRINT 'Centre Activity Recommendations seeded successfully!';

-- Verification queries
PRINT 'Total recommendations created:';
SELECT COUNT(*) as total_recommendations 
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id LIKE 'doctor_%';

PRINT 'Active recommendations:';
SELECT COUNT(*) as active_recommendations 
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id LIKE 'doctor_%' AND is_deleted = 0;

PRINT 'Soft-deleted recommendations:';
SELECT COUNT(*) as deleted_recommendations 
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id LIKE 'doctor_%' AND is_deleted = 1;

-- Detailed verification (simplified without activity name)
SELECT 
    car.id,
    car.centre_activity_id,
    car.patient_id,
    car.doctor_id,
    LEFT(car.doctor_remarks, 50) + CASE WHEN LEN(car.doctor_remarks) > 50 THEN '...' ELSE '' END AS doctor_remarks_preview,
    car.created_date,
    car.is_deleted
FROM CENTRE_ACTIVITY_RECOMMENDATION car
WHERE car.created_by_id LIKE 'doctor_%'
ORDER BY car.patient_id, car.doctor_id, car.centre_activity_id;

-- Summary by patient
SELECT 
    patient_id,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN is_deleted = 0 THEN 1 END) as active_recommendations,
    COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted_recommendations
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id LIKE 'doctor_%'
GROUP BY patient_id
ORDER BY patient_id;

-- Summary by doctor
SELECT 
    doctor_id,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN is_deleted = 0 THEN 1 END) as active_recommendations,
    COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted_recommendations
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id LIKE 'doctor_%'
GROUP BY doctor_id
ORDER BY doctor_id;