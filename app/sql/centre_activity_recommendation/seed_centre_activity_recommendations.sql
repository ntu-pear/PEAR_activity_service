-- This script creates sample centre activity recommendations for testing

-- Clear existing test data (optional - uncomment if you want to reset)
-- DELETE FROM CENTRE_ACTIVITY_RECOMMENDATION WHERE created_by_id = 'seeding_script';

-- Insert sparse sample recommendations (approximately 30 records)
INSERT INTO CENTRE_ACTIVITY_RECOMMENDATION (
    centre_activity_id,
    patient_id,
    doctor_id,
    doctor_recommendation,
    doctor_remarks,
    created_by_id,
    created_date,
    modified_by_id,
    modified_date,
    is_deleted
)
VALUES
-- Patient 1 recommendations
(1, 1, 'seeding_script', 1, 'Recommended for physical rehabilitation and strength building', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 1, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 1, 'seeding_script', -1, 'May not be suitable due to current physical limitations', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 1, 'seeding_script', 1, 'Excellent for cognitive stimulation and memory enhancement', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 1, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(2, 1, 'seeding_script', -1, 'Social interaction requirements may be too demanding', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 1, 'seeding_script', 1, 'Good for creative expression and fine motor skills', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 1, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 1, 'seeding_script', 1, 'Beneficial for emotional wellbeing and stress reduction', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 1,'seeding_script', -1, 'Activity complexity may cause frustration', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),

-- Patient 2 recommendations  
(2, 2, 'seeding_script', 1, 'Excellent for social interaction and communication skills', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 2, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 2, 'seeding_script', 1, 'Recommended for physical rehabilitation and mobility improvement', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 2, 'seeding_script', -1, 'Cognitive demands may be overwhelming at this time', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 2,'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(1, 2, 'seeding_script', 1, 'Good for building strength and endurance', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 2, 'seeding_script', -1, 'Fine motor requirements may be challenging', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 2, 'seeding_script', 1, 'Beneficial for cognitive stimulation and problem solving', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 2, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 2, 'seeding_script', 1, 'Excellent for emotional expression and creativity', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),

-- Patient 3 recommendations
(1, 3, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 3, 'seeding_script', 1, 'Recommended for improving fine motor coordination', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 3, 'seeding_script', 1, 'Good for cognitive enhancement and memory training', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 3, 'seeding_script', -1, 'May cause anxiety due to social interaction requirements', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 3, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(2, 3, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 3, 'seeding_script', -1, 'Physical demands may be too strenuous currently', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 3, 'seeding_script', 1, 'Beneficial for overall wellness and relaxation', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 3, 'seeding_script', 0, NULL, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 3, 'seeding_script', -1, 'Complex instructions may be difficult to follow', 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0);

PRINT 'Centre Activity Recommendations seeded successfully!';

-- Verification queries
PRINT 'Total recommendations created:';
SELECT COUNT(*) as total_recommendations 
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id = 'seeding_script';

PRINT 'Active recommendations:';
SELECT COUNT(*) as active_recommendations 
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0;

-- Summary by patient
SELECT 
    patient_id,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN doctor_recommendation = 1 THEN 1 END) as recommended,
    COUNT(CASE WHEN doctor_recommendation = 0 THEN 1 END) as neutral,
    COUNT(CASE WHEN doctor_recommendation = -1 THEN 1 END) as not_recommended
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0
GROUP BY patient_id
ORDER BY patient_id;

-- Summary by recommendation type
SELECT 
    CASE 
        WHEN doctor_recommendation = 1 THEN 'Recommended'
        WHEN doctor_recommendation = 0 THEN 'Neutral'
        WHEN doctor_recommendation = -1 THEN 'Not Recommended'
        ELSE 'Unknown'
    END AS recommendation_type,
    COUNT(*) as count,
    COUNT(CASE WHEN doctor_remarks IS NOT NULL THEN 1 END) as with_remarks,
    COUNT(CASE WHEN doctor_remarks IS NULL THEN 1 END) as without_remarks
FROM CENTRE_ACTIVITY_RECOMMENDATION 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0
GROUP BY doctor_recommendation
ORDER BY doctor_recommendation DESC;

-- Sample data preview
SELECT TOP 10
    car.centre_activity_id,
    car.patient_id,
    car.doctor_id,
    CASE 
        WHEN car.doctor_recommendation = 1 THEN 'Recommended'
        WHEN car.doctor_recommendation = 0 THEN 'Neutral'
        ELSE 'Not Recommended'
    END AS recommendation_status,
    CASE 
        WHEN car.doctor_remarks IS NULL THEN '[No remarks]'
        WHEN LEN(car.doctor_remarks) > 50 THEN LEFT(car.doctor_remarks, 47) + '...'
        ELSE car.doctor_remarks
    END AS remarks_preview
FROM CENTRE_ACTIVITY_RECOMMENDATION car
WHERE car.created_by_id = 'seeding_script' AND car.is_deleted = 0
ORDER BY car.patient_id, car.centre_activity_id;