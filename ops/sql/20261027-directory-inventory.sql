SELECT s.value AS active_batch, e.entry_key, e.content_hash, e.payload FROM public.settings s JOIN public.entries e ON e.batch_id=s.value WHERE s.key='active_batch' ORDER BY e.entry_key;
