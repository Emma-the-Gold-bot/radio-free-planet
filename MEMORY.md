# MEMORY.md — Long-Term Context

## Major Projects

### AquaGraph (active — started 2026-05-13, Phase 2 in progress)
- California Water Accountability Network — transparency tool for groundwater governance
- PoC target: "Show me every board member who owns land in the district they govern"
- Focus: Vina subbasin (Butte County, CA) — Vina GSA, TWD, AGUBC
- Architecture: Scrapers → PostgreSQL + AGE → Entity resolution → Conflict detection → Frontend
- Phase 0 (Weeks 1-3): Validated entity resolution with Gemini 2.5 Flash (100% accuracy, $0.005/resolution)
- Phase 1 COMPLETE (Weeks 4-8): 60 entities, 44 relationships, PoC frontend
- Phase 2 Data Quality Audit: merged 3 duplicates, wired 24 relationships, orphans 31→7
- **Phase 2 Milestone (2026-05-27): self_interest_vote LIVE** — 155 CRITICAL conflicts
  - Butte County GDB (July 2020): 99,478 parcels, 256 owns_parcel relationships
  - Source: USB drive at `/media/emma/USB31FD/CA_BUTTE_20200713.gdb`
  - Key: Richard McGowan (AGUBC President) owns 15 parcels, Samantha Lewis (SHAC) owns 22
  - Headline PoC query fully functional
  - **Phase 2a Complete (2026-05-29):** TWD investigation final report at `data/TWD_INVESTIGATION_FINAL.md`
- Key model: Gemini 2.5 Flash for entity resolution
- Current state: 98,490 entities (136 persons, 299 organizations, 98,055 parcels), 1,579 relationships, 111 conflicts (104 self_interest_vote, 5 dual_role, 1 revolving_door, 1 formation_influence), 96,934 parcel geometries
- UI: 7.5/10 polish (dark theme, badges 7.5, graph viz 8, spacing 7, typography 8)
- Backup: `aquagraph-poc-20260528/` on flash drive (19MB, restore instructions in BACKUP_README.md)
- **Phase 2a TWD Investigation (2026-05-28):**
  - TWD entity ingested: 377 owners, 3,136 parcels, 820+129+114+216 relationships
  - Farmland Reserve Inc (LDS Church): 11,432 acres, 11.5% vote power, largest landowner
  - Nuvista LP + Las Nogaleras LP: Delaware LPs, same-day formation (7/9/2019), same address, same CSC agent, GP = NuVista GP LLC (also Delaware). Combined 3,351 acres.
  - Land transfer: Gilbert family trust → Nuvista LP, 11/18/2019 (3 days after CA registration)
  - Provost & Pritchard (Clovis/Fresno): San Joaquin Valley water consulting firm, prepared Vina GSP, administered TWD election. Also works for Westlands Water District. Founder started career at Westlands. Specializes in "water transfers, groundwater banking."
  - 2011 GCID study (funded by DWR/USBR): Tuscan Aquifer should be "exercised aggressively" for statewide water transfer markets. Envisions recharge in Butte County, extraction in Glenn/Colusa Counties. $300M federal/state funding.
  - Kern Water Bank model: public aquifer → private bank through Monterey Amendments (1994). Resnick controls 57% through Westside Mutual shell corp.
  - No direct Resnick ownership in TWD — connection is institutional (P&P bridges both regions)
  - Full investigation report: `data/TWD_INVESTIGATION_FINAL.md`
- Location: `projects/aqua-graph/`

### VIN Lookup PWA (active — started & completed 2026-06-19)
- Mobile-first PWA for VIN lookup — enter VIN, get vehicle specs, recalls, safety ratings, fuel economy
- Portfolio piece for Pilgrim's boss, open source, no backend
- **Tech:** Vanilla JS + Vite, PWA (Workbox), Vitest, IndexedDB
- **Location:** `projects/vin-pwa/app/`
- **Built in one session:** 10 units, ~50 tasks, dispatched via fusion sub-agents
- **Tests:** 92 passing (vin-validator, store, idb, dom, debounce, api-tracker, vin-decoder)
- **Data sources:**
  - NHTSA vPIC (`https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json`) — VIN decode, unlimited, no key
  - NHTSA Recalls (`https://api.nhtsa.gov/recalls/recallsByVehicle`) — unlimited, no key
  - NHTSA Safety (`https://api.nhtsa.gov/SafetyRatings`) — two-step lookup, many vehicles return null
  - EPA FuelEconomy (`https://www.fueleconomy.gov/ws/rest`) — two-step XML lookup, unlimited, no key
  - Vehicle-Finder (500 req/mo, needs key) — maintenance, TSBs, repair costs
  - YouTube Data API (~100/day, needs key) — repair videos
  - WMI database (bundled 12,297 entries) — manufacturer/country from VIN prefix
  - OBD-II codes (bundled 54 codes) — diagnostic trouble code lookup
