# Whole-source Graphify holdout results

On two previously unused source families, v2 recovered one additional case dimension. It recognized the measured GPU power draw during the token-generation phase as electrical power. Both versions left every article topic and case task unsuggested. They also abstained on all three modeled or future claims.

The [sampling protocol](PROTOCOL.md) and [source-linked annotations](annotations.json) were committed at `c8e87f8776b3c75f71b0f3db4d2d7a36e5a707d9` before the first replay. The annotation SHA-256 is `a0425ba13c3075bc3c87ca66c7421c676a7374fd5aea5aaa1affcabd9c0737bf`. One Codex annotator applied the rubric directly to the primary sources. The annotation has no second reviewer.

## Reproduce

From the repository root on this checkout, run with Node.js 22 or later and Git history for the two pinned commits.

```sh
node docs/context-holdout/replay.mjs
node --test docs/context-holdout/replay.test.mjs
```

The replay checks the evaluator at `4f82ca83fd799880119172ee55f11e745c83c1f0` and reads both rules and the vocabulary from that commit. The report includes precision, recall, abstentions and wrong-scope counts by facet, with language and format breakdowns and source-located predictions. The two rule digests match the frozen regression releases. This operator replay uses a standalone index of the two holdout sources and has no publication or promotion path.

## Results

Precision and recall count tags across subjects. Abstentions count subjects for which the evaluator returned no tags. A dash means the precision denominator was zero.

| Facet | Subjects | v1 precision | v1 recall | v1 abstentions | v2 precision | v2 recall | v2 abstentions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Article topic | 2 | — | 0/10 | 2/2 | — | 0/10 | 2/2 |
| Case task | 18 | — | 0/14 | 18/18 | — | 0/14 | 18/18 |
| Case dimension | 18 | 13/13 | 13/18 | 5/18 | 14/14 | 14/18 | 4/18 |

| Family and source format | v1 topic recall | v1 task recall | v1 dimension recall | v2 topic recall | v2 task recall | v2 dimension recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| droid-llm, Simplified Chinese guide (`zh-Hans`) | 0/4 | 0/8 | 8/8 | 0/4 | 0/8 | 8/8 |
| Splitwise, English research article | 0/6 | 0/6 | 5/10 | 0/6 | 0/6 | 6/10 |

Both rules correctly tagged all eight handset timing cells. The metric names in the Chinese table are English acronyms and words. The local API feature appears at article scope. The real-device cells capture interactive chat, and the separately labeled export examples are placeholders. [droid-llm README](https://github.com/pisces312/droid-llm/blob/1e995146fc905f944c83873f07237abd9febdf29/README.md#L15-L63)

Both rules recognized the paper’s prompt-phase power draw. Adding the token-generation qualifier made v1 abstain. V2 still recognized power. Both versions missed the measured KV-cache transfer latency and all three projections. The two modeled figures describe throughput and provisioned power in an event-driven simulator. The third claim discusses how future conversation caching might change memory use. [Power characterization](https://arxiv.org/html/2311.18677v2#S3.SS6), [transfer experiment](https://arxiv.org/html/2311.18677v2#S6.SS1.p1.1), [simulator method](https://arxiv.org/html/2311.18677v2#S5.SS2), [modeled clusters](https://arxiv.org/html/2311.18677v2#S6.SS3), [future caching](https://arxiv.org/html/2311.18677v2#S7.p5.1)

Each version made zero false article-to-case transfers across 18 task subjects and zero false forecast-to-measurement transfers across three projection subjects. Every task and projection subject drew an abstention. Four case tasks had no expected tag. Case task evidence sits in the source context and record conditions, while these rules look at the case metric field for task suggestions.

The sample covers two publishers, two document formats and two source languages. Cases within a device session or paper share setup and reporting choices. The single corrected energy case shows how v2 handles that wording in this sample. General power recall, multilingual topic accuracy, caption coverage and forecast detection remain unestablished.
