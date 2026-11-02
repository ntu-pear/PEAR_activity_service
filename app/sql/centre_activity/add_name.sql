-- Adds CENTRE_ACTIVITY.name.
--
-- A centre activity has no name of its own today: it is displayed through its
-- parent activity's title. That forces two variants of one activity - a morning
-- and an afternoon session, say - to be two separate activities, which is why
-- the live data contains an activity literally titled "Breathing exercise AM".
--
-- With this column, one activity called "Breathing" can carry two centre
-- activities called "Breathing AM" and "Breathing PM".
--
-- The service calls Base.metadata.create_all() at startup, which creates missing
-- tables but never alters existing ones. This script must therefore be run by
-- hand against every environment that already has a CENTRE_ACTIVITY table
-- (dev, staging, and the CI test database) BEFORE deploying the code that uses
-- the column. Deploying first takes down every endpoint touching the table.
--
-- Idempotent: safe to run more than once.

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.CENTRE_ACTIVITY')
      AND name = 'name'
)
BEGIN
    ALTER TABLE dbo.CENTRE_ACTIVITY ADD name NVARCHAR(200) NULL;
END
GO

-- Backfill from the parent activity's title, so every existing row keeps
-- displaying exactly as it does now and nothing changes visually on deploy.
UPDATE ca
SET ca.name = a.title
FROM dbo.CENTRE_ACTIVITY ca
INNER JOIN dbo.ACTIVITY a ON a.id = ca.activity_id
WHERE ca.name IS NULL;
GO

-- Once every environment is backfilled and the application always supplies a
-- value, tighten the column and change nullable=True in the model to match:
--
--   ALTER TABLE dbo.CENTRE_ACTIVITY ALTER COLUMN name NVARCHAR(200) NOT NULL;
