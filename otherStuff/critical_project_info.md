# Master Critical Project Knowledge & Technical Domain Guide

This document serves as the authoritative technical reference and domain specification for the **SPONGE** (ceRNA interaction networks) and **SpongEffects** (ceRNA module biomarkers & tumor subtyping) platform across both the backend (`SPONGE-web-backend`) and frontend (`SPONGE-web-frontend`) codebases.

---

## 1. SpongEffects Runs & Best Model Selection

### Top-Accuracy Best Model (`get_best: bool = True`)
- **Multi-Run Architecture**: For every cancer dataset (e.g., `pancancer`, `brca`, `luad`, `coad`), SPONGE pre-computes multiple SpongEffects runs (`spongEffects_run_ID`) corresponding to different parameter combinations (`m_scor_threshold`, `p_adj_threshold`, `modules_cutoff`).
- **Random Forest Model Alignment (`models.RDS`)**: Pre-trained Random Forest models used for patient tumor classification and subtyping are trained on the **single top-accuracy SpongEffects run** per dataset.
- **Backend API Contract (`get_best` / `best_model_only`)**:
  - API endpoints (`getSpongEffectsGeneModules`, `getSpongEffectsTranscriptModules`) take `get_best: bool = True` (aliased in OpenAPI as `best_model_only: true`).
  - By default (`get_best=True`), requests without explicit run parameters return modules **exclusively from the single best model run** (`spongEffects_run_IDs[:1]`).
  - If a caller explicitly specifies `get_best=False`, the backend retrieves modules across all parameter runs for that disease.

### Center vs. Member Biological & UI Constraints
- **Module Structure**: A SpongEffects module consists of **one module center gene/transcript** and its associated **ceRNA module members**.
- **Center-Only Enrichment Scores**: Single-sample enrichment scoring (ssGSEA / GSVA) aggregates member gene expression into the module center. Therefore, **only module center nodes possess SpongEffects enrichment scores**. Member nodes participate in the interaction network but do not have standalone enrichment scores.
- **UI Modal Rules**: Gene and transcript detail modals (`GeneModalComponent`, `TranscriptModalComponent`) render SpongEffects enrichment score tabs/panels **exclusively for module center nodes**.

---

## 2. Network Construction & WebGL Rendering Rules

### Node Sizing & Visual Framing
- **Standardized Degree Sizing**: Module centers are graph anchors, but their visual node sizes must be computed standardly based on node degree:
  $$\text{size} = 5 + 15 \times \frac{\text{node\_degree}}{\text{maxNodeDegree}}$$
  Center nodes must **never** receive artificial size boosts or hardcoded minimum radii.
- **Center Identification**: Center status is indicated **exclusively by the green border frame** (`borderedCircle` for genes, `borderedSquare` for transcripts).
- **Clean Label Formatting**: Node labels in WebGL network views must display clean gene/transcript symbols without appending text suffixes like `(Member)` or `[Center]`.

### Induced Subgraph Construction
- **Module Network Selection**: Module networks display the center node(s) and their top $N$ highest-$m_{scor}$ interaction members.
- **Edge Complete Property**: Subgraphs return all valid database edges between any pair of nodes in the selected set (both center $\leftrightarrow$ member AND member $\leftrightarrow$ member edges).
- **⚠️ Caveat (see §9)**: not every spongEffects module member actually has a DB ceRNA edge to the center — the module-member set is broader than the sponge run's first-neighbours. So "member ⇒ center edge" does NOT hold against the `GeneInteraction` table.

---

## 3. Parameter Serialization, Database Safeguards & Caching

### Query Parameter Type Coercion
- **Flask/Connexion HTTP Strings**: HTTP query parameters (e.g. `spongEffects_gene_module_ID=1103`) arrive at backend controller functions as raw strings (`'1103'`).
- **SQLAlchemy `.in_()` Safeguard**: Passing raw strings to `.in_('1103')` raises an `ArgumentError`. Controllers (`get_gene_module_enrichment_score`, `get_transcript_module_enrichment_score`) must sanitize and coerce string, int, or list inputs into `list[int]`.

### MySQL `NaN` Protection
- **Numeric Field Handling**: Unset HTML `<input type="number">` fields in Angular emit `NaN`. Passing `NaN` to SQLAlchemy/MySQLdb causes a `ProgrammingError`.
- **Sanitization Protocol**:
  - Frontend services sanitize numeric parameters using `numOrUndefined` to convert `NaN` to `undefined`.
  - Backend controllers guard numeric inputs using `math.isnan()` checks.

