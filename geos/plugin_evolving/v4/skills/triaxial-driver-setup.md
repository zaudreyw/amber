---
name: triaxial-driver-setup
description: How to create a GEOS TriaxialDriver input file for constitutive model testing
---
## Detailed instructions

1. **Find a base file**: Start from `<file>` in `/geos_lib/inputFiles/triaxialDriver/`. It defines the solver, output, and table functions. Override only the `<Constitutive>` block and possibly the solver parameters.
2. **Copy table files**: The base file expects `tables/time.geos`, `tables/axialStrain.geos`, `tables/radialStress.geos`. Copy them from the same directory to your workspace (e.g., `tables/` subdirectory). Use `Bash` to create the directory and copy.
3. **Modify constitutive model**: Replace the placeholder solid model with the desired one (e.g., `ExtendedDruckerPrager`, `ModifiedCamClay`, `ViscoExtendedDruckerPrager`). Provide all required parameters (friction angle, dilation angle, hardening rate, etc.). For viscoplastic models, include `relaxationTime`.
4. **Adjust solver parameters**: In the `<TriaxialDriver>` solver, you may need to set `maxTime`, `timeStep`, etc. to match the table duration.
5. **Output configuration**: The base file already has `<HistoryCollection>` for `TriaxialDriver`. Ensure `fieldName` is set to e.g., `stress`, `strain`. Add additional fields if needed.
6. **Write final files**: Output the main XML (e.g., `<file>`) and the three table files. The main XML should `<Included>` the base file or be standalone if you copied the full structure.
