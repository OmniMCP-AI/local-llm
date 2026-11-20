function positiveFact(value, pattern) {
  const match = pattern.exec(value ?? "");
  const number = Number(match?.[1]?.replaceAll(",", ""));
  return number > 0 && Number.isFinite(number) ? number : null;
}

export function cardRatings({ vendorSpec }) {
  const facts = vendorSpec?.facts ?? {};
  const capacity = positiveFact(
    facts["Memory configuration"] ?? facts["Dedicated memory (GB)"],
    /^(\d+(?:\.\d+)?)\s*(?:GB\s*(?:GDDR\dX?|HBM\dE?)?)?$/i,
  );
  return {
    capacity,
    bandwidth: positiveFact(facts["Memory bandwidth"] ?? facts["Memory bandwidth (GB/s)"],
      /^([\d,]+(?:\.\d+)?)\s*(?:GB\s*\/\s*(?:s|sec))?$/i),
    power: positiveFact(facts["Rated graphics power (W)"], /^([\d,]+(?:\.\d+)?)\s*W?$/i),
  };
}

export function cardPosition(card, peers, linkTo) {
  const current = cardRatings(card);
  const metric = current.capacity && !current.bandwidth && current.power ? "power" : "bandwidth";
  const points = peers.flatMap(row => {
    const point = cardRatings(row);
    return point.capacity && point[metric] ? [{
      id: row.id, name: row.name, capacity: point.capacity, value: point[metric],
      source: row.vendorSpec.source, href: linkTo(row.id),
    }] : [];
  });
  return {
    label: metric === "power" ? "Rated graphics power (W)" : "Rated memory bandwidth (GB/s)",
    points, selected: points.find(point => point.id === card.id),
  };
}
