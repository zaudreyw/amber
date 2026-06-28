# Per-task run comparison

Runs compared:
- **E17_plug_mm_v2**
- **E18_gmem_mm_v2**

| Task | E17_plug_mm_v2_ts | E17_plug_mm_v2_status | E17_plug_mm_v2_elapsed | E17_plug_mm_v2_tools | E17_plug_mm_v2_rag | E17_plug_mm_v2_mem | E17_plug_mm_v2_$ | E18_gmem_mm_v2_ts | E18_gmem_mm_v2_status | E18_gmem_mm_v2_elapsed | E18_gmem_mm_v2_tools | E18_gmem_mm_v2_rag | E18_gmem_mm_v2_mem | E18_gmem_mm_v2_$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ExampleIsothermalLeakyWell | 0.354 | success | 610 | 25 | 15 | 0 | $0.300 | 0.865 | success | 578 | 45 | 10 | 0 | $0.521 |
| AdvancedExampleCasedContactThermoElasticWellbore | 0.340 | success | 575 | 41 | 25 | 0 | $0.529 | 0.847 | success | 586 | 38 | 17 | 0 | $0.550 |
| ExampleEDPWellbore | 0.945 | success | 173 | 17 | 11 | 0 | $0.114 | 0.468 | success | 341 | 30 | 23 | 0 | $0.245 |
| AdvancedExampleModifiedCamClay | 0.568 | success | 146 | 19 | 12 | 0 | $0.095 | 0.992 | success | 203 | 21 | 9 | 0 | $0.153 |
| ExampleThermoporoelasticConsolidation | 0.274 | success | 435 | 43 | 31 | 0 | $0.436 | 0.573 | success | 280 | 30 | 22 | 0 | $0.267 |
| buckleyLeverettProblem | 0.629 | success | 468 | 44 | 16 | 0 | $0.519 | 0.393 | success | 514 | 50 | 35 | 0 | $0.474 |
| TutorialSneddon | 0.148 | success | 362 | 36 | 15 | 0 | $0.353 | 0.301 | success | 420 | 31 | 17 | 0 | $0.320 |
| AdvancedExampleExtendedDruckerPrager | 1.000 | success | 299 | 37 | 9 | 0 | $0.277 | 0.880 | success | 185 | 19 | 10 | 0 | $0.108 |
| pknViscosityDominated | 0.328 | success | 526 | 37 | 24 | 0 | $0.476 | 0.404 | success | 534 | 37 | 28 | 0 | $0.323 |
| TutorialPoroelasticity | 0.667 | success | 237 | 25 | 14 | 0 | $0.185 | 0.723 | success | 294 | 26 | 9 | 0 | $0.239 |
| ExampleMandel | 0.314 | success | 288 | 21 | 13 | 0 | $0.177 | 0.349 | success | 310 | 29 | 18 | 0 | $0.307 |
| kgdExperimentValidation | 0.923 | success | 158 | 11 | 6 | 0 | $0.084 | 0.903 | success | 224 | 20 | 12 | 0 | $0.160 |
| AdvancedExampleViscoDruckerPrager | 0.985 | success | 218 | 41 | 14 | 0 | $0.247 | 0.998 | success | 179 | 28 | 10 | 0 | $0.147 |
| AdvancedExampleDeviatedElasticWellbore |  -  | failed_no_outputs | 35 | 2 | 2 | 0 | $0.009 | 0.879 | success | 313 | 32 | 12 | 0 | $0.239 |
| AdvancedExampleDruckerPrager |  -  | failed_no_outputs | 44 | 7 | 4 | 0 | $0.038 | 0.965 | success | 243 | 34 | 12 | 0 | $0.255 |
| ExampleDPWellbore |  -  | failed_no_outputs | 39 | 6 | 6 | 0 | $0.019 | 0.978 | success | 174 | 17 | 9 | 0 | $0.118 |
| ExampleThermalLeakyWell |  -  | failed_no_outputs | 27 | 3 | 3 | 0 |  -  | 0.815 | success | 306 | 34 | 24 | 0 | $0.303 |

## Summary

| Metric | E17_plug_mm_v2 | E18_gmem_mm_v2 |
|---|---|---|
| Tasks scored (treesim present) | 13/17 | 17/17 |
| Mean TreeSim (scored only) | 0.575 | 0.725 |
| Mean TreeSim (failures=0, over all tasks below) | 0.440 | 0.725 |
| Total cost (sum openrouter_cost_usd) | $3.860 | $4.729 |
| Total per-task elapsed (sum elapsed_s) | 4640s | 5684s |

## Paired (13 tasks scored in both)

- Mean delta (E18_gmem_mm_v2 - E17_plug_mm_v2): **+0.094**
- Wins E17_plug_mm_v2: 4, Wins E18_gmem_mm_v2: 9, Ties: 0
