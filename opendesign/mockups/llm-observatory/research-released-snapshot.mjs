import { createHash } from "node:crypto";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";

export const readJson = async (name) => JSON.parse(await readFile(name, "utf8"));
export const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
export const researchReleaseId = /^v1-[a-f0-9]{16}$/;
const artifactNames = ["library.html", "library.md", "index.json", "graphify.json", "library.mjs", "research-filter.mjs"];

export async function readResearchPin(root, pin, expected) {
  if (!researchReleaseId.test(pin)) throw new Error("Invalid research release");
  const folder = join(root, "research", pin);
  const manifestBytes = await readFile(join(folder, "manifest.json"));
  const manifestSha256 = digest(manifestBytes);
  const manifest = JSON.parse(manifestBytes);
  if ((expected && manifestSha256 !== expected) || manifest.release !== pin ||
      Object.keys(manifest.artifacts ?? {}).length !== artifactNames.length) {
    throw new Error("Research release manifest disagrees with " + pin);
  }
  const files = new Map(await Promise.all(artifactNames.map(async (name) => {
    const bytes = await readFile(join(folder, name));
    if (manifest.artifacts[name] !== digest(bytes)) {
      throw new Error("Research artifact and release manifest disagree: " + pin + "/" + name);
    }
    return [name, bytes];
  })));
  const index = JSON.parse(files.get("index.json"));
  if (index.release !== pin) throw new Error("Research index disagrees with " + pin);
  files.set("manifest.json", manifestBytes);
  return { index, files, manifestSha256 };
}

export async function readResearchSnapshot(root, release) {
  const wiki = await readJson(join(root, "wiki/manifest.json"));
  return { wiki, ...await readResearchPin(root, release ?? wiki.researchRelease) };
}

export function deniedResearchPin(release, paths) {
  const prefix = "/research/" + release;
  return paths.some((path) => path === prefix || path.startsWith(prefix + "/") || path === "/research/*");
}

export function allowedResearchPin({ index }, approvals, paths) {
  return !deniedResearchPin(index.release, paths) &&
    index.sources.every(({ id, publicationScope }) => approvals[id]?.status !== "withdrawn" &&
      (publicationScope === "editorial-reference" || approvals[id]?.status === "approved-metadata")) &&
    index.methods.every(({ url }) => approvals["youtube/" + new URL(url).searchParams.get("v")]?.status !== "withdrawn");
}

export async function writeResearchPin(output, { index, files }) {
  const folder = join(output, "research", index.release);
  await rm(folder, { recursive: true, force: true });
  await mkdir(folder, { recursive: true });
  await Promise.all([...files].map(([name, bytes]) => writeFile(join(folder, name), bytes)));
}
