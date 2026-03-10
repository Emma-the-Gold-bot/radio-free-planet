import { createMap } from './map.js';
import { loadSchema } from './schema.js';
import { renderResults } from './assistant.js';

createMap();

const worker = new Worker('./src/workers/retrieval-worker.js');
const askButton = document.getElementById('askButton');
const queryInput = document.getElementById('queryInput');

worker.onmessage = (event) => {
  const { type, payload } = event.data;
  if (type === 'ready') {
    console.log(`Worker ready with ${payload.count} records`);
  }
  if (type === 'results') {
    renderResults(payload.results);
  }
};

const schema = await loadSchema();
worker.postMessage({ type: 'init', payload: { records: schema } });

askButton.addEventListener('click', () => {
  const query = queryInput.value.trim();
  if (!query) return;
  worker.postMessage({ type: 'search', payload: { query } });
});
