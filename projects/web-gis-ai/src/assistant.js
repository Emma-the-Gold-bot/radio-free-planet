import { summarizeRecord } from './tools.js';

export function renderResults(results) {
  const root = document.getElementById('results');
  root.innerHTML = '';

  if (!results.length) {
    root.innerHTML = '<p class="small">No likely matches yet.</p>';
    return;
  }

  for (const item of results) {
    const div = document.createElement('div');
    div.className = 'result-item';
    div.innerHTML = `
      <strong>${item.record.title}</strong>
      <div class="small">score: ${item.score}</div>
      <div class="small">${summarizeRecord(item.record)}</div>
    `;
    root.appendChild(div);
  }
}
