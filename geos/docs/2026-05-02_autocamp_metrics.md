# Autocamp 2026-05-01 — Analysis

Source root: `/data/shared/geophysics_agent_data/data/eval/autocamp_2026-05-01`

## Phase 2 main effects (Resolution-IV factorial)

| factor | mean Δ |
|---|---:|
| R (RAG) | -0.032 |
| S (SR-hook) | -0.003 |
| X (xmllint MCP) | +0.007 |
| M (memory) | +0.004 |

(positive = factor on improves quality)

## Phase 1 — primer screen

| cell | seeds | quality (mean) | quality σ | reliability (avg per-task σ) | avg input tok | avg output tok | avg wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| autocamp_p_contract | 1 | 0.934 | 0.000 | 0.000 | 4832157 | 0 | 432 |
| autocamp_p_method | 1 | 0.931 | 0.000 | 0.000 | 4246334 | 0 | 348 |

### Tool-call distribution (% of tool calls)

| cell | Agent | Bash | Edit | Glob | Grep | Read | TaskOutput | TodoWrite | Write |
|---|---|---|---|---|---|---|---|---|---|
| autocamp_p_contract | 2% | 3% | 0% | 12% | 22% | 52% | — | 5% | 4% |
| autocamp_p_method | 2% | 2% | 0% | 14% | 21% | 50% | 0% | 6% | 5% |

### File-extension distribution (Read calls)

| cell | .(no_ext) | .ats | .bash | .cpp | .geos | .hpp | .other | .png |
|---|---|---|---|---|---|---|---|---|
| autocamp_p_contract | — | 10 | — | 13 | 48 | 19 | 2 | 1 |
| autocamp_p_method | 1 | 5 | 2 | 7 | 32 | 68 | — | — |

### Subtree distribution (top file-read prefixes)

**autocamp_p_contract** (n_seeds=1):
  - `/geos_lib/src/coreComponents`: 115
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 91
  - `/geos_lib/inputFiles/solidMechanics`: 91
  - `/geos_lib/inputFiles/triaxialDriver`: 84
  - `/geos_lib/inputFiles/poromechanics`: 80
  - `/geos_lib/src/docs`: 65
  - `/geos_lib/inputFiles/wellbore`: 62
  - `/geos_lib/inputFiles/hydraulicFracturing`: 61
  - `/geos_lib/inputFiles/thermoPoromechanics`: 33
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 12
  - `/geos_lib/inputFiles/poromechanicsFractures`: 11
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 6
  - `/geos_lib/inputFiles/wellboreECP`: 5
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 5
  - `/geos_lib/inputFiles/efemFractureMechanics`: 4

**autocamp_p_method** (n_seeds=1):
  - `/geos_lib/inputFiles/hydraulicFracturing`: 90
  - `/geos_lib/src/coreComponents`: 89
  - `/geos_lib/inputFiles/poromechanics`: 64
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 56
  - `/geos_lib/inputFiles/wellbore`: 47
  - `/geos_lib/inputFiles/solidMechanics`: 40
  - `/geos_lib/inputFiles/triaxialDriver`: 37
  - `/geos_lib/inputFiles/thermoPoromechanics`: 32
  - `/geos_lib/src/docs`: 29
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 15
  - `/geos_lib/inputFiles/wellboreECP`: 15
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 13
  - `/geos_lib/inputFiles/poromechanicsFractures`: 12
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 9
  - `/geos_lib/inputFiles/efemFractureMechanics`: 5

## Phase 2 — DSv4 fractional factorial + SE

| cell | seeds | quality (mean) | quality σ | reliability (avg per-task σ) | avg input tok | avg output tok | avg wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| autocamp_F0 | 3 | 0.910 | 0.019 | 0.030 | 4429007 | 0 | 359 |
| autocamp_F1 | 3 | 0.885 | 0.011 | 0.024 | 2938848 | 0 | 279 |
| autocamp_F2 | 3 | 0.919 | 0.003 | 0.023 | 3980137 | 0 | 349 |
| autocamp_F3 | 3 | 0.874 | 0.018 | 0.039 | 2830689 | 0 | 274 |
| autocamp_F4 | 3 | 0.921 | 0.006 | 0.016 | 4620075 | 0 | 337 |
| autocamp_F5 | 3 | 0.893 | 0.027 | 0.037 | 3156020 | 0 | 257 |
| autocamp_F6 | 3 | 0.917 | 0.003 | 0.019 | 4701938 | 0 | 348 |
| autocamp_F7 | 3 | 0.885 | 0.007 | 0.022 | 3003622 | 0 | 274 |
| autocamp_SE | 3 | 0.919 | 0.016 | 0.028 | 3640656 | 0 | 321 |

