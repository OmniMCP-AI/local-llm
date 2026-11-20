import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const readJson = async (name) => JSON.parse(await readFile(name, "utf8"));
export const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

export async function readResearchSnapshot(root, release) {
  const wiki = await readJson(join(root, "wiki/manifest.json"));
  const pin = release ?? wiki.researchRelease;
  if (!/^v1-[a-f0-9]{16}$/.test(pin)) throw new Error("Invalid research release");
  const folder = join(root, "research", pin);
  const [bytes, manifest] = await Promise.all([readFile(join(folder, "index.json")), readJson(join(folder, "manifest.json"))]);
  const index = JSON.parse(bytes);
  if (index.release !== pin || manifest.release !== pin || manifest.artifacts["index.json"] !== digest(bytes)) {
    throw new Error("Research index and release manifest disagree");
  }
  return { wiki, index };
}
