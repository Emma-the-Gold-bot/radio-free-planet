export function scoreQuery(query, record) {
  const haystack = [
    record.title,
    record.description,
    ...(record.fields || []),
    ...Object.values(record.aliases || {}),
    ...(record.tags || [])
  ].join(' ').toLowerCase();

  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  let score = 0;
  for (const term of terms) {
    if (haystack.includes(term)) score += 1;
  }
  return score;
}

export function rankRecords(query, records, limit = 5) {
  return records
    .map((record) => ({ record, score: scoreQuery(query, record) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