### Tool-call distribution (% of tool calls)

| cell | Agent | Bash | Edit | Glob | Grep | Read | TodoWrite | WebFetch | WebSearch | Write | mcp__geos-rag__search_navigator | mcp__geos-rag__search_schema | mcp__geos-rag__search_technical | mcp__xmllint__validate_geos_xml |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| autocamp_F0 | 2% | 4% | — | 13% | 20% | 52% | 5% | — | — | 4% | — | — | — | — |
| autocamp_F1 | — | 2% | 0% | 5% | 2% | 31% | 11% | — | — | 9% | 6% | 21% | 12% | — |
| autocamp_F2 | 2% | 7% | — | 10% | 21% | 48% | 6% | 2% | 1% | 4% | 0% | — | — | — |
| autocamp_F3 | — | 2% | 0% | 5% | 2% | 34% | 11% | — | — | 9% | 6% | 16% | 14% | — |
| autocamp_F4 | 1% | 4% | — | 12% | 22% | 44% | 6% | — | — | 4% | 1% | 1% | — | 4% |
| autocamp_F5 | — | 1% | — | 7% | 2% | 28% | 12% | — | — | 9% | 5% | 17% | 11% | 8% |
| autocamp_F6 | 2% | 5% | — | 13% | 20% | 44% | 6% | — | — | 4% | 1% | 1% | — | 3% |
| autocamp_F7 | — | 2% | — | 4% | 2% | 26% | 13% | — | — | 9% | 6% | 19% | 12% | 8% |
| autocamp_SE | 2% | 9% | 0% | 12% | 18% | 45% | 6% | — | — | 5% | — | — | — | 4% |

### File-extension distribution (Read calls)

| cell | .(no_ext) | .ats | .bash | .cpp | .csv | .dat | .geos | .hpp |
|---|---|---|---|---|---|---|---|---|
| autocamp_F0 | 7 | 20 | — | 31 | 8 | 1 | 109 | 89 |
| autocamp_F1 | 1 | 1 | — | — | — | — | 31 | — |
| autocamp_F2 | 8 | 24 | 1 | 33 | — | — | 81 | 38 |
| autocamp_F3 | — | 1 | — | — | — | — | 41 | — |
| autocamp_F4 | 3 | 27 | 4 | 15 | 2 | — | 70 | 57 |
| autocamp_F5 | — | 3 | — | — | — | — | 37 | — |
| autocamp_F6 | 6 | 22 | — | 16 | — | — | 67 | 58 |
| autocamp_F7 | — | — | — | 1 | — | — | 35 | 1 |
| autocamp_SE | — | 37 | — | 16 | 5 | — | 124 | 47 |

### Subtree distribution (top file-read prefixes)

**autocamp_F0** (n_seeds=3):
  - `/geos_lib/src/coreComponents`: 376
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 281
  - `/geos_lib/inputFiles/triaxialDriver`: 245
  - `/geos_lib/inputFiles/poromechanics`: 202
  - `/geos_lib/inputFiles/solidMechanics`: 173
  - `/geos_lib/src/docs`: 139
  - `/geos_lib/inputFiles/wellbore`: 107
  - `/geos_lib/inputFiles/hydraulicFracturing`: 98
  - `/geos_lib/inputFiles/thermoPoromechanics`: 85
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 77
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 49
  - `/geos_lib/inputFiles/efemFractureMechanics`: 42
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 29
  - `/geos_lib/inputFiles/poromechanicsFractures`: 28
  - `/geos_lib/inputFiles/singlePhaseFlow`: 16

**autocamp_F1** (n_seeds=3):
  - `/geos_lib/inputFiles/triaxialDriver`: 121
  - `/geos_lib/inputFiles/wellbore`: 53
  - `/geos_lib/src/docs`: 49
  - `/geos_lib/inputFiles/hydraulicFracturing`: 47
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 45
  - `/geos_lib/inputFiles/solidMechanics`: 32
  - `/geos_lib/inputFiles/poromechanics`: 32
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 25
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 14
  - `/geos_lib/inputFiles/efemFractureMechanics`: 8
  - `/geos_lib/inputFiles/thermoPoromechanics`: 8
  - `/workspace/inputs/triaxialDriver_base.xml`: 6
  - `/workspace/backend/app`: 4
  - `/workspace/inputs/buckleyLeverett_base.xml`: 3
  - `/workspace/inputs/buckleyLeverett_benchmark.xml`: 3