- **Key architecture decisions:**
  - No framework (vanilla JS), static deploy (Vercel/Netlify), client-side only
  - IndexedDB over localStorage (5-10MB limit vs unlimited)
  - NHTSA vPIC as primary decoder (corgi offline noted as future enhancement)
  - `{ element, destroy }` component contract prevents memory leaks
  - Pub/sub store with `searchStatus` enum: idle/loading/success/not_found/error
  - Hash-based routing with deep linking: `#/`, `#/about`, `#/lookup/:vin`
- **API gotchas discovered:**
  - `DecodeVinValues` returns flat keys, `DecodeVin` returns Variable/Value pairs
  - `api.nhtsa.dot.gov` doesn't resolve — correct domain is `api.nhtsa.gov`
  - Recalls API returns capitalized field names (`NHTSACampaignNumber`, `Component`, etc.)
  - Safety ratings need two-step lookup (get vehicle ID, then fetch ratings)
  - EPA returns XML, needs DOMParser to parse
  - IndexedDB version must be >= existing DB version or you get "requested version less than existing" error
- **Pilgrim's email:** matt_brush@zoho.com
- **Models used:** DeepSeek V4 Pro (primary coder), Gemini 3 Flash (judge/review/design fixes)
- **Kimi K2.6 removed from config** — consistently unreliable on coding tasks (dumps file listings instead of creating files)
- **Deployment configs:** `vercel.json` + `netlify.toml` created
- **Zip shared:** https://files.catbox.moe/coux4r.zip (502KB, excludes node_modules/dist)

### Sacramento Valley Water Transfers Research (active — started 2026-06-15)
- Deep dive into actual board actions (resolutions, votes, approved contracts) for Sacramento Valley water sellers
- Key document set: SLDMWA CEQA addendum + USBR Long-Term Transfers NEPA EA — same project, dual compliance
- SLDMWA site: sldmwa.org — found Long-Term Water Transfers EIS-EIR (2020) + 2026-2027 North-South Water Transfers EA/IS (July 2025)
- EA/IS: joint Reclamation/SLDMWA, 32+ sellers, 467K AF pool, 250K AF/yr cap, references 2024 Biological Opinions
- Contact: Pablo Arroyave (pablo.arroyave@sldmwa.org), Exec Director: Federico Barajas
- **Key board actions found:**
  - SSJID/OID: Resolutions 26-09-W & 26-10-W (Mar 2026) — 50K AF to SLDMWA/DWR, 5-year, 5-0 vote
  - PCWA: Amendment 4 to EBMUD MOU (Nov 2024), Resolution 24-24 Warren Act (Dec 2024), WF2050+PSA (Jan 2026)
  - MID: 6,000 AF to SLWD approved Dec 2024 ($200/AF, CVP exchange)
  - EID: CEQA Neg Dec for Five-Year Conserved Water Transfer (Jun 2024) + Reservoir Re-operation (Jul 2024)
  - RD 108: Water Reduction Program Agreement with SRSC/USBR (Dec 2024)
