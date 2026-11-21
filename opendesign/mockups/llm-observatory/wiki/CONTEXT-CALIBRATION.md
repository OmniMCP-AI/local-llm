# Graphify context suggestions

Use the editor CLI from the observatory directory. Pass the current Pages build containing the research and wiki manifests and `evidence-quarantine.json`. The CLI checks the same pinned research index as the correction workflow and excludes current withdrawals. If using a preserved build for comparison, supply the live quarantine file through `FASTEST_EVIDENCE_STATE`. Sources with approved video metadata enter through the existing Pages approval gate.

```sh
node research-context-cli.mjs CURRENT_PAGES evaluate
node research-context-cli.mjs CURRENT_PAGES suggest together-evaluation-methods
```

Each proposal has a source revision, subject, facet, locator, rule digest and stable proposal ID. Article suggestions name the matching title or editorial summary field and cite the publication URL. Case suggestions cite the individual record and use its declared metric name. Explicit forecast markers can use the same record’s conditions and evidence class. When a dimension is ambiguous, the tool abstains. It never takes a case task from the article’s tags or prose. The reviewed tags, curator task prose and mapped dimension are evaluation targets. Model weights stay unchanged.

## Replay a rule change

Update `context-suggestion-rules.json` or draft a copy and increment its version. The tool combines the scoped rule aliases with the released vocabulary’s aliases. The rule digest covers the engine version, rules and released vocabulary. A changed rule engine also needs a new rule release. Use `FASTEST_CONTEXT_RULES` to evaluate a draft.

```sh
FASTEST_CONTEXT_RULES=draft-rules.json node research-context-cli.mjs CURRENT_PAGES evaluate split.json
```

The split file takes `heldOut` source IDs and additional `crossPosts` arrays of related source IDs. All observations from one source stay together. Publisher groups and registered cross-post families stay on one side of the split. Use development sources for rule edits and record cited positive and hard negative labels from those sources. Use untouched sources and families for each rule change’s final check. Public evaluation and review use eligible released sources.

The replay reports micro precision and recall, abstentions per subject, wrong-scope assignment counts and source coverage for languages and formats. An article-to-case error is a false case-task suggestion that is a reviewed topic of its parent publication. A forecast transfer is a non-projection dimension suggested for an annotated projection. A null score means no denominator was available. The input coverage is restricted to released metadata, including its curator-written publication summaries. Spanish, Japanese, Korean, German, Hindi, French and Arabic display labels are already present in the wiki. The suggestion rules cover English and Chinese prose. An unreported source language abstains on lexical topic and task suggestions. Coverage gaps appear in the report. Automatic promotion is disabled for every replay.

## Review and stage a release

Create a private request JSON containing `review`, optional `plan` and `rules`, `examples` and `decisions`. Supply at least one positive and one negative development example as `{source, subject, facet, tag, expected}` with an explicit boolean. Examples must match the existing released annotations. Set both release and decision `review` fields to traceable editor review references.

Each decision contains the proposal ID and one of these actions.

- `accept` stages the suggested tags.
- `correct` stages explicit `tags` from the same facet.
- `unclassified` records the reviewed choice to leave the subject unassigned.

```sh
umask 077
node research-context-cli.mjs CURRENT_PAGES promote review.json > reviewed-context-1.json
FASTEST_CONTEXT_RELEASE=reviewed-context-1.json node research-context-cli.mjs CURRENT_PAGES promote next-review.json > reviewed-context-2.json
node research-context-cli.mjs CURRENT_PAGES rollback reviewed-context-2.json reviewed-context-1.json > restored-context.json
FASTEST_CONTEXT_RELEASE=restored-context.json node research-context-cli.mjs CURRENT_PAGES suggest together-evaluation-methods
```

The files hold the approved editorial assignments and audit history for the suggestion workflow. Keep both releases so the predecessor can be checked. A stale or withdrawn source revision requires fresh review before its decisions can be carried forward. Editors apply selected assignments through the existing annotations and rebuild Graphify. The normal Pages approval and correction workflow governs any resulting public release. Measurement eligibility continues to come from the cohort, protocol and evidence.

## Rules v1 replay

The default Pages research release `v1-09d6dff4b52d4427` contains nine development sources and four held-out sources across three publisher families. The held-out sources are two articles, one blog and one forum post. Three report English and one has no recorded language.

| Facet | Subjects | Precision | Recall | Abstentions | Scope transfers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Article topic | 4 | 3/3 | 3/11 | 2/4 | 0 |
| Case task | 0 | Unavailable | Unavailable | Unavailable | Unavailable |
| Case dimension | 0 | Unavailable | Unavailable | Unavailable | Unavailable |

The default public holdout covers English and one unrecorded language. Guides and the approved llama-bench documentation example are in development. The four-source public replay measures agreement with the released annotations on that sample.

## Operator-local replay

```sh
node research-context-cli.mjs CURRENT_PAGES evaluate-local
```

