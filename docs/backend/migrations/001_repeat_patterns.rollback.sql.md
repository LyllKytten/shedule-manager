# `backend/migrations/001_repeat_patterns.rollback.sql`

Drops the three columns added by `001_repeat_patterns.sql`, in one transaction.

Rarely needed: the previous backend version runs fine with the columns present.
Use it only if you want the schema exactly as before. Shift-cycle series keep
their existing rows but lose the pattern, so they can no longer auto-extend.