- "Six entities / 75,520 AF" reference from Pilgrim — not yet located in documents
- Pilgrim's research focus: actual approved transfers, not possibilities; board agendas/minutes are ground truth
- Entity folders at `projects/water-transfers/entities/` (33 directories with PROFILE.md, sources.md, meetings/)
- **2026-06-20: Four Focus Entity Deep Dive** — RD 108, Sutter MWC, RD 1004, Natomas Central MWC
  - All four SLDMWA seller pool Sacramento River area entities, all SRSC members
  - **RD 108** (extraction: 839 lines, 38.5KB from 31 agendas): 5 transfer partners staged (Sutter Mutual, Roberts Ditch, Dunnigan WD, Colusa County WD, Fair Ranch/DWR). Water transfer revenue $440K→$535K/yr. Sites Reservoir 500 AF investment, $2.2M remaining burden. DPP: 20-year agreement, up to 50% supply reduction in severe drought years, ~55,000 AF deficit. No minutes posted (agendas only). Lewis Bair GM.
  - **Sutter MWC** (extraction: 805 lines, 56KB from 44 PDFs): SLDMWA Letter of Intent + explicit SLDMWA agenda item (Feb-Apr 2026). DPP payment $25.7M (held in CDs, resiliency account, $3.8M tax reserve, $10.9M deferred). ITP lawsuit dismissed (Jan 2025), 90-5 SWRCB settled (Mar 2026), SWC CEQA settled (Mar 2026). 100% SRSC supply 2025+2026. RD 108 supplemental: 10K AF @ $53/AF. Water rate $21/AF. SRSC engaged Bureau Aug 2025 over aggressive Shasta releases. Roger Cornwell GM, Bill Henle on board.
  - **RD 1004** (extraction: 186 lines, 8KB from 7 meetings): Website found at reclamationdistrict1004.us. SLDMWA timeline: Feb 2026 (~4,500 AF groundwater transfer request), Mar 2026 (SLDMWA named, state 15% allocation, Glenn County conversation initiated), Apr 2026 (process started). Provost & Pritchard fee study ongoing. Thad Bettner presented at Annual Landowner Meeting. Dustin Cooper (Minasian) counsel. Board: Hans Herkert (Chair). Terry Bressler GM.
  - **Natomas Central MWC** (extraction: 30KB from 13 PDFs): 2026 annual shareholder presentations sanitized — no mention of transfers, SLDMWA, HCP, SWRCB orders. Conservancy election strategy (4,195 shares, contested 7-seat election). Bylaws "return flows belong to company" clause. Troy Givans dual role (NCMWC director + Sacramento County voter). 2026 water toll $10.35/AF. NRDC v. Haaland (9th Cir. 2024) dismissal cited in Downey Brand update. Board: Tom Ramos (President).
  - All extractions at `entities/{name}/meetings/2025-2026_EXTRACTION.md` or `2026_EXTRACTION.md`
  - **Cross-cutting pattern:** All four entities actively engaged with SLDMWA transfers in 2026, all SRSC members, all in DPP framework, all with Provost & Pritchard or Minasian Law connections

### Knowledge Loom (active — started 2026-04-05, validated 2026-04-09)
- Research archaeology tool — finds suppressed/abandoned knowledge in scientific literature
- First domain: Medicine (H. pylori / peptic ulcer ground truth case)
- Architecture: PubMed + OpenAlex ingestion → LLM extraction → PostgreSQL graph → discovery engine → verified connections
- 4,140 papers, 35K citations, 16,077 constraints, 7,999 named methods, 549 full texts (13%), 20 domains
- Domains: Medicine (1,161), Biochemistry (537), Computer Science (527), Engineering (516), Neuroscience (273), Materials Science (217), Immunology (149), Environmental Science (135)
- Named methods extraction: 7,090 named techniques across 2,798 papers (avg 2.6/paper)
- Constraint graveyard: 41.4% cross-domain (coarse domains), 58.2% same-domain, 0.4% open
- 72 LLM-verified named-method transfers across 13 domains (strict verification)
- 25 abandoned findings identified in constraint graveyard suppression pass
- Solution query matching: LLM reformulates constraints as positive queries, then matches against methods
- Coarse domain taxonomy: 8 fields (Life Sciences, Engineering, CS & Math, etc.)
- Validated: constraint matching (28 confirmed YES)
- Validated: cross-domain transfer (108 verified, named methods: Bayesian modeling, ROC analysis, propensity scoring, decellularization, microfluidic bioprinting)
- Validated: suppression detection — 6/6 in-corpus positive cases scored, 2/2 negative controls correctly NOT flagged, 100% recall with enhanced 7-marker scanner
- Key finding: `author_retreat` fires on 100% of suppression cases — most reliable marker
- Key finding: Gemma 4 (97% pass) vs Gemini 2.5 Flash (28% pass) — named-method verification is the differentiator
- Built: `loom_recommend.py` — CLI tool for cross-domain method recommendation (DOI → constraints → methods)
- Built: `enhanced_suppression_scan.py` — 7-marker scanner with LLM citation stance + retraction/fraud gate
- Built: `negative_citation_shift_v3.py` — OpenAlex + Gemini citation stance classifier
- Cross-domain transfer needs full text (named methods > generic constraints)
- Cost: ~$5-10 total (free data sources, cheap extraction, quality verification)
- Validation set: 8 positive cases, 2 negative controls in `validation/suppression_cases.json`
- Full assessment: `projects/knowledge-loom/ASSESSMENT.md`
- Location: `projects/knowledge-loom/`

