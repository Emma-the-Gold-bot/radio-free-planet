# web-gis-ai

Lean starter scaffold for an open web GIS assistant with client-side schema embeddings.

## Goal
Build a minimal web GIS app that:
- shows a map with free/open basemaps
- loads domain layers
- extracts schema from the active map
- creates client-side embeddings for layers and fields
- semantically matches user questions to relevant map context
- routes to deterministic tools
- optionally sends narrowed context to an LLM later

## Stack
- Vanilla JS (ES modules)
- MapLibre GL JS
- Web Workers
- IndexedDB
- Optional embedding model in-browser (future)

## Structure
- `index.html` — app shell
- `styles.css` — minimal styling
- `src/main.js` — bootstrap
- `src/map.js` — map setup and layer control
- `src/schema.js` — schema extraction/normalization
- `src/assistant.js` — assistant UI logic
- `src/tools.js` — deterministic map tools
- `src/vector-store.js` — local vector storage/search
- `src/workers/retrieval-worker.js` — background retrieval worker
- `data/layers.json` — sample layer metadata

## Notes
See:
- `arcgis-agentic-web-mapping-notes.md`
- `open-source-agentic-web-mapping-spec.md`
