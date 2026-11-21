function positiveFact(value, pattern) {
  const match = pattern.exec(value ?? "");
  const number = Number(match?.[1]?.replaceAll(",", ""));
  return number > 0 && Number.isFinite(number) ? number : null;
}

export function cardRatings({ vendorSpec }) {
  const facts = vendorSpec?.scope === "Multiple manufacturer configurations" ? {} : vendorSpec?.facts ?? {};
  const capacity = positiveFact(
    facts["Memory configuration"] ?? facts["Dedicated memory (GB)"],
    /^(\d+(?:\.\d+)?)\s*(?:GB\s*(?:GDDR\dX?|HBM\dE?)?)?(?: with ECC)?$/i,
  );
  const rawBandwidth = facts["Memory bandwidth"] ?? facts["Memory bandwidth (GB/s)"];
  const bandwidth = positiveFact(rawBandwidth, /^(?:up to )?([\d,]+(?:\.\d+)?)\s*(?:GB\s*\/\s*(?:s|sec))?$/i);
  const terabytes = positiveFact(rawBandwidth, /^(?:up to )?([\d,]+(?:\.\d+)?)\s*TB\s*\/\s*(?:s|sec)$/i);
  return {
    capacity,
    bandwidth: bandwidth ?? (terabytes && terabytes * 1000),
    power: positiveFact(facts["Rated graphics power (W)"], /^([\d,]+(?:\.\d+)?)\s*W?$/i),
  };
}

export const memoryAxis = { label: "Nominal GPU memory", unit: "GB" };
export const bandwidthAxis = { label: "Rated memory bandwidth", unit: "GB/s" };
export const speedAxis = { label: "Measured decode speed", unit: "tok/s" };

export function cardPosition(card, peers, linkTo) {
  const rated = peers.map(row => {
    const { capacity, bandwidth } = cardRatings(row);
    return {
      id: row.id, name: row.name,
      short: row.name.replace(/^(NVIDIA (?:GeForce |Tesla )?|AMD (?:Radeon |Instinct )?|Intel )/, ""),
      capacity, bandwidth, source: row.vendorSpec?.source,
      bandwidthSource: row.vendorSpec?.bandwidthSource ?? row.vendorSpec?.source, href: linkTo(row.id),
    };
  });
  const points = rated.filter(({ capacity, bandwidth }) => capacity && bandwidth)
    .map(point => ({ ...point, x: point.capacity, y: point.bandwidth }));
  const capacityPoints = rated.filter(({ capacity }) => capacity).sort((a, b) => b.capacity - a.capacity)
    .map(point => ({ ...point, x: point.id, y: point.capacity, xText: point.name }));
  return { id: card.id, name: card.name, points, capacityPoints };
}
