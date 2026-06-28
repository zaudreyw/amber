# Reasoning-Memory Items (distilled from past trajectories)

*Each item is a cross-task rule or anti-pattern. Use these to guide solver selection, schema choices, and attribute usage.*


## 1. Hydrofracture Solver Hierarchy

- **Solver family:** hydrofracture
- **Kind:** structural_pattern (high abstraction)
- **Description:** Correct nesting and solver selection for hydraulic fracturing simulations.
- **Applies when:** Physics involves fluid-driven fracture propagation (KGD, radial, or penny-shaped).

Use Hydrofracture as the top-level solver. It must reference a flowSolverName (typically SinglePhaseFVM) and a solidSolverName (typically SolidMechanicsLagrangianFEM). Ensure the fracture surface is defined in the Geometry section and referenced by the solver to handle aperture and propagation.

## 2. Avoid Fracture Vocabulary Hallucinations

- **Solver family:** hydrofracture
- **Kind:** anti_pattern (medium abstraction)
- **Description:** Prevents the use of non-existent fracture-related tags.
- **Applies when:** Defining fracture geometry or propagation logic.

Do NOT use <FractureModel>, <FractureProperties>, or <PropagationCriteria>. These are not valid GEOS elements. Use SurfaceGenerator within the Geometry section to define the fracture plane and use the Hydrofracture solver attributes to control propagation logic.

## 3. Poromechanics Coupling Structure

- **Solver family:** poromechanics
- **Kind:** attribute_rule (medium abstraction)
- **Description:** Mandatory attributes for coupled poromechanical simulations.
- **Applies when:** Simulating coupled fluid flow and solid deformation.

The SinglePhasePoromechanics solver requires explicit mapping of sub-solvers. Use the attributes solidSolverName and flowSolverName to link to the respective Lagrangian mechanics and finite volume flow solvers. Ensure the ElementRegions reference a constitutive model that supports poromechanics, such as those involving Biot coefficients.

## 4. Avoid Generic Boundary Condition Hallucinations

- **Solver family:** all
- **Kind:** anti_pattern (high abstraction)
- **Description:** Prevents the use of standard FEA BC tags that do not exist in GEOS.
- **Applies when:** Defining boundary conditions or initial loads.

Do NOT use <BoundaryCondition>, <FixedConstraint>, or <PressureLoad>. GEOS uses FieldSpecifications for all spatial and temporal field assignments. Within FieldSpecifications, use specific types like BoxFieldSpecification or ComponentFieldSpecification to apply values to sets or regions.

## 5. Triaxial Test Driver Configuration

- **Solver family:** triaxial
- **Kind:** section_skeleton (medium abstraction)
- **Description:** Pattern for single-element or laboratory-scale geomechanics tests.
- **Applies when:** Task specifies strain-controlled or stress-controlled compression (e.g., Cam-Clay or Drucker-Prager validation).

Use the TriaxialDriver element. It requires a Constitutive section defining the soil/rock model (e.g., ViscoplasticModifiedCamClay). The driver must specify control parameters for axial and lateral loading, often referencing specific strain rates or confining pressures directly in its attributes rather than via FieldSpecifications.

## 6. Thermal-Fluid Coupling Requirements

- **Solver family:** thermal
- **Kind:** attribute_rule (medium abstraction)
- **Description:** Rules for thermal transport in porous media.
- **Applies when:** Simulating heat transfer in fluid-filled rock.

Use SinglePhaseThermalFVM. This solver requires a fluid constitutive model that defines heat capacity and thermal conductivity. In the ElementRegions, you must link the thermal solver to a CellElementRegion that specifies both the solid and fluid phase thermal properties.
