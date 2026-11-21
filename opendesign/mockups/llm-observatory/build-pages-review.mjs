import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { hardwareDirectoryPath } from "./catalog-paths.mjs";
import { importLocalCatalog } from "./catalog-pg.mjs";
import { withLocalPages } from "./pages-test-server.mjs";

const run = promisify(execFile);
const here = fileURLToPath(new URL(".", import.meta.url));
const [directory, expectedHead] = process.argv.slice(2);
if (!directory || !/^[a-f0-9]{40}$/.test(expectedHead ?? "")) {
  throw new Error("Usage: node build-pages-review.mjs <new output directory> <expected checkout SHA>");
}
const { stdout } = await run("git", ["show", "-s", "--format=%H%n%cs", "HEAD"], { cwd: here });
const [head, releaseDate] = stdout.trim().split("\n");
if (head !== expectedHead) throw new Error("Pages review checkout does not match the requested commit");
await run("git", ["diff", "--quiet", "HEAD", "--"], { cwd: here });
const { FASTEST_TEST_DATABASE_URL: publisher, FASTEST_TEST_CATALOG_READER_URL: reader } = process.env;
if (!publisher || !reader || publisher === reader) {
  throw new Error("Pages review requires a disposable catalog database and a separate catalog reader");
}

const output = resolve(directory);
const canonicalOrigin = "http://127.0.0.1:8788";
const signal = AbortSignal.timeout(90_000);
await mkdir(output);
try {
  const { snapshotId } = await importLocalCatalog(await readHardwareCatalog(here), publisher, () => false);
  const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => !name.startsWith("FASTEST_")));
  await run(process.execPath, ["build.mjs", "--pages", "--catalog-postgres", "--review", "--output", output], {
    cwd: here, signal, env: {
      ...env,
      FASTEST_CATALOG_DATABASE_URL: reader,
      FASTEST_CATALOG_SNAPSHOT_ID: snapshotId,
      FASTEST_RELEASE_DATE: releaseDate,
      FASTEST_PUBLIC_ORIGIN: canonicalOrigin,
    },
  });

  const wikiPath = "/wiki/manifest.json";
  const { release: wikiRelease, catalogRelease, researchRelease, highlights } =
    JSON.parse(await readFile(join(output, wikiPath), "utf8"));
  const catalogPath = `/catalog/${catalogRelease}/manifest.json`;
  const catalog = JSON.parse(await readFile(join(output, catalogPath), "utf8"));
  if (catalog.snapshotId !== snapshotId || catalog.release !== catalogRelease) {
    throw new Error("Pages review output does not match the replayed catalog pin");
  }
  const discovery = Object.fromEntries(await Promise.all(["/robots.txt", "/sitemap.xml", "/llms.txt", "/_redirects"]
    .map(async (path) => [path, createHash("sha256").update(await readFile(join(output, path))).digest("hex")])));
  const manifest = {
    schemaVersion: 1,
    status: "non-production-review",
    head,
    releaseDate,
    canonicalOrigin,
    wiki: {
      release: wikiRelease,
      manifest: wikiPath,
      highlights: highlights.map(({ id, href, markdown }) => ({ id, href, markdown })),
    },
    research: { release: researchRelease, manifest: `/research/${researchRelease}/manifest.json` },
    catalog: { release: catalogRelease, snapshotId, manifest: catalogPath,
      directory: { html: hardwareDirectoryPath(catalogRelease), markdown: hardwareDirectoryPath(catalogRelease, true) } },
    discoverySha256: discovery,
  };
  await writeFile(join(output, "review-manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  await withLocalPages(output, signal, async (servedOrigin) => {
    const { stdout } = await run(process.execPath, ["verify-pages.mjs", servedOrigin, canonicalOrigin, "--review"], { cwd: here, signal });
    console.log(stdout.trim());
  }, { staticOnly: true });
  console.log(`Pages review for ${head}, catalog snapshot ${snapshotId}`);
} catch (error) {
  await rm(output, { recursive: true, force: true });
  throw error;
}
