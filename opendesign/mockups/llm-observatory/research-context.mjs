import { digest } from "./research-released-snapshot.mjs";

const engineVersion = 1;
const facets = ["topic", "task", "dimension"];
const hash = (value) => digest(JSON.stringify(value));
const normalized = (text) => text.normalize("NFKC").toLowerCase().match(/[\p{L}\p{N}]+/gu)?.join(" ") ?? "";
const compact = (text) => normalized(text).replaceAll(" ", "");
const language = (source) => source.language?.toLowerCase().split("-")[0] ?? "unknown";
const nonempty = (text) => typeof text === "string" && text.trim().length > 0;
const ratio = (numerator, denominator) => denominator ? numerator / denominator : null;
const slotKey = ({ source, subject, facet }) => JSON.stringify([source, subject, facet]);

function calibrationSplit(sources, plan, knownCrossPosts) {
  const { heldOut, crossPosts } = plan ?? {};
  if (!Array.isArray(heldOut) || !heldOut.every(nonempty) || !Array.isArray(crossPosts) ||
      crossPosts.some((family) => !Array.isArray(family) || family.length < 2 || !family.every(nonempty))) {
    throw new Error("Calibration requires heldOut source IDs and crossPosts source families");
  }
  const requested = new Set(heldOut);
  const eligible = new Set(sources.map(({ id }) => id));
  const groups = new Map(sources.map(({ id }) => [id, new Set([id])]));
  const join = (family, kind) => {
    const members = family.filter((id) => eligible.has(id));
    if (new Set(members.map((id) => requested.has(id))).size > 1) {
      throw new Error("Calibration split divides " + kind);
    }
    const group = new Set(members.flatMap((id) => [...groups.get(id)]));
    for (const id of group) groups.set(id, group);
  };
  for (const family of [...knownCrossPosts, ...crossPosts]) join(family, "an eligible cross-post family");

  const publishers = Map.groupBy(sources, ({ publisher }) => publisher.toLowerCase().trim());
  for (const publications of publishers.values()) join(publications.map(({ id }) => id), "a publisher");
  return {
    requested, unavailable: [...requested].filter((id) => !eligible.has(id)).length,
    heldOutFamilies: new Set([...requested].flatMap((id) => groups.has(id) ? [groups.get(id)] : [])).size,
  };
}

function facetMetrics(samples) {
  let tp = 0;
  let fp = 0;
  let fn = 0;
  let abstentions = 0;
  const wrongScope = { articleToCase: 0, forecastAsMeasurement: 0 };
  for (const { proposal, gold, source } of samples) {
    const tags = proposal.matches.map(({ tag }) => tag);
    if (tags.length === 0) abstentions++;
    for (const tag of tags) {
      if (gold.includes(tag)) {
        tp++;
        continue;
      }
      fp++;
      if (proposal.facet === "task" && Object.hasOwn(source.topics, tag)) wrongScope.articleToCase++;
      if (proposal.facet === "dimension" && gold.includes("projection")) wrongScope.forecastAsMeasurement++;
    }
    fn += gold.filter((tag) => !tags.includes(tag)).length;
  }
  return {
    subjects: samples.length, tp, fp, fn, precision: ratio(tp, tp + fp), recall: ratio(tp, tp + fn),
    abstentions, abstentionRate: ratio(abstentions, samples.length), wrongScope,
  };
}

function reportFacets(samples) {
  return Object.fromEntries(facets.map((facet) =>
    [facet, facetMetrics(samples.filter(({ proposal }) => proposal.facet === facet))]));
}

