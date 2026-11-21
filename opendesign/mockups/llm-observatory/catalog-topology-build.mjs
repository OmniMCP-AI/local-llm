import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export async function readCatalogPhotos(directory) {
  const assets = new URL("hardware-assets/", directory);
  const index = JSON.parse(await readFile(new URL("assets.json", assets), "utf8"));
  return Object.fromEntries(await Promise.all(Object.entries(index).map(async ([id, asset]) => {
    if (!/^[a-z0-9-]+\.jpg$/.test(asset.file) || !asset.credit || !asset.author || !asset.license ||
        !asset.source?.startsWith("https://") || !asset.licenseUrl?.startsWith("https://")) {
      throw new Error("Hardware photo lacks a reviewed file or attribution: " + id);
    }
    const jpeg = await readFile(new URL(asset.file, assets));
    return [id, {
      ...asset, sha256: createHash("sha256").update(jpeg).digest("hex"),
      data: "data:image/jpeg;base64," + jpeg.toString("base64"),
    }];
  })));
}
