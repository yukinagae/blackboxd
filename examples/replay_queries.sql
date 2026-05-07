SELECT *
FROM public.llm_logs
WHERE response::text ILIKE '%approve%';

SELECT trace_id, span_id, parent_span_id, provider, model, latency_ms, error
FROM public.llm_logs
WHERE kind = 'llm'
ORDER BY created_at DESC
LIMIT 50;

SELECT trace_id, name, created_at, latency_ms
FROM public.llm_logs
WHERE trace_id = '<trace-id>'
ORDER BY created_at ASC;
