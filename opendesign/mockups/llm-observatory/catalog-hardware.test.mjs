import assert from "node:assert/strict";
import { dirname } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { hardwareCard, renderCard } from "./catalog-card.mjs";

const here = dirname(fileURLToPath(import.meta.url));

test("GPU profile main navigation matches the home page and links back from deep paths", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const release = "v1-1234567890abcdef";
  const card = hardwareCard(catalog.cards[0], release, "cards");
  for (const local of [true, false]) {
    const html = renderCard(card, { release, pathname: `catalog/${release}/cards/${card.id}.html`, local });
    const nav = html.match(/<nav[^>]*aria-label="Main navigation"[^>]*>([\s\S]*?)<\/nav>/)?.[1];
    assert.ok(nav, "main navigation is present in the initial HTML");
    const labels = [...nav.matchAll(/<a\b[^>]*>([^<]+)<\/a>/g)].map(match => match[1]);
    assert.deepEqual(labels, ["Explorer", local ? "Compare demo" : "Compare", "Battles", "Methods", local ? "Costs demo" : "Costs", "Catalog", "Machines", "Models", "Wiki", "Price watch", "For agents"]);
    const home = local ? "../../../../fastest-ai.html" : "/";
    assert.ok(nav.includes(`href="${home}#explorer"`));
    assert.ok(nav.includes(`href="${home}#catalog" aria-current="page"`));
  }
  const hosted = renderCard(card, { release, pathname: `/catalog/${release}/cards/${card.id}.html`, releaseOrigin: "https://evidence.example" });
  assert.match(hosted, /href="https:\/\/evidence\.example\/profiles">Explorer/);
  assert.match(hosted, /href="https:\/\/evidence\.example\/advisor">Guided advisor/);
  assert.match(hosted, /href="\/wiki\/catalog\/" aria-current="page">Catalog/);
});

test("the hardware snapshot accounts for all sources and keeps memory limits separate", async () => {
  const { manifest, catalog } = await readHardwareCatalog(here);
  assert.equal(manifest.asOf, "2026-11-22");
  assert.equal(manifest.coverage.llmfitDiscreteMatchers, 72);
  assert.equal(manifest.coverage.researchProfiles, 116);
  assert.equal(manifest.coverage.researchComponentReferences, 46);
  assert.equal(manifest.coverage.partialMachines, 70);
  assert.equal(manifest.coverage.upstreamPresets, 3);
  assert.equal(manifest.coverage.completeBuilds, 4);
  assert.equal(manifest.coverage.reviewedMeasuredProfiles, 0);
  assert.equal(manifest.coverage.creatorReportedAssociations, 293);
  assert.equal(catalog.machines.length, 124 + manifest.coverage.creatorBuilds);
  assert.equal(manifest.coverage.manufacturerMachines, 5);
  assert.equal(manifest.coverage.cards, catalog.cards.length);
  assert.equal(catalog.cards.filter(card => !card.modification || card.relatedProfiles.length).length, 156);
  assert.equal(manifest.coverage.cardsWithVendorSpecs, 149);
  assert.equal(manifest.coverage.cardsWithSpecificVendorSpecs, 127);
  assert.equal(manifest.coverage.cardsWithProductImageLinks, 88);
  assert.equal(manifest.coverage.boardPartnerCards, 17);

  const find = (rows, id) => rows.find((row) => row.id === id);
  assert.equal(find(catalog.machines, "V001-HP-G001").kind, "Component reference");
  assert.equal(find(catalog.machines, "V005-HP-G002").kind, "Partial configuration");
  const capped = find(catalog.machines, "V018-HP-C002");
  assert.deepEqual(capped.memory, {
    system: null, perDevice: null, aggregate: null,
    allocation: "20 GB system RAM limit; 16 GB VRAM limit (creator reported)",
  });
  const reported = find(catalog.machines, "V022-HP-C002");
  assert.equal(reported.memory.system, null);
  assert.match(reported.memory.allocation, /46 GB.*ambiguous/i);
  assert.equal(find(catalog.machines, "llmfit-apple-m3-max-128gb").memory.system, "128 GB unified memory");

  assert.equal(find(catalog.cards, "nvidia-a100").variant, "PCIe 40 GB calibration");
  assert.equal(find(catalog.cards, "nvidia-a100-sxm").variant, "SXM calibration");
  const mi300 = find(catalog.cards, "amd-instinct-mi300");
  assert.equal(mi300.kind, "Unresolved family reference");
  assert.equal(mi300.vendorSpec.facts.Architecture, "CDNA 3");
  assert.equal(mi300.vendorSpec.facts["Memory configuration"], undefined);
  assert.equal(mi300.memory, null);
  assert.ok(find(catalog.cards, "amd-radeon-rx-7600"));
  for (const id of ["amd-radeon-instinct-mi50-16gb", "amd-radeon-instinct-mi50-32gb", "nvidia-tesla-v100-16gb", "nvidia-tesla-v100-32gb", "nvidia-tesla-v100-sxm2", "nvidia-geforce-rtx-2080-ti-colorful-modified"]) {
    assert.ok(find(catalog.cards, id), id);
  }
  assert.equal(find(catalog.machines, "V024-HP-C001").cardIds.length, 0);
  assert.deepEqual(find(catalog.machines, "V019-HP-TEST").cardIds.sort(), ["amd-radeon-rx-6600-xt", "t10-unresolved"].sort());
});

