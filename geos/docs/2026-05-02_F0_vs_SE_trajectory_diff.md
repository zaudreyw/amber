# F0 vs SE trajectory diff

*Generated 2026-05-02 from `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/F0_vs_SE_diff.json` via DeepSeek summary of top
5 highest-savings (task, seed) pairs.*

## Aggregate (51 pairs)

| metric | F0 (no plugin) | SE (plugin v3) | Δ (F0−SE) |
|---|---:|---:|---:|
| avg turns | 105.9 | 94.3 | **+11.6** |
| avg tools | 81.5 | 68.9 | **+12.7** |
| avg tools-before-first-Write | 72.5 | 59.3 | **+13.2** |
| avg unique files read | 32.3 | 23.9 | +8.4 |
| avg input tokens | 4.43M | 3.64M | +0.79M |
| avg read-backs | 2.3 | 0.2 | +2.1 |

**Most of the savings come from "tools before first Write"** — the
exploration phase. F0 averages 72 search/read calls before
emitting its first XML; SE averages 59. SE jumps to canonical
files faster.

## Top 5 highest-savings (task, seed) pairs

| task | seed | F0 turns | SE turns | Δ |
|---|:-:|---:|---:|---:|
| ExampleThermoporoelasticConsolidation | s3 | 134 | 50 | +84 |
| AdvancedExampleExtendedDruckerPrager | s3 | 174 | 98 | +76 |
| ExampleMandel | s2 | 129 | 58 | +71 |
| TutorialSneddon | s1 | 161 | 92 | +69 |
| AdvancedExampleCasedContactThermoElasticWellbore | s1 | 170 | 105 | +65 |

## Top files F0 reads but SE skips

These are the files that appear in F0 trajectories but not in matched SE
trajectories — candidate compression targets.

| reads | file |
|---:|---|
| 11× | `/geos_lib/src/coreComponents/schema/schema.xsd` |
| 9× | `/geos_lib/inputFiles/poromechanics/PoroElasticWellbore_base.xml` |
| 9× | `/workspace/inputs/triaxialDriver_base.xml` |
| 8× | `/geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/spe11b_vti_source_base.xml` |
| 7× | `/geos_lib/inputFiles/solidMechanics/ModifiedCamClayWellbore_base.xml` |
| 7× | `/geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/kr.xml` |
| 6× | `/geos_lib/inputFiles/poromechanics/PoroViscoModifiedCamClay_base.xml` |
| 6× | `/geos_lib/inputFiles/solidMechanics/viscoExtendedDruckerPrager_relaxation_base.xml` |
| 6× | `/geos_lib/src/docs/sphinx/basicExamples/triaxialDriver/Example.rst` |
| 6× | `/geos_lib/src/coreComponents/constitutive/solid/DruckerPrager.hpp` |
| 6× | `/geos_lib/src/coreComponents/constitutive/solid/DruckerPragerExtended.hpp` |
| 6× | `/geos_lib/src/coreComponents/constitutive/solid/DuvautLionsSolid.hpp` |
| 6× | `/geos_lib/src/coreComponents/constitutiveDrivers/solid/TriaxialDriver.cpp` |
| 6× | `/geos_lib/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_base.xml` |
| 6× | `/geos_lib/inputFiles/compositionalMultiphaseFlow/benchmarks/SPE11/b/include/dirichlet_boundary_vti.xml` |
| 5× | `/geos_lib/inputFiles/wellboreECP/ECP_Wellbore_geom01.xml` |
| 5× | `/geos_lib/inputFiles/wellbore/CasedElasticWellbore_base.xml` |
| 5× | `/geos_lib/inputFiles/poromechanics/PoroViscoDruckerPrager_base.xml` |
| 5× | `/geos_lib/inputFiles/solidMechanics/DruckerPragerWellbore_base.xml` |
| 5× | `/geos_lib/inputFiles/solidMechanics/ExtendedDruckerPragerWellbore_base.xml` |

## Per-pair pattern analysis (DeepSeek)

### Pair 1: ExampleThermoporoelasticConsolidation (s3)

- **F0** spent 7 Glob calls searching for thermoporoelastic files across multiple patterns (`*thermoPoro*`, `*Poromechanics*`, `*Thermal*`, `*consolidation*`). **SE** used 2 targeted Grep calls (`ThermoPoroElastic`, `SinglePhasePoromechanics`) to directly locate the relevant directory, then immediately Read the key files.
- **Plugin asset:** `memory/cheatsheet.md` (m1u-distilled GEOS XML cheatsheet) likely provided the exact solver name (`SinglePhasePoromechanics`) and file naming conventions, eliminating the need for broad glob searches.
- **Generalizable:** Yes — the cheatsheet's knowledge of solver names and file patterns can shortcut file discovery for any GEOS physics solver.

