-- Adds CENTRE_ACTIVITY.care_centre_id.
--
-- The service calls Base.metadata.create_all() at startup, which creates missing
-- tables but never alters existing ones. This script must therefore be run by
-- hand against every environment that already has a CENTRE_ACTIVITY table
-- (dev, staging, prod) before deploying the code that uses the column.
--
-- Idempotent: safe to run more than once.

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.CENTRE_ACTIVITY')
      AND name = 'care_centre_id'
)
BEGIN
    ALTER TABLE dbo.CENTRE_ACTIVITY ADD care_centre_id INT NULL;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'FK_CENTRE_ACTIVITY_CARE_CENTRE'
)
BEGIN
    ALTER TABLE dbo.CENTRE_ACTIVITY
        ADD CONSTRAINT FK_CENTRE_ACTIVITY_CARE_CENTRE
        FOREIGN KEY (care_centre_id) REFERENCES dbo.CARE_CENTRE(id);
END
GO

-- Backfill. Existing rows predate the column and have no centre.
--
-- Review before running. This assigns every unassigned row to the single
-- active care centre, and does nothing if there is not exactly one. If the
-- environment has several centres, assign them deliberately instead.
IF (SELECT COUNT(*) FROM dbo.CARE_CENTRE WHERE is_deleted = 0) = 1
BEGIN
    UPDATE dbo.CENTRE_ACTIVITY
    SET care_centre_id = (SELECT id FROM dbo.CARE_CENTRE WHERE is_deleted = 0)
    WHERE care_centre_id IS NULL;
END
GO

-- Once every environment is backfilled and the application always supplies a
-- value, tighten the column and change nullable=True in the model to match:
--
--   ALTER TABLE dbo.CENTRE_ACTIVITY ALTER COLUMN care_centre_id INT NOT NULL;