test("official memory variants retain their own specifications and family links", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  for (const [id, parent, memory, field, value] of [
    ["intel-arc-a770-8gb", "intel-arc-a770", "8 GB GDDR6", "Memory bandwidth", "512 GB/s"],
    ["nvidia-geforce-gtx-1650-gddr5", "nvidia-geforce-gtx-1650", "4 GB GDDR5", "Boost clock (MHz)", "1665"],
    ["nvidia-geforce-gtx-1650-gddr6", "nvidia-geforce-gtx-1650", "4 GB GDDR6", "Boost clock (MHz)", "1590"],
    ["nvidia-geforce-rtx-3080-10gb", "nvidia-geforce-rtx-3080", "10 GB GDDR6X", "Rated graphics power (W)", "320"],
    ["nvidia-geforce-rtx-3080-12gb", "nvidia-geforce-rtx-3080", "12 GB GDDR6X", "Rated graphics power (W)", "350"],
    ["nvidia-geforce-rtx-5060-ti-8gb", "nvidia-geforce-rtx-5060-ti", "8 GB GDDR7", "Memory bus", "128-bit"],
  ]) {
    assert.ok(cards.get(parent).variants.some(variant => variant.id === id), id);
    const { vendorSpec, relatedProfiles } = cards.get(id);
    assert.equal(vendorSpec.scope, "Exact memory variant");
    assert.equal(vendorSpec.facts["Memory configuration"], memory);
    assert.equal(vendorSpec.facts[field], value);
    assert.ok(vendorSpec.locator);
    assert.deepEqual(relatedProfiles, []);
  }
});

test("official accelerator and workstation configurations keep form-factor specifications distinct", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  for (const [id, parent, field, value] of [
    ["nvidia-a100-sxm-40gb", "nvidia-a100-sxm", "Memory bandwidth", "1555 GB/s"],
    ["nvidia-a100-sxm-80gb", "nvidia-a100-sxm", "Memory bandwidth", "2039 GB/s"],
    ["nvidia-h200-sxm", "nvidia-h200", "Maximum TDP (W)", "Up to 700 W (configurable)"],
    ["nvidia-h200-nvl", "nvidia-h200", "Form factor", "Dual-slot PCIe"],
    ["nvidia-tesla-p100-pcie-12gb", "nvidia-tesla-p100", "Memory bandwidth", "549 GB/s"],
    ["nvidia-tesla-p100-sxm2-16gb", "nvidia-tesla-p100", "Form factor", "SXM2"],
    ["nvidia-tesla-v100-pcie-32gb", "nvidia-tesla-v100-32gb", "Rated graphics power (W)", "250"],
    ["nvidia-tesla-v100-sxm2-32gb", "nvidia-tesla-v100-sxm", "Rated graphics power (W)", "300"],
    ["nvidia-rtx-pro-6000-blackwell-max-q", "nvidia-rtx-pro-6000", "Rated graphics power (W)", "300"],
  ]) {
    assert.ok(cards.get(parent).variants.some(variant => variant.id === id), id);
    const { vendorSpec, relatedProfiles } = cards.get(id);
    assert.equal(vendorSpec.facts[field], value);
    assert.ok(vendorSpec.locator);
    assert.deepEqual(relatedProfiles, []);
  }
  for (const id of ["nvidia-cmp-170hx-hynix", "nvidia-cmp-170hx-samsung", "nvidia-geforce-rtx-2080-ti-modified-22gb", "t10-unresolved"]) {
    assert.equal(cards.get(id).vendorSpec, null);
  }
});

