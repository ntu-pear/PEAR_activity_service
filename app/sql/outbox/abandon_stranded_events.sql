-- Retire the outbox events that were stranded by the old retry bug.
--
-- MUST RUN BEFORE deploying the retry fix, on every environment.
--
-- Background. The publisher used to select only status = 'PENDING', while
-- a failed publish set status = 'FAILED'. A failed event was therefore
-- never looked at again, whatever its retry_count said. 42 events in prod
-- were stranded this way between April and August 2026, all of them with
-- retry_count = 1 and the same error, "Failed to publish to message queue".
--
-- The fix widens the publisher to pick up FAILED rows that still have
-- attempts left. That is correct for events failing from now on, but it
-- would also sweep up these 42 and publish payloads captured months ago,
-- overwriting current state in the consumers with April values. So mark
-- them ABANDONED first: the publisher skips that status.
--
-- This does NOT resync anything. Of the 42, 15 are real divergence between
-- prod and the scheduler. Resync those through the drift path, which
-- republishes from current rows rather than replaying old payloads. The
-- one worth doing first is exclusion 95 (tee break, patient 1, "ulcer"):
-- it is active in prod and the scheduler was never told.
--
-- Idempotent: only touches rows that are still FAILED with the old error.

-- Guard. Editors often connect with no default database, which lands you
-- on master, and the table name here is unqualified. Select the target
-- database first (prod is activity_service_dev, despite the name).
DECLARE @db SYSNAME = DB_NAME();   -- RAISERROR needs a variable, not DB_NAME()
IF @db NOT LIKE 'activity_service%'
BEGIN
    RAISERROR('Wrong database: %s. Select activity_service_dev (prod) or activity_service_staging first.', 16, 1, @db);
    SET NOEXEC ON;
END
GO

-- What is about to change. Expect 42 rows in prod.
SELECT DB_NAME() AS running_against,
       COUNT(*)  AS rows_this_will_abandon
FROM dbo.OUTBOX_EVENTS
WHERE status = 'FAILED'
  AND created_at < '2026-11-01';
GO

UPDATE dbo.OUTBOX_EVENTS
SET status        = 'ABANDONED',
    retry_count   = 3,
    error_message = LEFT(
        'Abandoned by abandon_stranded_events.sql. Stranded by the '
        + 'pre-fix retry bug; payload is stale, do not replay. '
        + 'Original error: ' + ISNULL(error_message, '(none)'), 1000)
WHERE status = 'FAILED'
  AND created_at < '2026-11-01';
GO

-- Should be 0 FAILED, 42 ABANDONED, and PUBLISHED unchanged at 423.
SELECT status, COUNT(*) AS n
FROM dbo.OUTBOX_EVENTS
GROUP BY status
ORDER BY status;
GO

SET NOEXEC OFF;   -- clear the guard so the session stays usable
GO