export function createContextReview(index, rules, knownCrossPosts = []) {
  const { taxonomyVersion, vocabulary, sources } = index;
  const validTags = { topic: vocabulary.topics, task: vocabulary.topics, dimension: vocabulary.dimensions };
  if (!Number.isSafeInteger(rules.version) || rules.version < 1 || rules.taxonomyVersion !== taxonomyVersion ||
      !Array.isArray(rules.languages) || !rules.languages.every(nonempty) ||
      !Array.isArray(rules.projectionMarkers) || !rules.projectionMarkers.every(compact)) {
    throw new Error("Rules must use a positive version and the released taxonomy");
  }
  const ruleDigest = hash({ engineVersion, rules, vocabulary });
  const aliases = Object.fromEntries(facets.map((facet) => {
    const additions = rules[facet] ?? {};
    if (Object.entries(additions).some(([tag, terms]) => !Object.hasOwn(validTags[facet], tag) ||
      !Array.isArray(terms) || !terms.every((term) => nonempty(term) && compact(term)))) {
      throw new Error("Unrecognized tag or empty alias for facet " + facet);
    }
    return [facet, Object.keys(validTags[facet]).sort().map((tag) => [
      tag, [...new Set([...(additions[tag] ?? []), ...(facet === "task" ? [] : vocabulary.aliases[tag] ?? [])])],
    ])];
  }));
  const matches = (facet, fields) => {
    return aliases[facet].flatMap(([tag, terms]) => {
      for (const [field, text] of Object.entries(fields)) {
        const term = terms.find((alias) => {
          // Raw observation labels are often compact. Overview prose uses word boundaries.
          if (facet !== "topic") return compact(text).includes(compact(alias));
          if (/\p{Script=Han}/u.test(alias)) return normalized(text).includes(normalized(alias));
          return (" " + normalized(text) + " ").includes(" " + normalized(alias) + " ");
        });
        if (term) return [{ tag, field, term }];
      }
      return [];
    });
  };

  const bySource = new Map();
  const byId = new Map();
  const bySlot = new Map();
  for (const source of sources) {
    const rows = [];
    const sourceRevision = hash(source);
    const supported = rules.languages.includes(language(source));
    const slot = (subject, facet, locator, found, gold, evidence) => {
      const proposal = { source: source.id, sourceRevision, subject, facet, locator, ruleDigest, matches: found,
        ...(evidence && { evidence }) };
      proposal.id = hash(proposal);
      const row = { proposal, gold, source };
      rows.push(row);
      byId.set(proposal.id, row);
      bySlot.set(slotKey(proposal), row);
    };
    slot(source.id, "topic", source.url, supported ? matches("topic", { title: source.title, context: source.context }) : [],
      Object.keys(source.topics));
    for (const record of source.records) {
      const fields = { metric: record.metric };
      let dimensions = matches("dimension", fields);
      const projection = Object.entries({ evidence: record.evidence, metric: record.metric, conditions: record.conditions })
        .map(([field, text]) => [field, rules.projectionMarkers.find((marker) => compact(text).includes(compact(marker)))])
        .find(([, marker]) => marker);
      if (projection) {
        const [field, term] = projection;
        dimensions = [{ tag: "projection", field, term }];
      } else if (dimensions.length !== 1) {
        dimensions = [];
      }
      slot(record.id, "task", record.url, supported ? matches("task", fields) : [], record.topics, record.evidence);
      slot(record.id, "dimension", record.url, dimensions, [record.dimension], record.evidence);
    }
    bySource.set(source.id, rows);
  }

  function evaluate(plan, { includeBreakdowns = false } = {}) {
    const { requested, unavailable, heldOutFamilies } = calibrationSplit(sources, plan, knownCrossPosts);
    const heldOut = sources.filter(({ id }) => requested.has(id)).map(({ id }) => id).sort();
    const samples = heldOut.flatMap((id) => bySource.get(id));
    const counts = (keys, keyFor) => Object.fromEntries([...new Set([...keys, ...sources.map(keyFor)])].sort().map((key) => [
      key, { heldOut: sources.filter((source) => keyFor(source) === key && requested.has(source.id)).length,
        development: sources.filter((source) => keyFor(source) === key && !requested.has(source.id)).length },
    ]));
    const coverage = {
      languages: counts([...rules.languages, "en", "zh", "es", "ja", "ko", "de", "hi", "fr", "ar"], language),
      formats: counts(Object.keys(vocabulary.formats), ({ format }) => format),
    };
    const missingCoverage = Object.fromEntries(Object.entries(coverage).map(([kind, values]) =>
      [kind, Object.keys(values).filter((key) => values[key].heldOut === 0)]));
    const metrics = reportFacets(samples);
    const groupedFacets = (keyFor) => Object.fromEntries(Array.from(
      Map.groupBy(samples, ({ source }) => keyFor(source)), ([key, rows]) => [key, reportFacets(rows)],
    ));
    return {
      researchRelease: index.release, taxonomyVersion, rulesVersion: rules.version, ruleDigest,
      heldOut, heldOutFamilies, unavailableHeldOut: unavailable, development: sources.length - heldOut.length, coverage, missingCoverage,
      facets: metrics, untestedFacets: facets.filter((facet) => metrics[facet].recall === null),
      ...(includeBreakdowns && {
        facetsByLanguage: groupedFacets(language),
        facetsByFormat: groupedFacets(({ format }) => format),
      }),
      automaticPromotion: false, modelTraining: false,
    };
  }

  function suggest(id) {
    const rows = bySource.get(id);
    if (!rows) throw new Error("Source is not eligible in the current released research snapshot");
    return rows.map(({ proposal }) => proposal);
  }

  function validateRelease(release) {
    const { id, ...payload } = release ?? {};
    if (!nonempty(payload.review) || id !== "context-" + hash(payload) || !Array.isArray(payload.assignments) ||
        !Array.isArray(payload.examples) || !Array.isArray(payload.calibration?.heldOut)) {
      throw new Error("Expected an intact reviewed context release");
    }
    for (const item of [...payload.assignments, ...payload.examples]) {
      if (bySlot.get(slotKey(item))?.proposal.sourceRevision !== item.sourceRevision) {
        throw new Error("Reviewed context release refers to an unavailable source revision");
      }
    }
    if (payload.calibration.heldOut.some((source) => !bySource.has(source))) {
      throw new Error("Reviewed context release refers to an unavailable held-out source");
    }
  }

  function promote({ review, plan, examples, decisions, prior }) {
    if (!nonempty(review) || !Array.isArray(decisions) || !decisions.length || !Array.isArray(examples) ||
      !examples.some(({ expected }) => expected === true) || !examples.some(({ expected }) => expected === false)) {
      throw new Error("A release requires an editorial review, decisions, and positive and negative annotation examples");
    }
    const calibration = evaluate(plan);
    if (!calibration.heldOut.length) throw new Error("A release requires at least one eligible held-out source");
    const heldOut = new Set(calibration.heldOut);
    const citedExamples = examples.map((item) => {
      if (heldOut.has(item.source)) throw new Error("Review examples must come from development sources");
      const row = bySlot.get(slotKey(item));
      if (!row || !Object.hasOwn(validTags[item.facet], item.tag) || row.gold.includes(item.tag) !== item.expected) {
        throw new Error("Calibration example does not agree with the released annotation at the proposed scope");
      }
      const { source, subject, facet, locator, sourceRevision } = row.proposal;
      const cited = facet === "topic" && item.expected ? row.source.topics[item.tag] : null;
      return { source, subject, facet, locator: cited === "frontmatter.use_cases" ? locator + " (frontmatter.use_cases)" : cited ?? locator,
        sourceRevision, tag: item.tag, expected: item.expected };
    });

    if (prior) {
      validateRelease(prior);
      if (rules.version < prior.rules.version ||
          (ruleDigest !== prior.calibration.ruleDigest && rules.version === prior.rules.version)) {
        throw new Error("Changed context rules require a new version");
      }
    }
    const assignments = new Map((prior?.assignments ?? []).map((item) => [slotKey(item), item]));
    const reviewed = new Set();
    for (const { proposal: proposalId, action, review: decisionReview, tags } of decisions) {
      const proposal = byId.get(proposalId)?.proposal;
      if (!proposal || !nonempty(decisionReview) || reviewed.has(proposalId) ||
          !["accept", "correct", "unclassified"].includes(action)) {
        throw new Error("Expected one explicit editorial decision per current proposal");
      }
      const chosen = action === "accept" ? proposal.matches.map(({ tag }) => tag) : tags;
      if ((action === "unclassified" && tags !== undefined) || (action === "accept" && tags !== undefined) ||
          (action !== "unclassified" && (!Array.isArray(chosen) || !chosen.length ||
            chosen.some((tag) => !Object.hasOwn(validTags[proposal.facet], tag)) ||
            (proposal.facet === "dimension" && chosen.length !== 1)))) {
        throw new Error("Invalid tag selection for proposal facet");
      }
      const { id, matches: suggested, ...scope } = proposal;
      reviewed.add(id);
      assignments.set(slotKey(proposal), { ...scope, proposal: id, action, review: decisionReview,
        tags: [...new Set(chosen ?? [])].sort(), suggested });
    }
    const payload = { prior: prior?.id ?? null, review, rules, calibration, examples: citedExamples,
      assignments: [...assignments.values()] };
    return { id: "context-" + hash(payload), ...payload };
  }

  function rollback(current, prior) {
    validateRelease(current);
    validateRelease(prior);
    if (current.prior !== prior.id) throw new Error("Rollback must select the immediate reviewed predecessor");
    return prior;
  }

  function useReviewed(release) {
    validateRelease(release);
    if (ruleDigest !== release.calibration.ruleDigest) {
      throw new Error("Reviewed rules and the current released vocabulary disagree");
    }
  }

  return { suggest, evaluate, promote, rollback, useReviewed };
}