test("the Arc Pro B60 family links exact manufacturer board specifications and galleries", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  const family = cards.get("intel-arc-pro-b60");
  for (const [id, sku, source, gallery] of [
    ["asrock-b60-ct-24g", "B60 CT 24G",
      "https://www.asrock.com/Graphics-Card/Intel/Intel%20Arc%20Pro%20B60%20Creator%2024GB/index.asp",
      "https://www.asrock.com/Graphics-Card/Intel/Intel%20Arc%20Pro%20B60%20Creator%2024GB/index.asp"],
    ["sparkle-sbp60w-24g", "SBP60W-24G",
      "https://www.sparkle.com.tw/files/20251230103738615.pdf",
      "https://www.sparkle.com.tw/en/products/view/26C8B0add19C"],
  ]) {
    assert.ok(family.variants.some(variant => variant.id === id), id);
    const board = cards.get(id);
    assert.equal(board.parent, family.id);
    assert.equal(board.variant, sku);
    assert.equal(board.vendorSpec.designation, sku);
    assert.equal(board.vendorSpec.scope, "Board-partner SKU");
    assert.equal(board.vendorSpec.facts["Memory configuration"], "24 GB GDDR6");
    assert.equal(board.vendorSpec.source, source);
    assert.equal(board.vendorSpec.gallery.source, gallery);
  }
});

test("exact factory configurations carry a sourced system bill of materials", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const builds = catalog.machines.filter(({ kind, cardIds }) => kind === "Complete factory configuration" && !cardIds.length);
  assert.deepEqual(builds.map(({ configuration, memory, documentedPower }) =>
    [configuration, memory.system, documentedPower.label, documentedPower.value]), [
    ["MCYT4LL/A", "24 GB unified memory", "Maximum continuous system power", "155 W"],
    ["MHQM4LL/A", "24 GB unified memory", "Maximum continuous system power", "155 W"],
    ["128 GB unified memory / 4 TB SSD", "128 GB LPDDR5X unified system memory", "External power supply rating", "240 W"],
  ]);
  for (const build of builds) {
    assert.deepEqual(build.cardIds, []);
    assert.equal(build.memory.perDevice, null);
    assert.equal(build.memory.aggregate, null);
    assert.equal(build.memory.allocation, null);
    assert.deepEqual(build.bom.map(({ category }) => category), [
      "CPU", "GPU", "Memory", "Storage", "Platform", "Power supply", "Cooling",
    ]);
    assert.ok(build.locator && build.documentedPower.locator);
    assert.ok(build.bom.every(({ part, quantity, source, locator }) =>
      part && quantity && new URL(source).protocol === "https:" && locator));
  }
  const family = catalog.machines.find(({ id }) => id === "nvidia-dgx-spark");
  assert.equal(family.kind, "Manufacturer system reference");
  assert.match(family.memory.system, /64 GB or 128 GB/);
  assert.equal(family.bom, undefined);
});

test("withdrawing a factory BOM source removes dependent builds and updates coverage", async () => {
  const withdrawn = "https://docs.nvidia.com/dgx/dgx-spark/hardware.html";
  const { catalog, manifest } = await readHardwareCatalog(here, value => value === withdrawn);
  assert.equal(manifest.coverage.completeBuilds, 3);
  assert.ok(catalog.machines.some(({ id }) => id === "nvidia-dgx-spark"));
  assert.ok(!catalog.machines.some(({ id }) => id === "nvidia-dgx-spark-128gb-4tb"));
  assert.ok(!JSON.stringify(catalog).includes(withdrawn));
});

