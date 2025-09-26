-- This script creates sample centre activity preferences for testing

-- Clear existing test data (optional - uncomment if you want to reset)
-- DELETE FROM CENTRE_ACTIVITY_PREFERENCE WHERE created_by_id = 'seeding_script';

-- Insert sparse sample preferences (approximately 30 records)
INSERT INTO CENTRE_ACTIVITY_PREFERENCE (
    centre_activity_id,
    patient_id,
    is_like,
    created_by_id,
    created_date,
    modified_by_id,
    modified_date,
    is_deleted
)
VALUES
-- Patient 1 preferences
(1, 1, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 1, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 1, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 1, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 1, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(2, 1, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 1, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 1, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 1, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 1, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),

-- Patient 2 preferences  
(2, 2, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 2, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 2, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 2, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 2, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(1, 2, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 2, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 2, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 2, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 2, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),

-- Patient 3 preferences
(1, 3, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(3, 3, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(5, 3, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(7, 3, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(9, 3, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(2, 3, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(4, 3, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(6, 3, 1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(8, 3, 0, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0),
(10, 3, -1, 'seeding_script', GETDATE(), 'seeding_script', GETDATE(), 0);

PRINT 'Centre Activity Preferences seeded successfully!';

-- Verification queries
PRINT 'Total preferences created:';
SELECT COUNT(*) as total_preferences 
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE created_by_id = 'seeding_script';

PRINT 'Active preferences:';
SELECT COUNT(*) as active_preferences 
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0;

-- Summary by patient
SELECT 
    patient_id,
    COUNT(*) as total_preferences,
    COUNT(CASE WHEN is_like = 1 THEN 1 END) as likes,
    COUNT(CASE WHEN is_like = 0 THEN 1 END) as neutral,
    COUNT(CASE WHEN is_like = -1 THEN 1 END) as dislikes
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0
GROUP BY patient_id
ORDER BY patient_id;

-- Summary by preference type
SELECT 
    CASE 
        WHEN is_like = 1 THEN 'Likes'
        WHEN is_like = 0 THEN 'Neutral'
        WHEN is_like = -1 THEN 'Dislikes'
        ELSE 'Unknown'
    END AS preference_type,
    COUNT(*) as count
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE created_by_id = 'seeding_script' AND is_deleted = 0
GROUP BY is_like
ORDER BY is_like DESC;

-- Sample data preview
SELECT TOP 10
    cap.centre_activity_id,
    cap.patient_id,
    CASE 
        WHEN cap.is_like = 1 THEN 'Likes'
        WHEN cap.is_like = 0 THEN 'Neutral'
        ELSE 'Dislikes'
    END AS preference_status,
    cap.created_date
FROM CENTRE_ACTIVITY_PREFERENCE cap
WHERE cap.created_by_id = 'seeding_script' AND cap.is_deleted = 0
ORDER BY cap.patient_id, cap.centre_activity_id;
