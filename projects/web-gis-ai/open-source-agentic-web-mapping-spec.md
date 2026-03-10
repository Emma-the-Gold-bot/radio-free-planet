# Open-source alternative spec: semantic web-map assistant for environmental / watershed platforms

## Goal
Design an open-source alternative to the ArcGIS JavaScript SDK semantic web-map assistant pattern.

This alternative should:
- support web-based map applications,
- allow natural-language interaction with map/layer schemas,
- use semantic search over layer/field metadata,
- narrow context before invoking an LLM,
- and remain adaptable to environmental / watershed monitoring platforms.

---

## Core design principle
The open-source system should copy the **pattern**, not the proprietary stack:

1. represent map schema in structured form,
2. create embeddings for meaningful schema elements,
3. run semantic retrieval against the schema,
4. pass only relevant context to the LLM or workflow engine,
5. constrain actions through explicit tools/workflows.

The key idea is not "chat with a map."
It is:

**semantic retrieval over geospatial schema to improve map-aware assistant behavior.**

---

## Recommended open-source stack

### Front end
- **MapLibre GL JS** for 2D web mapping
- optional **CesiumJS** for 3D geospatial visualization if terrain / 3D scenes matter
- React / Svelte / Vue for application shell

### Data / services
- **GeoServer** or **pg_tileserv** / **tegola** for serving spatial layers
- **PostGIS** as core spatial database
- optional **STAC**-style catalog if imagery / raster assets matter

### Metadata / schema layer
A service that exposes:
- layer IDs
- titles
- descriptions
- field names
- aliases
- domains / coded values
- tags
- optional summaries

This can live as:
- Postgres tables,
- JSON schema documents,
- or service-derived metadata.

### Embedding generation
Options:
- **sentence-transformers** models server-side,
- or **Transformers.js** / ONNX models client-side in web workers,
- depending on privacy, scale, and performance constraints.

Recommended initial approach:
- precompute embeddings server-side for stability,
- allow optional client-side query embedding in-browser.

### Vector storage / retrieval
Options:
- **pgvector** in Postgres
- **Qdrant**
- **Weaviate**
- **FAISS** if fully local / server-contained

Recommended initial approach:
- **Postgres + pgvector** for simplicity and alignment with PostGIS.

### LLM / orchestration layer
Open-source-friendly choices:
- **Ollama** for local inference where feasible
- vLLM / llama.cpp / open-weight model serving if self-hosted
- optional external API if not avoiding hosted models

Orchestration:
- lightweight custom service,
- or LangChain / LlamaIndex if used carefully,
- but avoid framework bloat unless it clearly helps.

### Tool / workflow layer
The assistant should not directly do everything through free-form text.
It should call explicit tools such as:
- list relevant layers,
- inspect layer schema,
- filter features,
- zoom to matching extent,
- summarize selected records,
- run simple environmental workflows,
- pull recent sensor data,
- compare restoration monitoring dates.

---

## Conceptual architecture

### 1. Map schema ingestion
Collect and normalize metadata for:
- map layers,
- fields,
- feature services,
- dashboards,
- sensor layers,
- restoration sites,
- monitoring stations.

### 2. Embedding pipeline
Create embeddings for:
- layer titles,
- field names,
- aliases,
- descriptions,
- tags,
- optional examples of supported questions.

### 3. Semantic retrieval
When a user asks something, the system:
- embeds the query,
- runs vector similarity search,
- returns top relevant schema elements,
- optionally combines with keyword search,
- optionally conditions on current map extent / layer visibility / selection.

### 4. Context assembly
Build a compact context payload containing only:
- relevant layers,
- relevant fields,
- current map/app state,
- allowed workflows.

### 5. Assistant / tool execution
The assistant then either:
- answers with retrieved information,
- or invokes structured tools.

This is safer than letting the LLM infer arbitrary map operations from the full schema.

---

## Environmental / watershed adaptation
This pattern is especially useful for watershed and habitat platforms because those systems often have:
- many thematic layers,
- technical field names,
- monitoring stations,
- land use layers,
- restoration sites,
- drone products,
- sensor data,
- and users who do not know the schema.

Example questions such a system could support:
- "Show me reaches with recent restoration work and high erosion risk."
- "Which stations in this watershed have temperature data from the last 30 days?"
- "What layers describe riparian vegetation condition?"
- "Where are restoration sites downstream of agricultural land use?"

---

## Minimal viable product

### MVP scope
Build a web map assistant that can:
1. read map schema metadata,
2. semantically search layers and fields,
3. identify relevant layers from user questions,
4. explain why those layers are relevant,
5. execute a small set of deterministic actions.

### First deterministic actions
- zoom to relevant layer extent
- toggle relevant layers
- summarize field schema
- list matching monitoring stations
- filter features by simple criteria
- open site detail views

### First domain target
A watershed or restoration monitoring app with:
- creek reaches,
- restoration sites,
- sensor stations,
- land use layers,
- riparian condition layers.

---

## Why this is better than a naive map chatbot
A naive map chatbot fails because it:
- sees too much schema,
- guesses at relevance,
- hallucinates fields/layers,
- and cannot safely execute actions.

This design is better because it:
- narrows context semantically,
- constrains actions through known tools,
- stays closer to map/application reality,
- and can remain largely open-source.

---

## Honest limitations
- good embeddings do not fix bad metadata,
- vector retrieval does not guarantee correct geospatial reasoning,
- environmental domain questions still need structured tools and rules,
- and open-source assembly means more plumbing work than a polished proprietary SDK.

But it avoids total dependency on proprietary assistant frameworks and fits better with a values-aligned, extensible public-interest platform.

---

## Best next implementation questions
- Should embeddings be server-side, client-side, or hybrid?
- Is 2D enough at first, or is CesiumJS worth the complexity?
- What exact schema objects need embeddings?
- What deterministic tools are most valuable for a watershed app?
- What metadata must be improved to make semantic retrieval useful?