test("an image source withdrawal preserves its separately sourced board specification", async () => {
  const { catalog } = await readHardwareCatalog(here, value => value?.includes("pg.asrock.com"));
  const board = catalog.cards.find(({ id }) => id === "asrock-a770-pg-16go");
  assert.equal(board.vendorSpec.designation, "A770 PG 16GO");
  assert.equal(board.vendorSpec.gallery, undefined);
  assert.ok(catalog.cards.find(({ id }) => id === "intel-arc-a770-16gb").variants.some(({ id }) => id === board.id));
});

test("a source withdrawal removes boards whose parent identity disappears", async () => {
  const { catalog } = await readHardwareCatalog(here, value => value?.endsWith("/hardware-profiles/V001-HP-G013.md"));
  assert.ok(catalog.cards.some(({ id }) => id === "amd-radeon-rx-9070-xt"));
  assert.ok(!catalog.cards.some(({ id }) => id === "amd-radeon-rx-9060-xt-16gb"));
  assert.ok(!catalog.cards.some(({ id }) => id === "asus-dual-rx9060xt-16g"));
});

test("a manufacturer source withdrawal removes independently sourced boards under that release", async () => {
  const withdrawn = "https://www.nvidia.cn/geforce/news/rtx-50-series-graphics-cards-gpu-laptop-announcements/";
  const { catalog } = await readHardwareCatalog(here, value => value === withdrawn);
  const ids = catalog.cards.map(({ id }) => id);
  assert.ok(ids.includes("nvidia-geforce-rtx-5090-d"));
  assert.ok(ids.includes("nvidia-geforce-rtx-5090-d-v2"));
  assert.ok(!ids.includes("nvidia-geforce-rtx-5090-d-32gb"));
  assert.ok(!ids.includes("asus-rog-astral-rtx5090d-o32g-gaming"));
});

test("withdrawing the Colorful launch announcement removes just its sourced RTX 5060 Ti board", async () => {
  const source = "https://www.colorful.cn/home/new?id=09e8d6a3-f28d-419e-bc68-2b25cbe99968";
  const { catalog, manifest } = await readHardwareCatalog(here, value => value === source);
  const family = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-5060-ti");
  assert.deepEqual(family.variants.map(({ id }) => id).sort(), [
    "asus-t1-rtx5060ti-o8g-gaming", "nvidia-geforce-rtx-5060-ti-16gb", "nvidia-geforce-rtx-5060-ti-8gb",
    "pny-vcg5060t8dfxpb1-o",
  ]);
  assert.equal(manifest.coverage.boardPartnerCards, 16);
  assert.ok(!JSON.stringify(catalog).includes(source));
});

test("5090 partner variants keep memory, operating modes and radiator dimensions scoped to the exact board", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  const soc = cards.get("msi-geforce-rtx-5090-32g-suprim-soc");
  const oc = cards.get("msi-geforce-rtx-5090-32g-suprim-oc");
  const liquid = cards.get("msi-geforce-rtx-5090-32g-suprim-liquid-soc");
  const original = cards.get("msi-geforce-rtx-5090-d-32g-vanguard-oc");
  const v2 = cards.get("msi-geforce-rtx-5090-d-v2-24g-ventus-3x-oc");
  assert.deepEqual([soc, oc, liquid].map(card => card.vendorSpec.designation), ["G5090-32SPS", "G5090-32SPC", "G5090-32SLS"]);
  assert.equal(soc.vendorSpec.facts["Power mode ratings"], "600 W gaming mode; 575 W silent mode");
  assert.equal(oc.vendorSpec.facts["Rated graphics power (W)"], "575");
  assert.equal(soc.vendorSpec.facts["Radiator dimensions"], undefined);
  assert.equal(liquid.vendorSpec.facts["Radiator dimensions"], "394 × 121 × 55 mm");
  assert.equal(original.parent, "nvidia-geforce-rtx-5090-d-32gb");
  assert.equal(v2.parent, "nvidia-geforce-rtx-5090-d-v2");
  assert.deepEqual([original, v2].map(card => card.vendorSpec.facts["Memory configuration"]), ["32 GB GDDR7", "24 GB GDDR7"]);
});

