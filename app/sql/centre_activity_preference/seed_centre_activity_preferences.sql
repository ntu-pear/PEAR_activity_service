-- This script creates random preferences for patients 1-5 across all centre activities

-- Insert preferences for all patient/centre_activity combinations that don't already exist
INSERT INTO CENTRE_ACTIVITY_PREFERENCE (
    centre_activity_id,
    patient_id,
    is_like,
    created_by_id,
    created_date,
    is_deleted
)
SELECT 
    ca.id AS centre_activity_id,
    p.patient_id,
    CASE WHEN (CHECKSUM(NEWID()) % 10) < 7 THEN 1 ELSE 0 END AS is_like, -- 70% like, 30% dislike
    'sql_seed_script' AS created_by_id,
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
WHERE ca.is_deleted = 0
AND NOT EXISTS (
    SELECT 1 FROM CENTRE_ACTIVITY_PREFERENCE cap
    WHERE cap.centre_activity_id = ca.id
    AND cap.patient_id = p.patient_id
);

-- Show summary
SELECT 
    'Total Preferences Created' AS Metric,
    COUNT(*) AS Count
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE patient_id IN (1, 2, 3, 4, 5);

-- Show breakdown by patient and preference type
SELECT 
    patient_id,
    CASE WHEN is_like = 1 THEN 'Likes' ELSE 'Dislikes' END AS preference_type,
    COUNT(*) AS count
FROM CENTRE_ACTIVITY_PREFERENCE 
WHERE patient_id IN (1, 2, 3, 4, 5)
GROUP BY patient_id, is_like
ORDER BY patient_id, is_like DESC;

-- Show sample of created preferences
SELECT TOP 20
    cap.patient_id,
    cap.centre_activity_id,
    CASE WHEN cap.is_like = 1 THEN 'Likes' ELSE 'Dislikes' END AS preference,
    cap.created_date
FROM CENTRE_ACTIVITY_PREFERENCE cap
WHERE cap.patient_id IN (1, 2, 3, 4, 5)
AND cap.created_by_id = 'sql_seed_script'
ORDER BY cap.patient_id, cap.centre_activity_id;

PRINT 'Centre Activity Preference seeding completed successfully!';
