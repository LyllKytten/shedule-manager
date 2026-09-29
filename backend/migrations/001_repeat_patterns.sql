-- 001: repeat patterns "weekdays", "weekends" and shift cycles (e.g. 5:2).
--
-- Additive only: three new NULLable columns, no existing data is changed except
-- filling series_start for existing series. Safe to run more than once.
-- Run it BEFORE deploying the new backend version (old code ignores the columns).
--
--   docker compose exec -T db psql -U schedule -d schedule -v ON_ERROR_STOP=1 < migrations/001_repeat_patterns.sql

BEGIN;

ALTER TABLE events ADD COLUMN IF NOT EXISTS repeat_days_on  INTEGER;
ALTER TABLE events ADD COLUMN IF NOT EXISTS repeat_days_off INTEGER;
ALTER TABLE events ADD COLUMN IF NOT EXISTS series_start    DATE;

-- Anchor existing series on their earliest remaining occurrence.
UPDATE events AS e
SET series_start = s.first_date
FROM (
    SELECT series_id, MIN(date) AS first_date
    FROM events
    WHERE series_id IS NOT NULL
    GROUP BY series_id
) AS s
WHERE e.series_id = s.series_id
  AND e.series_start IS NULL;

COMMIT;