### Knowledge Loom — Key Insight: Extraction Quality is Everything
- The bottleneck isn't matching algorithms — it's method extraction quality
- Old prompt gave generic "The paper reviews various approaches to..." — useless for matching
- New prompt forces named techniques: "CNN-LSTM hybrid model", "AFEM", "LC-MS/MS metabolomics"
- Named methods as separate matching candidates dramatically improves match relevance
- Verification prompt must reject reviews/surveys/meta-analyses — they're noise, not signal
- Cross-domain classification needs `method_origin_domain` (not just paper domain) to detect true transfers
- ~1,088 existing extractions need re-extraction (~$3-5) to populate new `methods` JSONB column

### Phase 2a (2026-05-28): TWD Entity Research — Delaware Shell LPs
- Nuvista LP (formed DE 7/9/2019, registered CA 11/15/2019) — CSC agent
- Las Nogaleras LP (same-day formation, same address, same CSC agent)
- Both at 10695 Decker Ave, Los Molinos, CA 96055
- NuVista GP LLC (Delaware LLC) is general partner — hides actual ownership
- Cam Land Co LP: formed CA 9/5/2008, different entity, agent William C Crain
- Gilbert family trust → Nuvista LP land transfer (3 days after CA registration)
- Butte County GDB shows 1 Nuvista parcel (APN 039-260-068, 30 acres, Nov 2019)
- Most Nuvista/Las Nogaleras parcels acquired after July 2020 (GDB snapshot date)

### Phase 2a (2026-05-29): P&P and Westlands Connection
- Provost & Pritchard (Clovis/Fresno): water consulting firm specializing in "water transfers, groundwater banking"
- P&P works for both TWD (administered election, prepared Vina GSP) and Westlands Water District
- P&P founder began career at Westlands Water District
- P&P also does Friant-Kern Pipeline (Kern County) and Fresno Irrigation District projects
- 2011 GCID study (DWR/USBR funded): Tuscan Aquifer should be "exercised aggressively" for statewide water transfer markets
- Envisions recharge in Butte County, extraction in Glenn/Colusa Counties
- Kern Water Bank model: Resnick controls 57% through Westside Mutual shell corp
- No direct Resnick/Wonderful Company ownership in TWD — connection is institutional, not ownership-based
- Final investigation report: `data/TWD_INVESTIGATION_FINAL.md`

### Phase 2a (2026-06-04): Cal-Access Financial Ties Investigation
- Puppeteer Stealth bypasses Incapsula bot protection on Cal-Access
- Resnick/Wonderful Company: LOBBYIST EMPLOYER (Entity 1254781, ACTIVE)
- Resnick paid $147,500 to California Strategies & Advocacy during TWD formation (2021-2022)
- California Strategies & Advocacy lobbyists: Rusty Areias (Ag Committee chair), Kristin Olsen-Cate (Water Committee vice chair, helped pass 2014 Water Bond)
- Provost & Pritchard: MAJOR DONOR (Entity 499832)
- Farmland Reserve: NOT in Cal-Access (no lobbying, no contributions)
- Zero direct campaign contributions found for all entities
- Lobbying firm transition: California Strategies & Advocacy → Capitol Advisors Group (July 2022, after TWD approval)
- SEE MEMO entries in 2021-2022 lobbying session remain inaccessible (ASP.NET postback limitation)
- Graph updated: added Resnick, Wonderful Company, Roll International, California Strategies & Advocacy, Capitol Advisors Group, Westlands Water District
- P&P wired: consulted_for TWD, Vina GSA, Westlands Water District

