-- Read-only owner evidence capture; public catalog and function definition only.
SELECT jsonb_build_object(
 'captured_at',clock_timestamp(),
 'database',current_database(),
 'executor_role',current_user,
 'function_definition',pg_get_functiondef('selfpay_directory_sync.apply_bundle(text,text,boolean)'::regprocedure),
 'function_body_md5',(SELECT md5(prosrc) FROM pg_proc WHERE oid='selfpay_directory_sync.apply_bundle(text,text,boolean)'::regprocedure),
 'catalog_status',selfpay_directory_sync.status(),
 'historical_publish_events',(SELECT coalesce(jsonb_agg(to_jsonb(e)),'[]'::jsonb) FROM public.publish_events e WHERE batch_id='b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4')
) AS evidence;