### Cache Decorators
- **Internal Helper Memoization**: Functions invoked internally within Flask controllers (such as `get_spongEffects_run_ID`) must use `@cache.memoize()` rather than `@cache.cached(query_string=True)` to track native Python arguments rather than HTTP request objects.

---

## 4. Plotting & Distribution Visualization Modes

### Dual Layout Modes (`ClassificationPlotComponent` & `EnrichmentClassPlotComponent`)
- **Combined Mode (`isCombinedMode = true`)**:
  - Overlays all reference cancer class KDE distributions (and uploaded patient sample distributions) on a single shared plot with a horizontal legend.
- **Stacked Mode (`isCombinedMode = false`)**:
  - Displays vertically stacked independent subplots for each cancer type/subtype with individual title annotations.
- **Hidden-Tab Auto-Resizing**:
  - Plots initialized inside hidden tabs receive `offsetWidth = 0`. Plot components observe element visibility and call `Plotly.relayout(el, { autosize: true })` and `Plotly.Plots.resize(el)` upon becoming visible.

### Enrichment scores endpoint — use `average=true`, NOT `average=false`, for mean/variance
- `getSpongEffectsGeneModuleScores` / `…TranscriptModuleScores` (`get_gene_module_enrichment_score`) has three modes:
  - `average=false, cluster=false` → **every per-sample score**. For ~269 modules this is **~2.3 M rows / 462 MB / 27 s** (ORM load + `EnrichmentScoreGeneSchema(many=True).dump`). **Never** fetch this for many modules.
  - `average=true` → SQL `AVG` + `VARIANCE ... GROUP BY module` → **one row per module** (`score_value`=mean, `variance_score`=variance) → **~269 rows / 57 KB**. This is what the "Enrichment: Mean vs Variance" scatter needs (it previously used `average=false` and aggregated in JS — fixed to `average=true`).
  - `cluster=true` → per-sample + pandas pivot + scipy `linkage`/`dendrogram` (used by the enrichment heatmap; also heavy — keep the module set small).
- The route is cached (`@cache.cached(query_string=True)`) and the module-ID column is FK-indexed, so repeat identical calls are fast; the `average=true` cost (~15 s aggregating 2.3 M rows) is a **cache-miss** cost. If "Add remaining" (all modules) needs to be instant on first load, precompute a module-level mean/variance aggregate table. Keep the frontend module-ID order **stable** so the query-string cache hits.

### `ScatterplotComponent` "Add remaining modules" contract
- The reusable `<app-scatterplot>` has its **own** `showRemaining` toggle and calls `dataSource.getData({ ...params, showRemaining })`; it then draws `isTop !== false` points as **red (top-N)** and `isTop === false` points as **grey (remaining, only when `showRemaining`)**. This is **separate** from the lollipop plot's own `toggleRemaining()` button (which only shows for `vis === 'plot'`).
- Therefore every scatter `dataSource.getData` MUST (a) honour `params.showRemaining` by fetching the **full** module list (not just top-N), and (b) set `isTop` per point (`topIDs.has(id)`). The Explore "Enrichment: Mean vs Variance" source (`enrichmentMeanVarDataSource`) previously ignored `showRemaining` and hard-coded `isTop:true`, so its "Add remaining" did nothing — fixed to fetch all modules via `getLollipopData(…, 10000, …)` and mark `isTop = topIDs.has(ensemblID)`.

---

## 5. Patient-Specific (Predict) Network — `PredictBrowseService`

Drives the "Compute SpongEffects Scores" network from `PredictService` signals (mirrors `ExploreBrowseService`). Renders each module as an **induced subgraph**: center + displayed members + every ceRNA edge among them (center↔member AND member↔member), NO second neighbours.

- **Two-step fetch** (a module can have 1000+ members, too many for a GET URL):
  1. Rank members by the mscor of their edge to the center via `ceRNAInteraction/findAll` on the center(s) only (edge-based → members never enter the URL).
  2. Fetch the induced subgraph on `{centers + topPool}` via `getGeneNetwork` (induced-subgraph semantics keep an edge only when BOTH endpoints are in the passed set). Pool buffered to `max(POOL_SIZE=100, maxNodes)`; result cached per `{level,dataset,version,scope,allIDs}`.
