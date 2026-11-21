// Live listing references only. Never feed these objects into the static catalog gallery.
const day = 24 * 60 * 60 * 1000;
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const instant = value => {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(value)) return NaN;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && new Date(parsed).toISOString().slice(0, 19) === value.slice(0, 19) ? parsed : NaN;
};

function url(value, hosts = null) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:' && !parsed.username && !parsed.password && !parsed.port && (!hosts || hosts.includes(parsed.hostname)) ? parsed : null;
  } catch { return null; }
}

/** Project a reviewed provider response into a short-lived listing view, or fail closed.
 * This does not fetch, cache, render, or grant permission to use any content. */
export function listingPhoto(row, at = new Date().toISOString()) {
  if (!row || !['amazon', 'ebay'].includes(row.provider)) return null;
  const amazon = row.provider === 'amazon';
  const listing = url(row.listingUrl, amazon ? ['www.amazon.com', 'amazon.com'] : ['www.ebay.com', 'ebay.com']);
  const image = url(row.imageUrl, amazon ? ['m.media-amazon.com', 'images-na.ssl-images-amazon.com'] : ['i.ebayimg.com']);
  const itemValid = amazon ? /^[A-Z0-9]{10}$/.test(row.itemId ?? '') && /^[A-Z0-9]{10}$/.test(row.variantId ?? '') &&
    listing?.pathname === `/dp/${row.variantId}`
    : /^\d{9,15}$/.test(row.itemId ?? '') && listing?.pathname === `/itm/${row.itemId}` &&
      (row.variantId === 'single' ? !listing.searchParams.has('var') :
        /^\d+$/.test(row.variantId ?? '') && listing.searchParams.getAll('var').length === 1 && listing.searchParams.get('var') === row.variantId);
  const fetched = instant(row.fetchedAt), expiry = instant(row.expiresAt), now = instant(at);
  if (!listing || !image || !itemValid || !nonempty(row.variantId) || row.variantId !== row.reviewedVariantId ||
      !nonempty(row.catalogId) || !nonempty(row.partNumber) || row.partNumber !== row.reviewedPartNumber ||
      !url(row.matchEvidence) || !url(row.imageEvidence) ||
      !['seller-specimen', 'product-imagery'].includes(row.imageKind) || row.approvedProviderAccess !== true ||
      row.status !== 'active' || row.public !== true || !Number.isFinite(now) || !Number.isFinite(fetched) ||
      !Number.isFinite(expiry) || fetched > now || expiry <= now || expiry <= fetched || expiry - fetched > day) return null;
  return { provider: row.provider, listingUrl: listing.href, imageUrl: image.href, catalogId: row.catalogId,
    partNumber: row.partNumber, imageKind: row.imageKind, fetchedAt: row.fetchedAt, expiresAt: row.expiresAt };
}
