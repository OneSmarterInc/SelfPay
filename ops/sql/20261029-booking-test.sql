DO $change$ BEGIN
LOCK TABLE public.batches,public.entries,public.settings IN SHARE ROW EXCLUSIVE MODE;
IF (SELECT value FROM public.settings WHERE key='active_batch') IS DISTINCT FROM 'directory-email-20261029' THEN RAISE EXCEPTION 'Active batch changed'; END IF;
IF EXISTS(SELECT 1 FROM public.batches WHERE id='booking-test-20261029') THEN RAISE EXCEPTION 'Test batch already exists'; END IF;
INSERT INTO public.batches VALUES('booking-test-20261029','8ca435db34a2895c339d34b3fb003d8b1b82194d03028bcbfe1d87d191e161c0','Owner-authorized synthetic appointment test',extract(epoch from now()),'test','{"test_only":true,"entry_count":1}');
INSERT INTO public.entries VALUES('booking-test-20261029','gitesh-test','8ca435db34a2895c339d34b3fb003d8b1b82194d03028bcbfe1d87d191e161c0',$payload${"appointment_email_approved":true,"coverage":"Test mailbox only \u2014 no physical facility","email":"giteshpawar880@gmail.com","email_scope":"Owner-approved appointment test mailbox","name":"Gitesh Imaging Center","test_only":true}$payload$);
END $change$;