- **Client-side filtering for instant sliders**: the backend is always queried unfiltered (`maxPValue=1`, `minMscor=0`, thresholds 0); mscor, p-value, min-degree/centrality, gene-type, support, node cap (`maxNodes`), edge cap+sort (`maxInteractions`/`interactionSorting`) are all applied client-side. Cache keys therefore do NOT depend on the slider values.
- **Virtual (fallback) edges**: for pool members defined as first-neighbours in `models.RDS` but lacking a DB center edge, a synthetic edge (`isVirtual:true`, `mscor:'< 0.2'`) is added ONLY in the fully-unfiltered state (`minMscor ≤ 0 && maxPValue ≥ 1`). Rendered very thin (fixed `size 0.4`) and excluded from the mscor→thickness normalization (`browse.service.ts createGraph`).
- **Orphan filter runs LAST**, over the final edge set (after support/gene-type/centrality + node cap + edge cap), so a node stranded by ANY filter is hidden when "Show orphans" is off. Centers are NOT force-kept — all filters + the node cap apply to them too.
- **Auto-bounds**: on a fresh module (keyed on scope/dataset/level/modules/includeMembers), after the unfiltered fetch the mscor/p-value sliders snap to the displayed edges' actual bounds (`minMscor=min(mscor)`, `maxPValue=max(p_value)`). Kept at 0/1 when any virtual edge is displayed. Runs once per module — user edits afterwards are left alone.

## 6. Cross-Level Support (`has_inverse`)

- Support = whether a matching interaction exists at the opposite level (gene↔transcript). Node shape: **circle = has support, square = no support** (`borderedCircle`/`borderedSquare` for centers).
- **Patient-specific network uses a DIFFERENT mechanism than Browse**: it reads the per-node `has_inverse` column from `network_analysis_gene`/`_transcript` **directly** (`Boolean(node.has_inverse)`), NOT by fetching the inverse network and diffing gene-name sets (which is what `BrowseService` does). Requires `getGeneNetwork` to serialize `has_inverse` on each node (schema `networkAnalysisSchema`).
- Synthetic/minimal nodes (no DB row → `has_inverse` null/undefined) are shown only when the Support filter is "all".

## 7. `get_gene_network` Node Selection (Bug-B fix)

- `candidate_ids` when `ensemblID` is passed must be **all requested genes** (`set(gene_query)`), NOT `gene_ids_in_edges ∩ requested`. The old intersection silently DROPPED any requested node whose edges were prefiltered out (e.g. by the `maxPValue` edge prefilter) — even though it had a real `networkAnalysis` row — producing centers with N/A centralities. Nodes missing a row are synthesized with null metrics so the response shape is preserved.

## 8. Shared Filter Drawer & Module Filtering (SpongEffects)

- **`NetworkFiltersComponent`** (`components/network-filters/`) renders the shared **Nodes + Interactions** filter panels for BOTH the Scores and Explore drawers, driven by a `NetworkFilterSignals` interface (14 signals). `PredictService` and `ExploreService` both expose these signals (structural match). `<app-form>` (`routes/browse/form`) is now **Browse-only**; Explore's network filtering moved onto `ExploreService` signals (gene-type + support applied client-side in `ExploreBrowseService`, since `getNetwork` ignores those two params).
- **`ModuleFormComponent`** (`app-module-form`, `source: 'predict'|'explore'`) is the shared "Module Filtering" panel. Which control drives what is consistent across both views:
  - **Max module centers (top-N)** + **Show module members** drive the *network* (Explore: `exploreService.selectedModules` slices to `topN`; Predict: `topModules$` = top-N by mean enrichment across selected samples). `includeModuleMembers` MUST be tracked by the browse-service query effect or the checkbox has no effect.
  - **Sort by** + **Min-score** filters drive the *"Top ceRNA Modules" plots/tables*, not the core network module set.
  - Source-specific: Predict has a "Patients to Consider" selector; sort/score **metrics differ** — Explore offers model-importance (Mean Accuracy/Gini Decrease) AND enrichment (Abs. Mean / Mean / Variance), Predict offers only the enrichment set. Explore modules get enrichment metrics attached in `getLollipopData` via `fetchSpongEffectsEnrichScores(…, average=false)`.
  - **`redNodes` (Explore) is deprecated/removed** — `topN` is the sole module-count limiter; the old `markControl` was never rendered.

---

## 9. Sponge Runs vs SpongEffects Runs; Network Query, Sorting & Filtering

### One sponge (network) run per dataset; multiple spongEffects (module) runs
- Per disease dataset there is exactly **1 `sponge_run`** (the ceRNA interaction network) but **several `spongEffects_run`s** (module/enrichment param-set variants differing in `m_scor_threshold` / `p_adj_threshold` / `modules_cutoff`). Every spongEffects run of a dataset references that dataset's single sponge run.
- Confirmed example: BRCA → `dataset_ID 98` → `sponge_run_ID 87`; spongEffects runs 2/3/4/51/52 all carry `dataset_ID 98` / `sponge_run_ID 87`.
- **The network must always be built on the dataset's single sponge run** — handled correctly end-to-end:
  - **Frontend**: `spongEffectsService.datasets$` derives each dataset's `dataset_ID` from the spongEffects runs (`run.dataset_ID`), deduped — so a disease resolves to the dataset the modules were built on (BRCA → 98). `ExploreService.selectedDiseaseObject$` / `getGeneNetwork` use that `dataset_ID`.
  - **Backend**: `get_gene_network` `run_query = SpongeRun WHERE sponge_db_version [AND dataset_ID]` → the one run.

