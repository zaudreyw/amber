# General XML Configuration Notes

*Generic background notes. Target token budget: ~900 tokens. Not derived
from any training trajectory; shared as context for XML authoring.*

## XML Document Structure

A simulation configuration is an XML document with a single root. The
root contains multiple top-level sections. Each section serves a
distinct purpose: defining the spatial domain, assigning physical
properties, declaring which solvers will run, and scheduling when they
run. Sections may appear in any order within the root.

Well-formed XML requires: (a) every opening tag has a matching close
tag (or is self-closed); (b) attribute values are quoted; (c) element
names are case-sensitive; (d) attribute keys within one element are
unique. Comments are enclosed in angle-bang-dash-dash...dash-dash-angle
and are ignored by parsers.

Attribute values may be scalars (single numbers, strings, booleans) or
lists. Lists are typically wrapped in curly braces with comma
separators, e.g. `{0.0, 1.0, 2.0}`. Vectors of three values are
commonly used for spatial coordinates, dimensions, and mesh sizes.
Numeric values may be written in scientific notation (1.0e-12).
Units are sometimes embedded in the string literal directly, following
the number with a space; consult the schema for each attribute.

## Typical Section Roles

Most physics simulation XMLs include sections in roughly the following
roles:

**Mesh / Geometry sections.** Describe the spatial domain: its bounds,
how it is discretized into elements, what element types are used, and
any pre-defined sub-regions or named surfaces within it. Some problems
define geometry analytically; others load an external mesh file.
Coordinates are typically Cartesian; some problems use cylindrical or
other coordinate systems.

**Constitutive section.** Lists the material models used by the
simulation. Each model has a unique name attribute (used as a reference
elsewhere) and model-specific parameters. Constitutive models span
fluids, solids, rock mechanics, thermal properties, and permeability.
Some models are coupled (the output of one feeds another).

**Element regions.** Associates mesh sub-regions with the constitutive
models that apply to them. Typically each region enumerates the names
of the materials applied to its elements as a list.

**Solver section.** Declares which numerical solvers will run during
the simulation. Each solver has a name, a type, and attributes that
control convergence, linear-algebra parameters, and which
constitutive models and regions it acts on. Solvers may be coupled:
one solver references other solvers by name through dedicated
attributes. Tolerance and iteration-limit attributes are common.

**Field specifications.** Initial conditions and boundary conditions on
fields (e.g., pressure, displacement, temperature). Each specification
names the field, the spatial region it applies to, and the value (a
constant or a function of space/time).

**Numerical methods.** Declares discretization choices — finite
element basis, finite volume discretization, interpolation strategies,
etc. Referenced by solvers via name.

**Events.** Time-stepping schedule and event triggers. Typical entries
include periodic solver applications, output writes at intervals, and
terminal events (simulation end). Each event has a schedule (start
time, end time, period) and a target (a solver or output).

**Outputs.** Declares what is written to disk. Common types are
volumetric field snapshots, time-series summaries, and restart files.
Each output specifies a plot filename or restart directory and a
subset of fields to write.

**Functions.** Space- or time-varying data tables referenced by field
specifications. May be inline arrays or references to external data
files.

**Tasks.** Post-simulation analysis or data-extraction tasks run as
part of the simulation lifecycle.

## General Style Considerations

Attribute values that appear in multiple places (e.g., a region name
used in both a solver and a field specification) must match exactly;
XML does not resolve close-misspelling as a warning. The solver, region,
material model, and function naming choices made in the Constitutive
section must be used verbatim in the Solver and FieldSpecifications
sections.

When a task requires multi-physics coupling, the coupling solver
typically references the names of the individual physics solvers by
attribute. Ensure each referenced name is defined in the Solvers
section with the matching element type.

For output requests, target regions must be declared or inferable
from the Element Regions section. Outputs typically require an event
in the Events section that fires the output periodically.

## Schema Hygiene

Element and attribute names are case-sensitive. When in doubt about
the exact spelling of an element or the set of valid attributes,
consult the schema documentation rather than guessing. Inventing an
element or attribute that doesn't exist leads to a parse-time failure
or silent ignoring.
