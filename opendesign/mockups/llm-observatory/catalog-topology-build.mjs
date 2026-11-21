import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export async function readCatalogPhotos(directory, scope = "component") {
  const assets = new URL("hardware-assets/", directory);
  const index = JSON.parse(await readFile(new URL("assets.json", assets), "utf8"));
  const scopes = Array.isArray(scope) ? scope : [scope];
  const entries = Object.entries(index).flatMap(([id, { scope: assetScope = "component", ...asset }]) =>
    scopes.includes(assetScope) ? [[id, asset]] : []);
  return Object.fromEntries(await Promise.all(entries.map(async ([id, { noticeFile, ...asset }]) => {
    if (!/^[a-z0-9-]+\.jpg$/.test(asset.file) || !asset.alt || !asset.credit || !asset.author || !asset.license ||
        !asset.source?.startsWith("https://") || !asset.licenseUrl?.startsWith("https://") ||
        (noticeFile !== undefined && !/^[a-z0-9-]+\.txt$/.test(noticeFile))) {
      throw new Error("Hardware photo lacks a reviewed file or attribution: " + id);
    }
    const jpeg = await readFile(new URL(asset.file, assets));
    const licenseNotice = noticeFile && (await readFile(new URL(noticeFile, assets), "utf8")).trim();
    return [id, {
      ...asset, ...(licenseNotice && { licenseNotice }), sha256: createHash("sha256").update(jpeg).digest("hex"),
      data: "data:image/jpeg;base64," + jpeg.toString("base64"),
    }];
  })));
}
