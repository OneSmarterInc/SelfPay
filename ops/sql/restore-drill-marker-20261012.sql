-- TEST BRANCH ONLY: br-weathered-field-b7ykycqf (restore-test-20261012).
-- Never execute on live or on the retained backup.
CREATE TABLE public.backup_drill_marker_20261012 (created_at timestamptz NOT NULL DEFAULT clock_timestamp());
INSERT INTO public.backup_drill_marker_20261012 DEFAULT VALUES;
SELECT created_at FROM public.backup_drill_marker_20261012;