**autocamp_F2** (n_seeds=3):
  - `/geos_lib/src/coreComponents`: 325
  - `/geos_lib/inputFiles/triaxialDriver`: 207
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 186
  - `/geos_lib/inputFiles/solidMechanics`: 185
  - `/geos_lib/inputFiles/poromechanics`: 143
  - `/geos_lib/inputFiles/hydraulicFracturing`: 126
  - `/geos_lib/src/docs`: 108
  - `/geos_lib/inputFiles/wellbore`: 77
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 77
  - `/geos_lib/inputFiles/thermoPoromechanics`: 57
  - `/geos_lib/inputFiles/efemFractureMechanics`: 27
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 23
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 23
  - `/geos_lib/inputFiles/poromechanicsFractures`: 20
  - `/geos_lib/inputFiles/surfaceGeneration`: 12

**autocamp_F3** (n_seeds=3):
  - `/geos_lib/inputFiles/triaxialDriver`: 117
  - `/geos_lib/inputFiles/wellbore`: 68
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 58
  - `/geos_lib/inputFiles/hydraulicFracturing`: 57
  - `/geos_lib/src/docs`: 46
  - `/geos_lib/inputFiles/poromechanics`: 38
  - `/geos_lib/inputFiles/solidMechanics`: 29
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 22
  - `/geos_lib/inputFiles/thermoPoromechanics`: 15
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 12
  - `/workspace/inputs/triaxialDriver_base.xml`: 9
  - `/geos_lib/inputFiles/efemFractureMechanics`: 8
  - `/geos_lib/inputFiles/singlePhaseFlow`: 5
  - `/workspace/inputs/tables`: 4
  - `/workspace/inputs/ExtendedDruckerPragerWellbore_benchmark.xml`: 4

**autocamp_F4** (n_seeds=3):
  - `/geos_lib/src/coreComponents`: 316
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 213
  - `/geos_lib/inputFiles/triaxialDriver`: 174
  - `/geos_lib/inputFiles/poromechanics`: 170
  - `/geos_lib/inputFiles/solidMechanics`: 161
  - `/geos_lib/inputFiles/hydraulicFracturing`: 148
  - `/geos_lib/inputFiles/wellbore`: 125
  - `/geos_lib/src/docs`: 83
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 80
  - `/geos_lib/inputFiles/thermoPoromechanics`: 70
  - `/geos_lib/inputFiles/efemFractureMechanics`: 44
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 30
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 24
  - `/geos_lib/inputFiles/poromechanicsFractures`: 23
  - `/geos_lib/inputFiles/surfaceGeneration`: 18

**autocamp_F5** (n_seeds=3):
  - `/geos_lib/inputFiles/triaxialDriver`: 107
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 90
  - `/geos_lib/inputFiles/wellbore`: 85
  - `/geos_lib/inputFiles/hydraulicFracturing`: 49
  - `/geos_lib/src/docs`: 39
  - `/geos_lib/inputFiles/solidMechanics`: 35
  - `/geos_lib/inputFiles/poromechanics`: 35
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 31
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 15
  - `/geos_lib/inputFiles/efemFractureMechanics`: 14
  - `/geos_lib/inputFiles/thermoPoromechanics`: 14
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 4
  - `/geos_lib/inputFiles/immiscibleMultiphaseFlow`: 2
  - `/workspace/inputs/thermalLeakyWell_base.xml`: 2
  - `/geos_lib/inputFiles/proppant`: 1

**autocamp_F6** (n_seeds=3):
  - `/geos_lib/src/coreComponents`: 402
  - `/geos_lib/inputFiles/triaxialDriver`: 208
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 180
  - `/geos_lib/inputFiles/poromechanics`: 179
  - `/geos_lib/inputFiles/solidMechanics`: 177
  - `/geos_lib/src/docs`: 164
  - `/geos_lib/inputFiles/hydraulicFracturing`: 125
  - `/geos_lib/inputFiles/wellbore`: 97
  - `/geos_lib/inputFiles/thermoPoromechanics`: 81
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 66
  - `/geos_lib/inputFiles/efemFractureMechanics`: 35
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 29
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 25
  - `/geos_lib/inputFiles/poromechanicsFractures`: 24
  - `/geos_lib/inputFiles/wellboreECP`: 12

**autocamp_F7** (n_seeds=3):
  - `/geos_lib/inputFiles/triaxialDriver`: 122
  - `/geos_lib/inputFiles/wellbore`: 70
  - `/geos_lib/inputFiles/hydraulicFracturing`: 50
  - `/geos_lib/src/docs`: 44
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 40
  - `/geos_lib/inputFiles/poromechanics`: 33
  - `/geos_lib/inputFiles/solidMechanics`: 31
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 20
  - `/geos_lib/inputFiles/thermoPoromechanics`: 18
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 17
  - `/geos_lib/inputFiles/efemFractureMechanics`: 8
  - `/geos_lib/src/coreComponents`: 3
  - `/workspace/inputs/isothermalLeakyWell_benchmark.xml`: 2
  - `/geos_lib/inputFiles/thermalMultiphaseFlow`: 2
  - `/geos_lib/inputFiles/singlePhaseFlow`: 1