The checked-in replay split extends the pinned Pages index with an `annotatedSources` allowlist from the local Graphify index. Pass a different split JSON as the next argument to replay another source. The private JSON report includes the annotation index SHA-256, Pages release, rule digest and exact held-out source IDs. It reports both language families and the language tags recorded in the input, including caption language tags. The command screens out withdrawn IDs and prefers the pinned Pages revision when a source appears in both inputs. Publication and assignment review require the existing release workflow. [Operator-local split](context-calibration-local-split.json)

On `v1-09d6dff4b52d4427`, the default local replay held out 18 sources from nine families and kept four sources in development. It held out whole sources, including both forecast cross-posts and all eight guides. The newly held-out source is the `zh-HK` video from 零度解说. Its publisher and video are absent from the prior splits and rule-authoring fixtures, and the supplied index lists no cross-post for that video. The `zh-Hant` source was already held out. Both runs use the frozen v1 rule digest `2940be1a7b631482da34a22f35044f7f6a88a99afe43258a17c628cf9471e037` and annotation index SHA-256 `323e3e34d1a5d522a66477ea14ba49e622eead0f079067edc273ff06186365f3`.

Each cell lists precision, recall and abstentions as fractions. A dash indicates that the corresponding denominator is zero.

| Holdout | Sources | Article topic | Case task | Case dimension |
| --- | ---: | --- | --- | --- |
| All | 18 | 4/4, 4/53, 15/18 | 7/7, 7/17, 102/108 | 91/92, 91/108, 16/108 |
| English | 14 | 4/4, 4/42, 11/14 | 7/7, 7/14, 73/79 | 74/74, 74/79, 5/79 |
| Chinese language family | 3 | —, 0/9, 3/3 | —, 0/3, 29/29 | 17/18, 17/29, 11/29 |
| `zh` | 1 | —, 0/3, 1/1 | —, 0/2, 13/13 | 9/10, 9/13, 3/13 |
| `zh-Hant` | 1 | —, 0/3, 1/1 | —, —, 11/11 | 7/7, 7/11, 4/11 |
| `zh-HK` | 1 | —, 0/3, 1/1 | —, 0/1, 5/5 | 1/1, 1/5, 4/5 |
| Unrecorded language | 1 | —, 0/2, 1/1 | — | — |
| Guide | 8 | 1/1, 1/24, 7/8 | — | — |
| Article | 2 | 1/1, 1/6, 1/2 | — | — |
| Blog | 1 | 2/2, 2/3, 0/1 | — | — |
| Forum post | 1 | —, 0/2, 1/1 | — | — |
| Video | 6 | —, 0/18, 6/6 | 7/7, 7/17, 102/108 | 91/92, 91/108, 16/108 |

All three Chinese-language sources had full topic and task abstention. The dimension scores reflect the English metric strings in the local annotations. The lone false dimension tag in the `zh` source was `prefill` on `V045-P010`, a cached-prefill wall-power record annotated as energy.

The Hong Kong note supplies three timestamped article topics and five case records. The rules proposed prefill on `V014-P001` and abstained on the other four dimensions. They also missed the sole case task, fine-tuning on `V014-P002`. The note's image-generation discussion, hardware-based model selection and language-model claims have distinct locators. The case labels describe the caption-derived material for discovery evaluation. The data carry no independent measurement verification, and the general acceleration rows lack clear LLM-specific scope. [Local note 014](../../../../docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/014-ao6B7GR8tQY.md)

The replay found zero article-to-case transfers across 108 task subjects. Note 024 kept the Python challenge and five-depth retrieval on their own records, and the uncached prefill observation had no task suggestion. The HumanEval blog contributed two correct article topics and had zero case subjects. Across six annotated forecasts, five received a projection suggestion and `V021-P011` drew an abstention. None received a measurement dimension.

### Taiwan regression replay

The Taiwan source `youtube/DEPF8rAprS4` was on the development side of the earlier local replay. Its own frozen-rules report covers one source and one family outside the default holdout counts. The case labels cover the available captions, whose final 67.2 seconds are missing relative to the listed duration. [Local note 042](../../../../docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/042-DEPF8rAprS4.md)

```sh
node research-context-cli.mjs CURRENT_PAGES evaluate-local wiki/context-calibration-zh-tw-regression-split.json
```

| Recorded language | Sources | Article topic | Case task | Case dimension |
| --- | ---: | --- | --- | --- |
| `zh-TW` | 1 | —, 0/2, 1/1 | —, —, 3/3 | 2/2, 2/3, 1/3 |

The two generation labels matched the reported ordinary and draft-assisted generation records. The rules abstained on the retained-intelligence claim, which the local note marks as marketing with an undefined evaluation basis. The three Taiwan case records have zero annotated task labels.

Both regional videos need an approved metadata revision to enter live suggestions. Applying a suggestion requires an explicit editor decision. The reviewed-release rollback commands above restore the immediate eligible predecessor. Benchmark eligibility still comes from the cohort, protocol and evidence.
