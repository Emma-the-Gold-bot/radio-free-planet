importScripts();

let records = [];

function scoreQuery(query, record) {
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

self.onmessage = (event) => {
  const { type, payload } = event.data;

  if (type === 'init') {
    records = payload.records || [];
    self.postMessage({ type: 'ready', payload: { count: records.length } });
    return;
  }

  if (type === 'search') {
    const results = records
      .map((record) => ({ record, score: scoreQuery(payload.query, record) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);

    self.postMessage({ type: 'results', payload: { results } });
  }
};
