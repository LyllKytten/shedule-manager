-- Undo 001. Only needed if you go back to the previous backend version AND want
-- the columns gone; the old version works fine with them present.
-- WARNING: shift-cycle series lose their pattern info (their existing rows stay).

BEGIN;
ALTER TABLE events DROP COLUMN IF EXISTS series_start;
ALTER TABLE events DROP COLUMN IF EXISTS repeat_days_off;
ALTER TABLE events DROP COLUMN IF EXISTS repeat_days_on;
COMMIT;
