-- Parameters supplied by the engagement CLI.
SELECT json_build_object(
    'closed_before_date', (statement_timestamp() AT TIME ZONE 'Asia/Shanghai')::date,
    'bindings', coalesce((SELECT json_agg(bindings ORDER BY receipt_id) FROM bindings), '[]'::json),
    'events', coalesce((
        SELECT json_agg(event ORDER BY occurred_at, kind, event_id) FROM (
            SELECT timing.occurred_at, timing.kind, timing.event_id, json_build_object(
                'kind', timing.kind,
                'occurred_at', to_char(timing.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                'receipt_id', b.receipt_id,
                'post_url', b.post_url,
                timing.id_field, timing.event_id
            )::jsonb || CASE WHEN timing.kind = 'evidence_arrival'
                THEN jsonb_build_object('evidence_destination', b.evidence_destination) ELSE '{}'::jsonb END AS event
            FROM bindings AS b
            JOIN fastest_pilot_engagement.journey AS j USING (attribution_key)
            CROSS JOIN LATERAL (VALUES
                ('evidence_arrival', 'visit_id', j.visit_id, j.visited_at),
                ('comparison_result', 'comparison_id', j.comparison_id, j.compared_at)
            ) AS timing(kind, id_field, event_id, occurred_at)
            WHERE timing.occurred_at >= b.published_at
              AND (timing.occurred_at AT TIME ZONE 'Asia/Shanghai')::date BETWEEN b.start_date AND b.start_date + 6
        ) AS projected
    ), '[]'::json)
);
