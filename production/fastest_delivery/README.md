# Editorial handoffs

Use the [seven-day distribution pilot guide](PILOT.md) to collect and audit the X and Shorts records.

## X pilot

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

## YouTube Shorts pilot

Run from `production/` with the same editorial draft, PostgreSQL login and Pillow dependency. Install FFmpeg with the `libx264` encoder. The pilot creates a 15-second, 720×1280 MP4 with an original benchmark chart and on-screen captions. It also creates UTF-8 title, description and timed SRT files. The description carries the full source credit and exact public evidence URL. The review manifest records the locale, release, claim, benchmark conditions, public evidence rights and file hashes.

```sh
PACKAGE=$(python3 -m fastest_delivery --channel youtube-shorts prepare \
  --draft "$DRAFT" --output-dir ./shorts-review)
```

For Simplified or Traditional Chinese drafts, add `--font-file "$FONT_FILE"` with a font licensed for the intended use that covers the chosen script. Play the MP4 and review the caption timing, chart, exact claim, locale, copy, source and rights in the package. Confirm use of the evidence, generated media and font with a YouTube-specific rights decision. Supply its reference and the authorized channel's stable `UC…` ID. [Find your YouTube channel ID](https://support.google.com/youtube/answer/3250431).

```sh
APPROVAL=$(python3 -m fastest_delivery --channel youtube-shorts approve \
  --package "$PACKAGE" --payload-sha256 "$(basename "$PACKAGE")" \
  --account "$YOUTUBE_CHANNEL_ID" --window-start "$WINDOW_START" --window-end "$WINDOW_END" \
  --approved-by "$EDITOR" --rights-reference "$RIGHTS_REFERENCE" \
  --approval-dir ./shorts-approvals)

python3 -m fastest_delivery --channel youtube-shorts export \
  --package "$PACKAGE" --approval "$APPROVAL" --delivery-dir ./shorts-deliveries
```

The approval binds the exact MP4 and upload text by hash, the YouTube channel ID, and the time window. Keep approvals and delivery records in directories writable only by authorized editors or operators. Run export immediately before delivery. For a queued export, the command rechecks the evidence and approval window. A retry returns the same handoff or the recorded receipt. A withdrawn release blocks queued exports.

Open `youtube-short.zip` from the returned path. In the approved YouTube Studio account, upload `short.mp4`, use `title.txt` and `description.txt`, select the language from the manifest, and add `captions.srt` as a timed caption track when using player captions. Use one operator per handoff. Check the channel for the exact Short before attempting another upload when publication is uncertain. [Upload a Short in YouTube Studio](https://support.google.com/youtube/answer/12779649).

After verifying the published clip, copy its canonical `https://www.youtube.com/shorts/VIDEO_ID` URL. Supply the actual publication time with a UTC offset and the channel ID you confirmed in YouTube Studio.

```sh
python3 -m fastest_delivery --channel youtube-shorts receipt \
  --approval "$APPROVAL" --delivery-dir ./shorts-deliveries \
  --account "$OBSERVED_CHANNEL_ID" --url "$PUBLIC_SHORT_URL" \
  --published-at "$POSTED_AT" --operator "$OPERATOR"
```

After a withdrawal, scan recorded Shorts with the command below. It prints the path to each applicable `correction.json` and reuses the same task on retry. The task identifies the live URL, channel, withdrawn release, claim IDs and receipt. Set the affected video to Private in YouTube Studio and, where revised evidence qualifies, prepare and approve a replacement. Set aside exported copies of withdrawn packages awaiting upload. [Change a video's visibility](https://support.google.com/youtube/answer/157177).

```sh
python3 -m fastest_delivery --channel youtube-shorts corrections \
  --delivery-dir ./shorts-deliveries
```

## Test locally

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -c -s tests -p test_x_delivery.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -c -s tests -p test_shorts_delivery.py -v
```
