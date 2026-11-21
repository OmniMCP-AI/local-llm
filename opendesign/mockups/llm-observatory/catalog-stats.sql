\set ON_ERROR_STOP on
SELECT format('SELECT %L AS table_name, count(*) AS row_count FROM %I.%I;',
              schemaname || '.' || tablename, schemaname, tablename)
FROM pg_tables
WHERE schemaname IN ('fastest_catalog', 'fastest_research', 'fastest_release',
                     'fastest_prices', 'fastest_contributor', 'fastest_intake',
                     'fastest_release_watch', 'fastest_github_intake', 'fastest_feedback',
                     'fastest_pilot_engagement', 'fastest_discoveries')
ORDER BY schemaname, tablename
\gexec