### Pair 2: AdvancedExampleExtendedDruckerPrager (s3)

- **F0** used 2 Agent calls and 7 Glob/Grep calls to explore triaxial driver examples and search for DruckerPrager variants. **SE** used 1 Grep (`TriaxialDriver`), 1 Glob (`**/triaxialDriver/**`), and immediately Read the correct example file.
- **Plugin asset:** `skills/triaxial-driver-setup.md` (recipe for triaxial driver tasks) provided the exact directory path (`triaxialDriver/`) and file naming pattern, bypassing exploratory searches.
- **Generalizable:** Task-specific — this skill is tailored to triaxial driver tasks, but similar skills could be created for other common task families.

### Pair 3: ExampleMandel (s2)

- **F0** used 2 Agent calls and 6 Grep/Glob calls searching for poroelasticity examples, mesh generation, and specific keywords (`Mandel`, `BiotPorosity`). **SE** used 1 Agent call, 3 targeted Globs (`*Mandel*`, `poromechanics/**`, `tables/**`), and 1 Grep (`Mandel`) to quickly locate the benchmark file.
- **Plugin asset:** `memory/cheatsheet.md` likely provided knowledge of the `tables/` directory convention for Mandel problems, and the exact solver name (`SinglePhasePoromechanics`).
- **Generalizable:** Yes — the cheatsheet's knowledge of problem-specific directory structures (e.g., `tables/` for Mandel) can accelerate file discovery for any well-known benchmark.

### Pair 4: TutorialSneddon (s1)

- **F0** used 1 Agent call and 6 Bash/Glob calls to explore multiple directories (`efemFractureMechanics`, `hydraulicFracturing`, `solidMechanics`, etc.) before finding Sneddon examples. **SE** used 3 parallel Agent calls targeting specific subdirectories (`efemFractureMechanics`, `lagrangianContactMechanics`, `hydroFracture`), then immediately Read the benchmark files.
- **Plugin asset:** `memory/cheatsheet.md` likely provided knowledge that Sneddon problems span multiple physics directories (EFEM, contact, hydrofracture), enabling parallel targeted searches instead of sequential exploration.
- **Generalizable:** Yes — the cheatsheet's mapping of problem names to relevant directories can guide parallel search strategies for any multi-physics benchmark.

### Pair 5: AdvancedExampleCasedContactThermoElasticWellbore (s1)

- **F0** used 2 Agent calls and 6 Glob/Grep calls exploring broadly (`*SurfaceGenerator*`, `*Contact*`, `*Poromechanics*`). **SE** used 1 Agent call and 8 targeted Globs (`*wellbore*`, `*casing*`, `*cement*`, `*debond*`, `*thermo*`, `*hydrofracture*`, `*SurfaceGenerator*`, `*Contact*`, `*Poromechanics*`) to narrow down quickly.
- **Plugin asset:** `memory/cheatsheet.md` likely provided the list of relevant keywords for wellbore problems (casing, cement, debond, thermo), enabling precise glob patterns instead of broad searches.
- **Generalizable:** Yes — the cheatsheet's domain-specific keyword lists can accelerate file discovery for any wellbore or contact mechanics task.

---

## Cross-pair patterns

1. **Cheatsheet-driven file discovery** (pairs 1, 3, 4, 5)
   - The `memory/cheatsheet.md` provides exact solver names, file naming conventions, and directory structures, replacing multi-step Glob/Grep searches with 1-2 targeted calls.
   - **v4 candidate:** Expand the cheatsheet to include a "problem-to-directory" mapping table for all common GEOS benchmarks, enabling even faster parallel searches.

2. **Task-specific skill shortcuts** (pair 2)
   - `skills/triaxial-driver-setup.md` provides a complete recipe for triaxial driver tasks, including exact file paths and naming patterns.
   - **v4 candidate:** Create similar skills for other high-frequency task families (e.g., `skills/poroelastic-consolidation.md`, `skills/sneddon-fracture.md`) to compress discovery for those tasks.

3. **Parallel targeted Agent calls** (pair 4)
   - SE used multiple concurrent Agent calls targeting specific subdirectories, while F0 explored sequentially.
   - **v4 candidate:** Add a "parallel exploration" meta-skill that spawns multiple agents to search different directories simultaneously, guided by cheatsheet knowledge of relevant paths.

## Source

- Diff JSON: `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01/_analysis/F0_vs_SE_diff.json`
- Script: `scripts/trajectory_diff.py`
- Summary script: `scripts/trajectory_diff_summarize.py`
- v3 plugin assets: `/home/matt/sci/repo3/plugin_evolving/v3/`