### `getGeneNetwork` expects COMMA-SEPARATED `ensemblID`
- Since commit `8cc90ee`, `ensemblID` is a single comma-joined string (`ensemblID=A,B,C`), **not** repeated params (`ensemblID=A&ensemblID=B`). Repeated params → only the last value is parsed → 1 node / 0 edges (a debugging gotcha). The frontend already sends comma-joined (`backend.service.ts getNetwork`: `Array.isArray(ensemblID) ? join(',') : …`).

### Backend sorting & filtering — `get_gene_network`
1. **Edge prefilter**: `sponge_run_ID IN runs AND (gene1 OR gene2 IN requested) AND p_value ≤ maxPValue`.
2. **Node selection, two paths**:
   - *`use_network_analysis`* (when `nodeSorting` **or** any `minBetweenness/minNodeDegree/minEigenvector` is set): candidates = **all requested genes**; attach run-scoped `networkAnalysis` rows + synthesize null-metric nodes for genes with no row; apply min-metric filters (null→0); **sort** = rank per key (desc, tie-aware) then order by the **mean of ranks**; paginate `[offsetNodes:+maxNodes]`.
   - *else*: candidates = all requested genes **ordered by `gene_ID`** (arbitrary), paginated `[start:+maxNodes]`, then attach/synthesize metrics.
3. **Edge selection**: keep edges with BOTH endpoints in the selected nodes; apply `minMscor`, `minCorrelation`; **sort** by `edgeSorting` (`pValue`→p ASC, `mscor`→mscor DESC, `correlation`→corr DESC); paginate `[offsetEdges:+maxEdges]`.

### Frontend neutralises the backend sort/filter and does it client-side
- Both `ExploreBrowseService` and `PredictBrowseService` call `getGeneNetwork` **unfiltered** (`maxPValue=1`, `minMscor=0`, thresholds 0, `maxNodes = allIDs+10`, `maxInteractions=50000`), so the backend returns the full induced subgraph and its node/edge sort order is irrelevant. All user-facing filtering/sorting is **client-side**: edge mscor/p → node degree/centrality/gene-type/support → sort (centers first → center-edge mscor → centrality toggles → node_degree) → `maxNodes` cap → edge sort by `interactionSorting` → `maxInteractions` cap → **orphan removal LAST**.

### Interaction endpoints — edge predicate & run scoping
- **`findAll` (`read_all_genes`)**: edges where gene1 **OR** gene2 ∈ set (neighbourhood). Defaults `pValue=0.05` (`≤`), `limit=100` (hard cap **1000**). Used by predict **and now Explore** to rank members by center-edge mscor. The FE wrapper `getGeneInteractionsAll` paginates by 1000 to fetch all, and sends **both** `disease_name` + `dataset_ID`.
- **`findSpecific` (`read_specific_interaction`)**: edges where gene1 **AND** gene2 ∈ set (induced). `pValue=0.05` (`<`), hard cap **1000**.
- **`getGeneNetwork`**: induced (both ∈ selected node set) + node-analysis/synthesis; `maxEdges` default **100** (FE overrides to 50000). No hard cap.
- **FIXED — cartesian `dataset_ID` scoping bug**: `read_all_genes`, `read_specific_interaction`, and 5 sibling functions filtered `Dataset.dataset_ID == dataset_ID` while only joining `Dataset` when `disease_name` was given. With `dataset_ID` alone (no `disease_name`) this cross-joined → `run_IDs` = *all* runs (wrong data). Changed to `SpongeRun.dataset_ID` (matches `get_gene_network`). Latent in the app (the FE always sends both params, so `Dataset` was joined and the filter narrowed correctly), but fixed defensively. Requires backend restart + redis flush to take effect.
- `disease_name` uses `LIKE %…%` → matches all subtypes of a disease; always pair it with `dataset_ID` to pin the single run.

