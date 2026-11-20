# Discovery intake

Editors can record opt-in forum, social, and video leads, then export approved
source links and withholding reasons. Run the CLI from `production/` with
Python 3.11 or later. Store the SQLite database in a private directory and
treat the `queue` output as private.

## Submit an opt-in lead

Start with the [submission fixture](../fixtures/discoveries/original.json).
Use the exact public HTTPS post permalink as `source_url`, the upstream
permalink as `original_url`, and the source's UTC publication time or `null`
when unknown. For an original, set both URLs to the same permalink. For a
repost, use the original's permalink even if the original arrives later. Use a
consistent canonical permalink for each post. Simple post anchors and YouTube
watch permalinks with a single video ID are accepted.

Before submitting, verify the rights holder or authorized representative
opted in, that the URLs identify the intended public posts, and that
`consent.reference` points to the retained grant. Use an opaque reference from
the private consent record. Use `discovery_only` for private editorial
discovery and `public_source_link` when the grant allows an approved public
link and its publication timestamp. The editor-run adapter reads one bounded
local JSON record. Source text, captions, attachments, and credentials are
outside the accepted fields. Automated X and Reddit access requires separate
platform approval and would use a separately authorized adapter.

`submit` retains one candidate per permalink. Exact retries return the
original intake record. `queue` shows the cross-post relationship, consent,
review, and any recorded withdrawal. `review` takes `approve` or `withhold`,
an editor identity, and a private reason. A recorded choice is immutable.
`public` exports approved original links with their publication times and
fixed reasons. A withheld entry contains only its status and a fixed reason.

Use `withdraw` when the source is deleted or redisplay permission is revoked.
It immediately suppresses the link on subsequent exports and retains the
prior review in the private history. Withdrawals take effect even if an
earlier submission is replayed or the withdrawal arrives before intake.
Regenerate or remove any separately distributed copy after a withdrawal.

## Replay the fixtures

```sh
(
  set -eu
  discovery_demo=$(mktemp -d)
  trap 'rm -rf "$discovery_demo"' EXIT
  discoveries() { python3 -B -m fastest_discoveries --db "$discovery_demo/history.sqlite3" "$@"; }

  for fixture in cross-post original discovery-only deleted; do
    discoveries submit "fixtures/discoveries/$fixture.json" > /dev/null
  done
  discoveries review https://forum.example/topics/local-models/18 approve \
    --reviewer fixture-editor --reason 'Verified the fixture grant and original post.' > /dev/null
  discoveries review https://forum.example/topics/local-models/24 approve \
    --reviewer fixture-editor --reason 'Verified the fixture grant.' > /dev/null
  discoveries withdraw https://forum.example/topics/local-models/24 \
    --reason source_deleted > /dev/null
  discoveries public
)
```

The replay exports one link and the withholding reasons `cross_post`,
`source_deleted`, and `discovery_only`. Run the CLI boundary tests with
`python3 -B -m unittest discover -s tests -p test_discoveries.py -v`.