test("reviewed machines expose creator build facts, attributed media and withdrawal behavior", async () => {
  const { catalog, manifest } = await readHardwareCatalog(here);
  const builds = catalog.machines.filter(({ kind }) => kind === "Creator-reported build");
  assert.ok(builds.length >= 12);
  assert.equal(manifest.coverage.creatorBuilds, builds.length);
  assert.ok(builds.every(row => row.bom.length && row.bom.every(part => part.source === row.source)));
  assert.ok(builds.every(row => row.associations === undefined && row.fit === undefined));
  assert.deepEqual([...new Set(builds.map(row => row.buildSource.platform))].sort(), [
    "Builder site", "GitHub", "Reddit", "X", "YouTube",
  ]);

  const release = "v1-1234567890abcdef";
  const createCard = (row, markdown = false) => renderCard(hardwareCard(row, release, "machines"), {
    release, pathname: `/catalog/${release}/machines/${row.id}.${markdown ? "md" : "html"}`, markdown,
  });
  const cluster = builds.find(({ id }) => id === "geerling-compute-blade-cluster");
  assert.match(createCard(cluster), /<iframe[^>]+youtube-nocookie.com\/embed\/8SiB-bNyP5E/);
  assert.match(createCard(cluster, true), /youtube.com\/watch\?v=8SiB-bNyP5E/);
  assert.match(createCard(cluster), /Publisher thumbnail by Jeff Geerling/);

  const mixed = builds.find(({ id }) => id === "sanasol-home-llm-rtx-5090-dual-rtx-3090");
  assert.match(createCard(mixed, true), /github\.com\/sanasol\/home-llm\/blob\/[a-f0-9]{40}\/assets\/rig-irl\.jpg/);

  const wrx90 = builds.find(({ id }) => id === "cangemi-wrx90-dual-rtx-3090");
  assert.equal(wrx90.bom.find(({ category }) => category === "GPU").quantity, 2);
  assert.equal((createCard(wrx90).match(/<figure>/g) ?? []).length, 3);
  assert.equal((createCard(wrx90).match(/Copyright \(c\) 2026 Zachary Cangemi/g) ?? []).length, 1);

  const spark = catalog.machines.find(({ id }) => id === "nvidia-dgx-spark-128gb-4tb");
  assert.equal((createCard(spark).match(/<figure>/g) ?? []).length, 3);
  assert.match(createCard(spark, true), /CC BY-SA 4\.0/);
  const { catalog: filtered } = await readHardwareCatalog(here, value =>
    value === cluster.source || value?.includes("File:Nvidia_DGX_front_view_dllu.jpg"));
  assert.ok(!filtered.machines.some(({ id }) => id === cluster.id));
  assert.equal(filtered.machines.find(({ id }) => id === spark.id).photos.length, 2);
});

test("a partial cluster profile links to its source video at the disclosure, with creator credit", async () => {
  const { catalog, manifest } = await readHardwareCatalog(here);
  assert.equal(manifest.coverage.partialMachinesWithSourceVideo, 14);
  const release = "v1-1234567890abcdef";
  const profile = (id, markdown = false) => renderCard(hardwareCard(
    catalog.machines.find(row => row.id === id), release, "machines",
  ), { release, pathname: `/catalog/${release}/machines/${id}.${markdown ? "md" : "html"}`, markdown });

  const html = profile("V059-HP-TEST");
  assert.match(html, /i\.ytimg\.com\/vi\/4l4UWZGxvoc\/hqdefault\.jpg/);
  assert.match(html, /www\.youtube\.com\/watch\?v=4l4UWZGxvoc&amp;t=44s/);
  assert.match(html, /youtube-nocookie\.com\/embed\/4l4UWZGxvoc\?start=44/);
  assert.match(html, /Publisher thumbnail by jakkuh/);
  assert.match(html, /may depict the video topic/);
  assert.match(profile("V059-HP-TEST", true), /Publisher thumbnail by jakkuh/);
  assert.match(profile("V053-HP-C001"), /youtube-nocookie\.com\/embed\/RkzCAaIV_cQ\?start=80/);
  assert.match(profile("V053-HP-C002"), /youtube-nocookie\.com\/embed\/RkzCAaIV_cQ\?start=140/);
  assert.doesNotMatch(profile("V019-HP-E02"), /<figure class="profile-video"/);
  assert.doesNotMatch(profile("V001-HP-G001", true), /YouTube thumbnail/);
});

