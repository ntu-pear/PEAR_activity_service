-- This script creates sample centre activity recommendations for testing

-- Insert sample recommendations for patients 1-5 with doctors 1-3
INSERT INTO CENTRE_ACTIVITY_RECOMMENDATION (
    centre_activity_id,
    patient_id,
    doctor_id,
    doctor_remarks,
    created_by_id,
    created_date,
    is_deleted
)
SELECT 
    ca.id AS centre_activity_id,
    p.patient_id,
    d.doctor_id,
    CASE 
        WHEN (CHECKSUM(NEWID()) % 4) = 0 THEN 'Recommended for physical therapy'
        WHEN (CHECKSUM(NEWID()) % 4) = 1 THEN 'Good for social interaction'
        WHEN (CHECKSUM(NEWID()) % 4) = 2 THEN 'Helps with cognitive stimulation'
        ELSE 'Regular activity for wellness'
    END AS doctor_remarks,
    CONCAT('doctor_', d.doctor_id) AS created_by_id,
    GETDATE() AS created_date,
    0 AS is_deleted
FROM CENTRE_ACTIVITY ca
CROSS JOIN (
    SELECT 1 AS patient_id
    UNION SELECT 2
    UNION SELECT 3
    UNION SELECT 4
    UNION SELECT 5
) p
CROSS JOIN (
    SELECT 1 AS doctor_id
    UNION SELECT 2
    UNION SELECT 3
) d
WHERE ca.is_deleted = 0
AND NOT EXISTS (
    SELECT 1 FROM CENTRE_ACTIVITY_RECOMMENDATION car
    WHERE car.centre_activity_id = ca.id
    AND car.patient_id = p.patient_id
    AND car.doctor_id = d.doctor_id
    AND car.is_deleted = 0
)
-- Limit to avoid too many recommendations - only create for first 3 centre activities per patient/doctor pair
AND ca.id IN (
    SELECT TOP 3 id FROM CENTRE_ACTIVITY 
    WHERE is_deleted = 0 
    ORDER BY id
);

-- Verify the insertions
SELECT 
    car.id,
    car.centre_activity_id,
    ca.activity_name,
    car.patient_id,
    car.doctor_id,
    car.doctor_remarks,
    car.created_date
FROM CENTRE_ACTIVITY_RECOMMENDATION car
JOIN CENTRE_ACTIVITY ca ON car.centre_activity_id = ca.id
WHERE car.created_by_id LIKE 'doctor_%'
ORDER BY car.patient_id, car.doctor_id, car.centre_activity_id;
