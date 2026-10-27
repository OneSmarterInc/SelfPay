DO $rollback$ BEGIN
IF (SELECT value FROM public.settings WHERE key='active_batch') IS DISTINCT FROM 'directory-additions-20261027' THEN RAISE EXCEPTION 'Active batch changed; stop recovery'; END IF;
UPDATE public.settings SET value='directory-additions-20261018' WHERE key='active_batch';
INSERT INTO public.publish_events(batch_id,previous_batch,created,action) VALUES('directory-additions-20261018','directory-additions-20261027',extract(epoch from now()),'rollback');
END $rollback$;
