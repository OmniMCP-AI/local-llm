# Editorial draft generator

Run this from `production/` with Python 3.11 or later and `psql` on your path. Use the [benchmark release service](../README.md) to publish reviewed observations separately. Give the generator its own database login with schema usage and permission to execute `fastest_release.read_release(uuid)`.

```sh
export FASTEST_EDITORIAL_DATABASE_URL='dbname=fastest_release user=fastest_release_reader'
python3 -m fastest_editorial \
  --public-origin https://benchmark.example \
  --output-dir ./editorial-drafts \
  --locale zh-CN
```

Set `--public-origin` to the HTTPS origin serving your public benchmark releases. The command prints the absolute path of one review record. GrokBot can invoke the command and read that JSON file. The process reads public evidence, writes a local draft, and has no channel-account configuration.

Use the [pilot scheduler entry point](../fastest_delivery/PILOT.md#run-a-scheduled-editorial-slot) for a scheduled pilot run. It retains the exact review revision and the observed attempt history for the pilot audit.

The default date is today's date in Asia/Shanghai. The default release is the current release at the start of the run. Pass `--date YYYY-MM-DD` and `--release RELEASE_UUID` to reproduce a specific run. Use `--locale en`, `zh-CN`, or `zh-TW` for English, Simplified Chinese, or Traditional Chinese.

## Review record

Every record contains the editorial date, timezone, language, outcome, and draft revision. A story uses an evergreen question for an original measurement and correction copy for a later revision of that evidence. The claim carries its exact decimal value, unit, statistic, sample count, and evidence ID. The package includes the benchmark conditions, attribution, public evidence rights decision, and a citation link pinned to the release. The source locator and revision identify the source. The release service does not provide an observation date.

Before producing copy, the generator verifies the release row against the pinned public table and checks the table digest against the release manifest. The story records both digests. Drafts contain text only. The public evidence decision gives no media authorization, so the media list is empty. Channel approval can reference `draft_revision` and record its own account, exact payload and permissions.

A `no_story` record includes a machine-readable `reason` of `no_current_release`, `release_not_found`, `withdrawn_release`, `synthetic_release`, or `unsupported_metric`. The checked-in synthetic observation produces a no-story record. Database failures and release integrity errors exit with a failure status so the runner can retry or report them.

The file path is `<output-dir>/<editorial-date>/<draft-revision>.json`. The revision is the SHA-256 of the JSON object without `draft_revision`, encoded as UTF-8 with sorted keys, unescaped Unicode, and no whitespace between elements or keys and values. Concurrent runs with the same inputs return the same file. An advance of the current release or a withdrawal can produce a new record. Retained drafts are audit artifacts. Read the pinned release again and verify the figures, rights, and exact payload before any later delivery.

Use the [X editorial handoff](../fastest_delivery/README.md) to prepare a post with a chart, approve its destination and publishing window, and reconcile manual delivery.

## Test locally

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -c -s tests -p test_editorial.py -v
```
