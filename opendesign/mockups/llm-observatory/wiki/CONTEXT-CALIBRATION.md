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

The split file takes `heldOut` source IDs and additional `crossPosts` arrays of related source IDs. All observations from one source stay together. Publisher groups and registered cross-post families stay on one side of the split. Use development sources for rule edits and record cited positive and hard negative labels from those sources. Use untouched sources and families for each rule change’s final check. An unapproved or withdrawn source contributes no examples.

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

The default Pages research release `v1-b2e3f39a779d2e05` contains eight English guides in development and four held-out sources across three publisher families. The held-out sources are two articles, one blog and one forum post. Three report English and one has no recorded language.

| Facet | Subjects | Precision | Recall | Abstentions | Scope transfers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Article topic | 4 | 3/3 | 3/11 | 2/4 | 0 |
| Case task | 0 | Unavailable | Unavailable | Unavailable | Unavailable |
| Case dimension | 0 | Unavailable | Unavailable | Unavailable | Unavailable |

The current public metadata supplies no Chinese or video holdout. Guides are present only in development. Test fixtures use existing annotations to exercise note 024, a forecast, Chinese video, and a grouped cross-post replay. The four-source public replay measures agreement with the released annotations on that sample.