**autocamp_SE** (n_seeds=3):
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 247
  - `/geos_lib/inputFiles/triaxialDriver`: 212
  - `/geos_lib/src/coreComponents`: 193
  - `/geos_lib/inputFiles/poromechanics`: 173
  - `/geos_lib/inputFiles/solidMechanics`: 167
  - `/geos_lib/inputFiles/hydraulicFracturing`: 122
  - `/geos_lib/inputFiles/wellbore`: 119
  - `/geos_lib/src/docs`: 80
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 59
  - `/geos_lib/inputFiles/thermoPoromechanics`: 54
  - `/geos_lib/inputFiles/poromechanicsFractures`: 34
  - `/geos_lib/inputFiles/efemFractureMechanics`: 32
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 18
  - `/geos_lib/inputFiles/wellboreECP`: 13
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 11

## Phase 3 — cross-model

| cell | seeds | quality (mean) | quality σ | reliability (avg per-task σ) | avg input tok | avg output tok | avg wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| autocamp_xmodel_baseline | 6 | 0.647 | 0.166 | 0.210 | 0 | 0 | 134 |
| autocamp_xmodel_best | 6 | 0.534 | 0.305 | 0.324 | 19788 | 290 | 218 |

### Tool-call distribution (% of tool calls)

| cell | Agent | Bash | Edit | Glob | Grep | Read | TodoWrite | Write | mcp__geos-rag__search_navigator | mcp__geos-rag__search_schema | mcp__geos-rag__search_technical | mcp__xmllint__validate_geos_xml |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| autocamp_xmodel_baseline | 0% | 11% | 2% | 14% | 12% | 42% | 6% | 14% | — | — | — | — |
| autocamp_xmodel_best | — | 5% | 2% | 10% | 16% | 29% | — | 12% | 4% | 4% | 2% | 7% |

### File-extension distribution (Read calls)

| cell | .(no_ext) | .ats | .cpp | .geos | .hpp | .json | .md | .other |
|---|---|---|---|---|---|---|---|---|
| autocamp_xmodel_baseline | — | 2 | 2 | 61 | 35 | 1 | — | — |
| autocamp_xmodel_best | 1 | 3 | 5 | 42 | 40 | 3 | 9 | 1 |

### Subtree distribution (top file-read prefixes)

**autocamp_xmodel_baseline** (n_seeds=6):
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 92
  - `/geos_lib/inputFiles/triaxialDriver`: 88
  - `/geos_lib/inputFiles/poromechanics`: 60
  - `/geos_lib/inputFiles/solidMechanics`: 51
  - `/geos_lib/src/coreComponents`: 41
  - `/geos_lib/inputFiles/wellbore`: 32
  - `/geos_lib/inputFiles/hydraulicFracturing`: 29
  - `/geos_lib/inputFiles/thermoPoromechanics`: 20
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 15
  - `/workspace/inputs/triaxialDriver_base.xml`: 14
  - `/geos_lib/inputFiles/poromechanicsFractures`: 12
  - `/geos_lib/inputFiles/efemFractureMechanics`: 11
  - `/workspace/inputs/tables`: 10
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 9
  - `/geos_lib/src/docs`: 8

**autocamp_xmodel_best** (n_seeds=6):
  - `/geos_lib/inputFiles/triaxialDriver`: 120
  - `/geos_lib/inputFiles/compositionalMultiphaseFlow`: 94
  - `/geos_lib/inputFiles/solidMechanics`: 69
  - `/geos_lib/inputFiles/poromechanics`: 58
  - `/geos_lib/src/coreComponents`: 56
  - `/geos_lib/inputFiles/hydraulicFracturing`: 36
  - `/geos_lib/inputFiles/wellbore`: 35
  - `/geos_lib/inputFiles/lagrangianContactMechanics`: 32
  - `/geos_lib/inputFiles/thermoPoromechanics`: 27
  - `/workspace/inputs/triaxialDriver_base.xml`: 17
  - `/geos_lib/src/docs`: 12
  - `/geos_lib/inputFiles/compositionalMultiphaseWell`: 10
  - `/geos_lib/inputFiles/efemFractureMechanics`: 9
  - `/workspace/inputs/thermalLeakyWell_base.xml`: 7
  - `/geos_lib/inputFiles/thermoPoromechanicsFractures`: 6
