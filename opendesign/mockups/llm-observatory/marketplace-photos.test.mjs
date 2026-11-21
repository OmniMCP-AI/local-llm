import test from 'node:test';
import assert from 'node:assert/strict';
import { listingPhoto } from './marketplace-photos.mjs';
import { readHardwareCatalog } from './catalog-hardware-build.mjs';
import { hardwareCard, renderCard } from './catalog-card.mjs';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const now = '2026-11-22T12:00:00Z';
const ebay = {
  provider: 'ebay', itemId: '137016414155', variantId: 'v1',
  listingUrl: 'https://www.ebay.com/itm/137016414155', imageUrl: 'https://i.ebayimg.com/images/g/example.jpg',
  catalogId: 'asus-dual-rtx5060ti-16g', partNumber: 'DUAL-RTX5060TI-16G',
  reviewedPartNumber: 'DUAL-RTX5060TI-16G', reviewedVariantId: 'v1',
  matchEvidence: 'https://example.org/verified-board', imageKind: 'seller-specimen',
  imageEvidence: 'https://example.org/original-photo',
  fetchedAt: '2026-11-22T11:00:00Z', expiresAt: '2026-11-22T13:00:00Z',
  status: 'active', public: true, approvedProviderAccess: true,
};

test('exact approved live listing is linked to the listing and labeled', () => {
  assert.deepEqual(listingPhoto(ebay, now), {
    provider: 'ebay', listingUrl: ebay.listingUrl, imageUrl: ebay.imageUrl,
    catalogId: ebay.catalogId, partNumber: ebay.partNumber, imageKind: 'seller-specimen',
    fetchedAt: ebay.fetchedAt, expiresAt: ebay.expiresAt,
  });
});

test('ambiguous variants and missing photo classification cannot appear as exact live views', () => {
  for (const row of [
    { ...ebay, reviewedPartNumber: 'DUAL-RTX5060TI-O16G' },
    { ...ebay, reviewedVariantId: null },
    { ...ebay, matchEvidence: null },
    { ...ebay, imageKind: 'unknown' },
    { ...ebay, imageEvidence: null },
    { ...ebay, matchEvidence: 'not a URL' },
  ]) assert.equal(listingPhoto(row, now), null);
});

test('expired, future, withdrawn, nonpublic and unapproved references disappear', () => {
  for (const row of [
    { ...ebay, expiresAt: now }, { ...ebay, fetchedAt: '2026-11-22T12:01:00Z' },
    { ...ebay, status: 'ended' }, { ...ebay, public: false },
    { ...ebay, approvedProviderAccess: false },
  ]) assert.equal(listingPhoto(row, now), null);
});

test('Amazon exact variation enforces 24-hour link expiry', () => {
  const amazon = { ...ebay, provider: 'amazon', itemId: 'B012345678', variantId: 'B012345679',
    reviewedVariantId: 'B012345679', listingUrl: 'https://www.amazon.com/dp/B012345679',
    imageUrl: 'https://m.media-amazon.com/images/I/example.jpg', imageKind: 'product-imagery',
    fetchedAt: '2026-11-22T00:00:00Z', expiresAt: '2026-11-23T00:00:00Z' };
  assert.equal(listingPhoto(amazon, now)?.imageKind, 'product-imagery');
  assert.equal(listingPhoto({ ...amazon, expiresAt: '2026-11-23T00:00:01Z' }, now), null);
});

test('listing identities and hostnames must agree', () => {
  for (const row of [
    { ...ebay, listingUrl: 'https://www.ebay.com/itm/123456789012' },
    { ...ebay, imageUrl: 'https://example.org/image.jpg' },
    { ...ebay, listingUrl: 'https://www.ebay.com.example.org/itm/137016414155' },
  ]) assert.equal(listingPhoto(row, now), null);
});


test('static HTML and Markdown do not export a live provider reference', async () => {
  const { catalog } = await readHardwareCatalog(dirname(fileURLToPath(import.meta.url)));
  const row = { ...catalog.cards[0], marketplacePhotos: [listingPhoto(ebay, now)] };
  const release = 'v1-1234567890abcdef';
  for (const markdown of [false, true]) {
    const page = renderCard(hardwareCard(row, release, 'cards'), {
      release, pathname: `/catalog/${release}/cards/${row.id}.${markdown ? 'md' : 'html'}`, markdown,
    });
    assert.ok(!page.includes(ebay.imageUrl));
    assert.ok(!page.includes(ebay.listingUrl));
  }
});