test("withdrawing a publisher thumbnail hides its media without removing the machine disclosure", async () => {
  const { catalog, manifest } = await readHardwareCatalog(here,
    value => value === "https://i.ytimg.com/vi/4l4UWZGxvoc/hqdefault.jpg");
  const cluster = catalog.machines.find(({ id }) => id === "V059-HP-TEST");
  assert.equal(cluster.video, undefined);
  assert.equal(cluster.capture, "https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s");
  assert.equal(manifest.coverage.partialMachinesWithSourceVideo, 13);
});

test("GPU photo galleries publish exact models with photo and license links", async () => {
  const { catalog, manifest } = await readHardwareCatalog(here);
  const card = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-5090");
  assert.ok(card.photos?.length > 1);
  assert.ok(card.photos.some(({ alt }) => alt.includes("Palit")));
  assert.ok(!catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-5090-d-32gb").photos);
  const photographed = catalog.cards.filter(({ photos }) => photos?.length);
  assert.ok(photographed.length >= 12);
  assert.equal(manifest.coverage.cardsWithPhotos, photographed.length);
  assert.ok(photographed.every(({ modification }) => !modification));
  const photos = photographed.flatMap(({ photos }) => photos);
  assert.equal(new Set(photos.map(({ source }) => source)).size, photos.length);
  assert.equal(new Set(photos.map(({ sha256 }) => sha256)).size, photos.length);
  for (const { author, credit, license, licenseUrl } of photos) {
    assert.ok(credit.includes(author) && /resized|converted to JPEG/.test(credit), credit);
    const licensePath = license === "CC0 1.0" ? "publicdomain/zero/1.0/" :
      "licenses/" + license.slice(3).toLowerCase().replace(" ", "/") + "/";
    assert.equal(licenseUrl, "https://creativecommons.org/" + licensePath, credit);
  }

  const release = "v1-1234567890abcdef";
  for (const markdown of [false, true]) {
    const pathname = `/catalog/${release}/cards/${card.id}.${markdown ? "md" : "html"}`;
    const page = renderCard(hardwareCard(card, release, "cards"), { release, pathname, markdown });
    for (const { source, licenseUrl, author } of card.photos) {
      assert.ok(page.includes(source) && page.includes(licenseUrl) && page.includes(author), pathname);
    }
    if (!markdown) assert.equal((page.match(/data:image\/jpeg;base64,/g) ?? []).length, card.photos.length);
  }

  const { catalog: filtered } = await readHardwareCatalog(here, source => source === card.photos[0].source);
  const filteredCard = filtered.cards.find(({ id }) => id === card.id);
  assert.deepEqual(filteredCard.photos, card.photos.slice(1));
  assert.deepEqual(filteredCard.vendorSpec.gallery, card.vendorSpec.gallery);
});

test("a GPU photo stays on the exact board when the catalog also contains other variants", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const card = id => catalog.cards.find(row => row.id === id);
  assert.ok(card("pny-vcg5060t16dfxpb1-o").photos.every(photo => photo.alt.includes("PNY") && photo.alt.includes("16 GB")));
  assert.equal(card("pny-vcg5060t8dfxpb1-o").photos, undefined);
  assert.equal(card("intel-arc-a770-8gb").photos, undefined);
  assert.equal(card("intel-arc-a770-16gb").photos.length, 3);
  assert.equal(card("nvidia-geforce-rtx-3080-12gb").photos, undefined);
});
