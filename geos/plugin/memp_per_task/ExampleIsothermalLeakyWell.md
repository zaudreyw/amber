## Procedural memory (retrieved by similarity)

Below are workflow notes from past similar GEOS XML authoring tasks. They are *guidance*, not commands — adapt to the current task. Top 3 most similar past tasks (cosine similarity in parentheses):

### Past task: TutorialCO2FieldCase (sim 0.752)

To set up a multiphase compositional simulation for CO2 injection, the most effective starting point is a base XML for **compositional multiphase flow with wells**, specifically those referencing CO2 storage benchmarks like SPE11. The workflow begins by defining a `CompositionalMultiphaseFVM` solver, which is essential for handling the mass-based conservation of CO2 and water components. For the constitutive models, use a `BrooksCorey` relative permeability model and a `CompressiblePoreVolume` rock model. To handle complex fluid behavior, utilize `TableFunction` elements to link external PVT and flash data files for phase densities, viscosities, and solubility.

When modeling the wellbore, employ the `InternalWellbore` mesh generator and a `WellboreCompositional` solver to ensure fully coupled reservoir-well hydraulics. A critical step for heterogeneous domains is using a `TableFunction` with `NearestNeighbor` interpolation to map voxelized permeability data onto the Cartesian grid. To maintain a modular setup, separate the physics and numerical settings into a base file, while defining the mesh, well trajectory, and `Event` schedule in a benchmark-specific "smoke" file. A common pitfall is neglecting the `primaryVariable` setting; ensure it is set to `Mass` for compositional stability. Additionally, always verify that the `FieldSpecification` for permeability correctly scales the components (e.g., 1e-15 for mD to m²) to avoid non-physical pressure spikes.


### Past task: TutorialDeadOilBottomLayersSPE10 (sim 0.680)

To author a multiphase, multicomponent reservoir flow simulation, begin by identifying reference XMLs for the SPE10 benchmark or similar dead-oil models. The workflow starts with defining a **CompositionalMultiphaseFVM** solver, typically paired with a **TwoPointFluxApproximation** discretization for the flow physics. For the fluid system, use a **DeadOilFluid** model within a **CompositionalMultiphaseMixture**, specifying surface densities and molar weights. Handle pressure-dependent oil properties by implementing **Table1D** interpolators for formation volume factors and viscosity, referencing external coordinate and voxel files.

For the rock physics, employ a **CompressibleSolid** material with a pressure-dependent porosity model and a **BrooksCoreyRelativePermeability** constitutive element to manage phase interference. When setting up the mesh, use an **InternalMesh** with a regular hexahedral discretization. Wells should be defined using **Box** geometry regions to identify specific cell sets for source and sink terms. A critical architectural step is splitting the setup into a reusable base file (containing physics, materials, and solvers) and a benchmark file (containing mesh and geometry) using the **Included** tag. Avoid schema hallucinations by ensuring the phase order in the mixture matches the relative permeability definitions and verifying that all external table files are correctly referenced.


### Past task: AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity (sim 0.652)

To simulate wellbore cooling with non-linear thermal diffusion, begin by referencing the base XML for a **single-phase thermal compressible flow problem** and the specific benchmark for **temperature-dependent single-phase thermal conductivity**. For the domain, use the `InternalWellbore` mesh generator to create a quarter-symmetry cylindrical mesh, carefully defining radial intervals and using the `autoSpacing` attribute for the outermost region to ensure proper resolution. 

The core physics should be handled by the `SinglePhaseThermal` solver coupled with a `SinglePhaseThermalConductivity` constitutive model. To capture the non-linear diffusion, specify the `defaultThermalConductivityComponent` and the `thermalConductivityGradient` within the conductivity model. Ensure the fluid is defined with a `CompressibleFluid` model and the rock uses a `ConstantVolumetricHeatCapacity` model for its internal energy. Use the `TwoPointFluxApproximation` (TPFA) for spatial discretization within the numerical methods section. 

**Common pitfalls** include hallucinating temperature-dependent attribute names; always verify the schema for the exact gradient parameter names. Additionally, ensure that the `InternalWellbore` mesh parameters (azimuthal sweep and radial intervals) align with the symmetry requirements and that boundary conditions are correctly mapped to the generated face sets (e.g., `xNeg` for the inner wellbore face).


---
