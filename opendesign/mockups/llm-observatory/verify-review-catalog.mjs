import assert from "node:assert/strict";
import { escapeHtml, escapeMarkdown } from "./catalog-card.mjs";
import { readPublishedCatalog } from "./catalog-pg.mjs";
import { modelShard } from "./catalog-paths.mjs";

const htmlLinks = (body) => [...body.matchAll(/href="(\/[^"]*)"/g)].map(([, href]) => href);
const markdownLinks = (body) => [...body.matchAll(/\]\(<?(\/[^)>\s]+)>?\)/g)].map(([, href]) => href);
const number = new Intl.NumberFormat("en");

async function inBatches(rows, visit) {
  for (let offset = 0; offset < rows.length; offset += 12) {
    await Promise.all(rows.slice(offset, offset + 12).map(visit));
  }
}

export async function verifyReviewCatalog(catalog, review, { read, origin }) {
  const { release, snapshotId, discovery, supplement, modelShardCounts, coverage } = catalog;
  const root = `/catalog/${release}`;
  const modelPath = (row) => `${root}/models/${row.id}`;
  const runtimePath = (row) => `${root}/runtimes/${row.id}`;
  const readData = async (filename) => JSON.parse(await read(`/catalog-data/${release}/${filename}.json`, "application/json"));
  const models = new Map();
  await inBatches(Object.entries(modelShardCounts), async ([key, count]) => {
    const rows = await readData(key);
    assert.equal(rows.length, count, key);
    for (const row of rows) {
      assert.equal(modelShard(row.id), key);
      assert.ok(!models.has(row.id), row.id);
      models.set(row.id, row);
    }
  });
  assert.equal([...models.values()].filter(row => !row.supplemental || row.supplemental.inUpstream).length, coverage.publishedRows);
  const collections = Object.fromEntries(["popular", "small"].map(collection => [collection,
    [...models.values()].filter(row => row.discovery?.[collection]).sort((a, b) => a.discovery[collection].rank - b.discovery[collection].rank),
  ]));
  const repositoryOrder = row => row.id.toLowerCase() + "\0" + row.id;
  collections.recent = [...models.values()].filter(row => row.supplemental).sort((a, b) =>
    b.supplemental.revisionDate.localeCompare(a.supplemental.revisionDate) || (repositoryOrder(a) < repositoryOrder(b) ? -1 : 1));
  const runtimes = await readData("runtimes");
  assert.equal(runtimes.length, coverage.runtimeProjects);
  assert.equal(new Set(runtimes.map(row => row.id)).size, runtimes.length);
  assert.equal(collections.recent.length, supplement?.repositories ?? 0);
  assert.ok(collections.popular.length <= 300);
  for (const collection of ["popular", "small"]) {
    const rankings = collections[collection].map(row => row.discovery[collection]);
    assert.equal(rankings.length, discovery[collection], collection);
    assert.equal(new Set(rankings.map(row => row.family)).size, rankings.length, collection);
    rankings.forEach(({ rank, parameters }, index) => {
      assert.equal(rank, index + 1, collection);
      assert.ok(parameters > 0 && (collection !== "small" || parameters <= 4_000_000_000));
    });
  }

  const reader = process.env.FASTEST_TEST_CATALOG_READER_URL;
  if (reader) {
    const pinned = readPublishedCatalog(reader, snapshotId);
    const ids = new Set([...pinned.source.models, ...pinned.supplementalModels].map(row => row.id));
    assert.deepEqual(new Set(models.keys()), ids);
    assert.equal(pinned.discovery.capturedAt, discovery.capturedAt);
    assert.equal(pinned.discovery.source, discovery.source);
    for (const collection of ["popular", "small"]) {
      assert.deepEqual(collections[collection].map(row => row.discovery[collection]),
        pinned.discovery[collection].map((row, index) => ({ ...row, rank: index + 1 })));
    }
    assert.deepEqual(new Set(collections.recent.map(row => row.id)), new Set(pinned.supplementalModels.map(row => row.id)));
    assert.deepEqual(runtimes, pinned.runtimes);
  }

  async function readPair(path) {
    const [html, markdown] = await Promise.all([read(path, "text/html"), read(path + ".md", "text/markdown")]);
    assert.ok(html.includes(snapshotId) && markdown.includes(`snapshot: ${snapshotId}`), path);
    assert.ok(html.includes(`rel="canonical" href="${origin + path}"`), path);
    assert.ok(html.includes(`rel="alternate" type="text/markdown" href="${path}.md"`), path);
    assert.ok(markdownLinks(markdown).includes(path), path);
    return { html, markdown };
  }

  const lookup = review.models.lookup.html;
  const lookupPair = await readPair(lookup);
  assert.match(lookupPair.html, /<label for="repository">Exact repository ID<\/label>/);
  assert.ok(lookupPair.html.includes(`${number.format(models.size)} repositories`));
  assert.ok(lookupPair.html.includes(`<script src="${lookup}.js" defer></script>`));
  for (const [collection, rows] of Object.entries(collections)) {
    const first = review.models[collection].html;
    const pages = Math.max(1, Math.ceil(rows.length / 30));
    const paths = Array.from({ length: pages }, (_, index) => index === 0 ? first : `${root}/model-collections/${collection}-${index + 1}`);
    await inBatches(paths, async (path) => {
      const { html, markdown } = await readPair(path);
      const page = paths.indexOf(path) + 1;
      const links = htmlLinks(html);
      const companions = markdownLinks(markdown);
      assert.ok(links.includes(lookup) && companions.includes(lookup + ".md"), path);
      assert.ok(html.includes(`<dt>Collection page</dt><dd>${page} of ${pages}</dd>`), path);
      if (collection !== "recent") {
        assert.ok(html.includes(`href="${escapeHtml(discovery.source)}">${discovery.capturedAt}</a>`), path);
        assert.ok(markdown.includes(`[${discovery.capturedAt}](<${discovery.source}>)`), path);
      }
      const expected = rows.slice((page - 1) * 30, page * 30).map(modelPath);
      assert.deepEqual(links.filter(link => link.startsWith(root + "/models/")), expected, path);
      assert.deepEqual(companions.filter(link => link.startsWith(root + "/models/")), expected.map(link => link + ".md"), path);
      for (const target of paths) {
        assert.ok(paths.length === 1 || (links.includes(target) && companions.includes(target + ".md")), target);
      }
      assert.doesNotMatch(html, /<script\b/i, path);
    });
  }

  const runtimeDirectory = await readPair(review.runtimes.html);
  assert.deepEqual(htmlLinks(runtimeDirectory.html).filter(link => link.startsWith(root + "/runtimes/")), runtimes.map(runtimePath));
  assert.deepEqual(markdownLinks(runtimeDirectory.markdown).filter(link => link.startsWith(root + "/runtimes/")),
    runtimes.map(row => runtimePath(row) + ".md"));
  const modelProfiles = new Set(Object.values(collections).flat());
  const common = ["/", review.directory.html, review.directory.html + "#cards", review.directory.html + "#machines",
    review.models.popular.html, review.runtimes.html, review.models.popular.markdown, review.runtimes.markdown,
    root + "/manifest.json", root + "/LICENSE.txt"];
  const routes = new Set([...common, ...runtimes.flatMap(row => [runtimePath(row), runtimePath(row) + ".md"])]);
  async function verifyProfile(path, title, citations) {
    const { html, markdown } = await readPair(path);
    assert.ok(html.includes(`<h1>${escapeHtml(title)}</h1>`), path);
    assert.doesNotMatch(html, /<script\b/i, path);
    assert.ok([...htmlLinks(html), ...markdownLinks(markdown)].every(link =>
      routes.has(link) || link === path || link === path + ".md"), path);
    for (const citation of citations.filter(Boolean)) {
      assert.ok(html.includes(`href="${escapeHtml(citation)}"`) && markdown.includes(`<${citation}>`), path);
    }
    return { html, markdown };
  }
  await inBatches([...modelProfiles], async (row) => {
    const { html, markdown } = await verifyProfile(modelPath(row), row.id, [row.source, row.supplemental?.cardUrl,
      ...(row.identity?.artifacts ?? []).map(artifact => `https://huggingface.co/${artifact.repository}/blob/${artifact.revision}/${artifact.path}`)]);
    if (!row.supplemental || row.supplemental.inUpstream) {
      assert.ok(html.includes(`<dt>llmfit snapshot tags</dt><dd>${escapeHtml(row.detail || "Tags unavailable")}</dd>`), row.id);
      assert.ok(markdown.includes(`**llmfit snapshot tags** — ${escapeMarkdown(row.detail || "Tags unavailable")}`), row.id);
    }
    for (const [collection, label] of [["popular", "Popular"], ["small", "Small"]]) {
      const rank = row.discovery?.[collection]?.rank;
      if (rank) {
        assert.ok(html.includes(`<dt>${label} rank</dt><dd>${rank}</dd>`), row.id);
        assert.ok(markdown.includes(`**${label} rank** — ${rank}\n`), row.id);
      }
    }
  });
  await inBatches(runtimes, async (row) => {
    const { html, markdown } = await verifyProfile(runtimePath(row), row.name, [
      row.source, row.releaseUrl ?? row.source + "/releases/tag/" + row.tag, row.docs,
      row.formatSource, row.backendSource, row.latestRelease?.url, ...(row.references ?? []).map(ref => ref.href),
    ]);
    assert.ok(html.includes(`<dt>Runtime ID</dt><dd>${row.id}</dd>`), row.id);
    assert.ok(html.includes(`>${escapeHtml(row.tag)}</a>`) && markdown.includes(`[${escapeMarkdown(row.tag)}](<`), row.id);
    assert.match(html, /Tested compatibility: No fastest\.ai compatibility test is published/);
    assert.match(markdown, /Tested compatibility: No fastest\.ai compatibility test is published/);
  });
  return { inventory: models.size, modelProfiles: modelProfiles.size, runtimes: runtimes.length };
}
