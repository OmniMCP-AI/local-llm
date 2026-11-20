# X editorial handoff

Run from `production/` with Python 3.11 or later. The preparation step also requires Pillow (`python3 -m pip install 'Pillow>=10.1,<13'`). Preparation and export use the same read-only PostgreSQL login and `FASTEST_EDITORIAL_DATABASE_URL` as the [editorial draft generator](../fastest_editorial/README.md).

## Prepare and approve

Set `DRAFT` to the path printed by the editorial generator. This renders a short X post, a PNG chart generated from the verified release metric, and translated alt text. The copy credits the source and links to the pinned benchmark citation.

```sh
PACKAGE=$(python3 -m fastest_delivery prepare --draft "$DRAFT" --output-dir ./x-review)
```

Review `post.txt`, `chart.png`, `chart-alt.txt`, and the evidence in `package.json` before approving. Confirm the destination account is authorized and that the evidence can be used in the post and its chart. Supply the separate channel-use rights decision with `--rights-reference`. Use an explicit start and end with UTC offsets for the publishing window, for example `2026-11-21T09:00:00+08:00` and `2026-11-21T10:00:00+08:00`.

```sh
APPROVAL=$(python3 -m fastest_delivery approve \
  --package "$PACKAGE" --payload-sha256 "$(basename "$PACKAGE")" \
  --account "$X_HANDLE" --window-start "$WINDOW_START" --window-end "$WINDOW_END" \
  --approved-by "$EDITOR" --rights-reference "$RIGHTS_REFERENCE" \
  --approval-dir ./x-approvals)
```

Allow only authorized editors to write approval files. Pass a trusted approval to the handoff command. File digests bind the approved artifacts and destination. Access to the approval directory establishes who can issue the record.

## Export and reconcile

Run `export` immediately before manual delivery. It checks the approved window and revalidates the draft against the pinned public release. A withdrawn release stops a queued handoff, including retries of a previously exported package. Set aside any retained copy if its evidence has since been withdrawn.

```sh
python3 -m fastest_delivery export \
  --package "$PACKAGE" --approval "$APPROVAL" --delivery-dir ./x-deliveries
```

The command prints an absolute path. A path ending in `x-post.zip` is a handoff for the authorized operator. Upload `chart.png`, enter `chart-alt.txt` as image alt text, and use `post.txt` as the post copy. The same story revision and handle use one immutable handoff in the shared delivery directory. Use one operator per handoff. If a prior publication attempt is uncertain, check the approved X account for the exact post before taking any further delivery action.

Once the post is visible, record its canonical `https://x.com/HANDLE/status/POST_ID` URL and observed publication time. The operator verifies the post against the exported package and confirms the account used. The command stores that confirmation locally.

```sh
python3 -m fastest_delivery receipt \
  --approval "$APPROVAL" --delivery-dir ./x-deliveries \
  --url "$PUBLIC_POST_URL" --published-at "$POSTED_AT" --operator "$OPERATOR"
```

Replaying the same receipt returns the existing record. A different receipt for the handoff is rejected. Subsequent exports with the same approval return the recorded `receipt.json` path. The local ledger can reconcile an observed publication after the window closes or after evidence is withdrawn.

## Test locally

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -c -s tests -p test_x_delivery.py -v
```