### Web-native Geoprocessing Suite (active — started 2026-06-14)
- Browser-native spatial workbench: MapLibre + DuckDB-WASM + discovery engine
- **2026-06-24 night: 10 commits shipped** (`a1fde2f` → `4b53bc6`, all pushed to origin)
- **Current state:** Map-first shell working (5 sidebar icons, command bar, chain visualization), per-artifact layer controls (visibility/opacity/z-order) with real tests, mobile-responsive (bottom tab bar at ≤768px), NL pipeline (artifact picker, disabled Execute), actionable empty states. 107/107 unit tests + 6 browser smoke checks passing.
- **Slice 1.5+1.6 lesson:** Replacing emoji icons with SVG was real. Adding mobile CSS without restructuring layout was theater — looked like progress, wasn't. Real mobile fix (Slice 4.5) required bottom-tab-bar architecture change.
- **Dispatch redesign (2026-06-24):** Fusion (parallel writers) → Complementary (implementer + tester with disjoint file scopes). Verifier role removed (Judge subsumes). MiniMax M3 flaky in coder role; reverted to MiMo v2.5 Pro.
- **Architecture:** Schema/registry/operation layer (`src/lib/operations/**`) untouched since Slice 1. View-layer changes only. Engine work (NL resolver, plan builder/executor, layer-controls) is real and tested.
- **Remaining work (in priority order):** Mobile UX polish (center card → bottom sheet, bottom density) → Discover panel wiring (still stub) → Discovery prefixes (`@osm/@ckan/@stac`) → Undo/redo → Export menu + keyboard shortcuts.
- Location: `projects/web-native-geoprocessing-suite/`
- Full arc: `projects/web-native-geoprocessing-suite/DEVELOPMENT.md` (Slices 1-4.5 documented with commits, dispatch patterns, decision log)

## Pilgrim Preferences
- Prefers high standards over expedient progress
- Values clean architecture and honest claims
- Favors disciplined sequencing — tighten the seam, then add the next slice
- Willing to invest time in validation before scaling
- Interested in systems that surface suppressed/forgotten knowledge

### Knowledge Loom — GIS Expansion (2026-04-10)
- 2,225 GIS papers ingested from OpenAlex (searched: GIS, kriging, remote sensing, spatial analysis, LiDAR, geostatistics)
- Total corpus: 6,365 papers, 26,117+ constraints
- 1,393 GIS-related cross-domain transfers found
- Earth & Environment jumped from 46.8% → 64.9% cross-domain
- GIS methods transferring: Kriging (spatial interpolation), variogram modeling, statistical downscaling, raster GIS
- GIS is genuinely cross-domain: methods from Physical Sciences transfer to Life Sciences, Social Sciences, Earth & Environment, Engineering

### Knowledge Loom — Domain-Aware Matching (2026-04-10)
- Root cause identified: matching solution queries against constraint texts (not method descriptions)
- Fix: solution queries matched directly against method_desc column
- Template patterns + LLM fallback for query generation
- LLM verification with scale/context/transfer mechanism checks
- fNIRS test: shifted from satellite remote sensing (noise) to 3-D deconvolution, ICA, reconstruction algorithms (signal)
- Implementation: `direct_method_matching.py` (standalone), `loom_recommend.py` (integrated)
- Remaining limitation: embedding still finds semantic similarity; solution queries reduce but don't eliminate noise

### Knowledge Loom — Constraint Graveyard v3 (2026-04-10 evening)
- Integrated solution query matching into constraint graveyard pipeline
- `constraint_graveyard.py` rewritten: generate solution queries → embed → match against methods
- Heuristic solution query generation (30+ regex templates, no LLM needed at scale)
- Results: 28,989 constraints, 97.1% cross-domain solutions, only 5 open constraints
- 14,864 named-technique cross-domain transfers mapped
- Top flows: CS→Life Sciences, Life Sciences→Engineering, Physical Sciences→Life Sciences
- Named techniques crossing domains: Kriging, ICA, Egger's test, meta-regression, gene dropout imputation
- Output: `constraint_graveyard.json`, `domain_transfer_map.json`, `loom_dashboard.html`

## NHTSA & EPA Vehicle API Reference
- **VIN decode:** `https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json` — returns Variable/Value pairs (NOT DecodeVinValues which returns flat keys)
- **Recalls:** `https://api.nhtsa.gov/recalls/recallsByVehicle?make=X&model=Y&modelYear=Z` — returns `results[]` with capitalized keys (`NHTSACampaignNumber`, `Component`, `Consequence`, `Remedy`)
- **Safety (step 1):** `https://api.nhtsa.gov/SafetyRatings/modelyear/Y/make/M/model/MDL` — returns vehicle IDs
- **Safety (step 2):** `https://api.nhtsa.gov/SafetyRatings/vehicleid/{id}` — returns ratings (many vehicles return empty Results)
- **EPA menu:** `https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=Y&make=M&model=MDL` — XML, returns menuItem/value pairs
- **EPA vehicle:** `https://www.fueleconomy.gov/ws/rest/vehicle/{id}` — XML, returns city08/highway08/comb08/fuelType/annualFuelCost etc.
- **Domain notes:** `api.nhtsa.dot.gov` does NOT resolve — correct domain is `api.nhtsa.gov`. EPA has CORS `*` header. All APIs are free, unlimited, no key required.
