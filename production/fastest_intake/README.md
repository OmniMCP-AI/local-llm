# Private price and evaluation intake

The collector's evidence bundle imports into the private `fastest_intake` PostgreSQL schema. A source may have a successful page check, a page without a price, restricted access, or no verified result. Price candidates identify the reporting source and retail channel separately. Capture time, source date, market, currency, condition, exact board and listing URL retain their own fields. Bundle, asking, coupon-adjusted and historical amounts retain different kinds.

Evaluations preserve the model identity, benchmark version, reported metric and scale, source locator, and evaluation settings where stated. The model-card revision in the source locator or context records which document was read. Leave the tested checkpoint revision unset unless the publisher supplies it.

Run from `production` with the development database selected:

```sh
export FASTEST_DATABASE_URL=postgresql://localhost/localdecode_catalog
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest intake/your-capture.json
python3 -B -m fastest_intake stats
```

The input JSON has `checked_at`, `note`, `sources`, `prices` and `evaluations`. See the tables for typed columns. The content hash identifies the batch and replay is idempotent. Keep capture bundles under the ignored intake directory. Review rights, exact identity, methodology, and current offer status before preparing a release. The public pricing and benchmark endpoints read their existing reviewed stores.