### Module membership is broader than DB first-neighbours; Explore now mirrors predict
- Empirically: BRCA module center EBF3 (module 4012, a single module — **not** a union across runs) → `getSpongEffectsGeneModuleMembers` returns **505 members**, but `getGeneNetwork(dataset 98, EBF3 + members, maxPValue=1)` yields only **240 center↔member edges** — ~half the members have **no** direct DB ceRNA edge to the center. Members are **stored rows** (`SpongEffectsGeneModuleMembers`) from the spongEffects analysis network, which no longer matches the DB `GeneInteraction` edges. So "a module member has a center edge by definition" does NOT hold against the DB.
- **Member-list derivation**: `get_gene_module_members` → `get_gene_modules(get_best=True default)` → the *best-accuracy* run's module. So fetching members by `ensg_number` returns the best run's members regardless of which param-set run the displayed center came from. **Fixed**: Explore now fetches members by `spongEffects_module_ID` (`fetchModuleMembers` → `getGeneModuleMembers({moduleId})`), so members always belong to the selected center's module.
- **`ExploreBrowseService` now uses the same two-step engine as `PredictBrowseService`**: (1) `findAll` on the center(s) → rank members by center-edge mscor → keep the strongest **`POOL_SIZE=100`** as the pool (bounds the `getGeneNetwork` URL/payload — previously it sent *all* 505 members / 23 k edges); (2) `getGeneNetwork` on `{centers + pool}`, unfiltered, client-side filtering. **Virtual (fallback) edges** are added for pool members with no real DB center edge, gated to the fully-unfiltered state (`minMscor ≤ 0 && maxPValue ≥ 1`), rendered thin. `createVirtualEdge` is shared on the `BrowseService` base class (used by both networks). Net effect: displayed members are the center's strongest-connected ones (real edges), with thin fallback edges only for sparse modules — matching predict.

---

## 10. SpongEffects runs are per-LEVEL (gene vs transcript); Model panel & Benchmarking must filter by level

- A disease can have a **different number of spongEffects runs/models per feature level**. Example: BRCA has **3 gene-level** param-set runs but only **2 transcript-level** runs. `getSpongEffectsRuns` returns *both* levels' runs for a disease.
- **The Explore Model panel, the param-set selection, benchmarking (`getRunPerformance`/`getRunClassPerformance`), and the module network are all level-specific.** `ExploreService.spongeEffectsRuns$` must filter by **`disease_name` AND `level`** — otherwise `paramSets$` becomes the *union across levels* (e.g. 3), the Model panel shows 3 chips, but transcript-level benchmarking only has data for the 2 transcript runs → "Model panel says 3, Benchmarking shows 2". **Fixed** — `spongeEffectsRuns$` now filters `run.disease_name === disease && run.level === level`.
- `ExploreService.level$` default is **`gene`** (do not silently change it — the model counts and the whole Explore view key off it).
- **Debugging note**: a "wrong number of models/params" symptom in Explore is almost always a **level** mismatch, NOT a run-scoping/`dataset_ID` bug. Verify with `getSpongEffectsRuns?disease_name=…` grouped by `.level` before touching backend query code.

---

## 11. Lazy Loading, Component Deferral & Navigation Sequencing

### Frontend Lazy Loading & Chunking (`app.routes.ts`)
- **Route Code-Splitting**: Routes (`/`, `/browse`, `/genes-transcripts`, `/spongeffects`, `/spongeffects/predict`, `/documentation`) use Angular's `loadComponent: () => import(...)`.
- **Heavy Library Isolation**: Heavy dependencies (Sigma.js/graphology, Plotly, Kaplan-Meier, IGV viewer) are isolated in lazy chunks and downloaded only when navigating to views containing network graphs, heatmaps, or genome tracks.

### Detail Modals & Deferred Tabs (`GeneModalComponent` / `TranscriptModalComponent`)
- **General Information**: Loaded eagerly on modal open (`getGeneInfo` / `getTranscriptInfo`).
- **ceRNA Interactions**: Computed in-memory from active `browseService` network nodes (0 extra HTTP requests).
- **SpongEffects Scores**: Resource signals (`module_IDs$`, `tcgaEffects$`) fetch module hubs and mean/variance TCGA scores on-demand.
- **Alternative Splicing**: Fetched lazily per-row using async pipe.
- **Genome View (IGV)**: Deferred until active tab index matches the Genome View tab (`[refresh]="activeTab$()"`).

### Patient-Centric (Predict) vs. Disease-Centric Route Initialization
- **Dataset Catalog Dependency**: `PredictService` resolves dataset IDs for scope selection (`selectedScopeDataset$`) by querying `VersionsService.diseases$()`.
- **Direct Navigation Safeguard**: When navigating directly to `/spongeffects/predict` without prior interaction on disease-centric routes (`/browse` or `/spongeffects`), dataset lists load asynchronously in the background while `activeModelScope$` falls back safely to `'pancancer'` (dataset ID 126).

