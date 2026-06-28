# GEOS Events primer (segment-focused)

The `<Events>` block is the simulation time-loop. Every solver step, every output, every task is triggered by an event in this block.

## Top-level

```xml
<Events maxTime="1000.0" minTime="0.0">
  <PeriodicEvent name="solverStep"
                 forceDt="1.0"
                 target="/Solvers/solidSolver"/>
  <PeriodicEvent name="outputs"
                 timeFrequency="100.0"
                 target="/Outputs/vtkOutput"/>
  <PeriodicEvent name="restarts"
                 timeFrequency="500.0"
                 target="/Outputs/restartOutput"/>
</Events>
```

`maxTime` is THE most-important attribute — it's the simulation end time. Read the task spec carefully for total simulation duration.

## Event types

- **`<PeriodicEvent>`** — fires every `forceDt` seconds OR every `timeFrequency` seconds OR every `cycleFrequency` cycles.
  - `forceDt` — sets the time step itself (used for solvers).
  - `timeFrequency` — fires at this cadence regardless of dt (used for outputs, post-processing).
  - `cycleFrequency` — fires every N timesteps.
  - `beginTime` / `endTime` — restrict the event to a time window.
  - `targetExactStartStop="1"` — synchronize so the simulation lands exactly on event boundaries.
  - `target="<path>"` — what to fire. Path format: `/Solvers/<n>`, `/Outputs/<n>`, `/Tasks/<n>`.
- **`<SoloEvent>`** — fires once.
  - `targetTime="N"` or `targetCycle="N"` — when to fire.
  - `target="<path>"`.
- **`<HaltEvent>`** — kills the run when a condition is met.
  - `maxRuntime="<seconds>"` — wall-clock cap.

## Pattern: poromechanics with output

```xml
<Events maxTime="86400.0">  <!-- 1 day in seconds -->
  <PeriodicEvent name="solverStep"
                 forceDt="3600.0"
                 target="/Solvers/poroSolver"
                 targetExactStartStop="1"/>

  <PeriodicEvent name="vtkOutput"
                 timeFrequency="3600.0"
                 target="/Outputs/vtkOutput"/>

  <PeriodicEvent name="pressureHistoryEvent"
                 timeFrequency="3600.0"
                 target="/Tasks/pressureCollection"/>

  <PeriodicEvent name="pressureHistoryOutput"
                 timeFrequency="3600.0"
                 target="/Outputs/pressureHistoryOutput"/>

  <PeriodicEvent name="restartEvent"
                 timeFrequency="86400.0"
                 target="/Outputs/restartOutput"/>
</Events>
```

Note: time-history needs TWO PeriodicEvents — one to trigger the Task (data collection), one to trigger the matching Output (dump to file). They typically share `timeFrequency`.

## Choosing time step

- `forceDt` for the solver event sets the timestep. Smaller = more accurate, slower. Heuristics:
  - Quasi-static mechanics: `forceDt` = `maxTime / (10–100)`.
  - Dynamic: `forceDt` ≤ CFL limit.
  - Single-phase poro: hours-to-days for reservoir problems.
- `targetExactStartStop="1"` is recommended on solver events to avoid sub-step issues at output boundaries.

## Pitfalls

- **maxTime mismatch.** If the task spec says "simulate for 100 days" and time is in seconds, `maxTime="8640000"`. Off by one factor of 86400 = nonsense results.
- **target path typos.** `/Solver/solidSolver` (missing 's') = silent no-op.
- **Missing the maxTime attribute** = simulation runs forever or stops at default cap.
- **Output without matching Solver event.** If your only Output PeriodicEvent fires every 100s but the solver only takes one 1000s step, you might get one output snapshot when you expected ten.
- **TimeHistory with no Task event.** PackCollection only collects when its event fires; if you don't trigger it, the TimeHistory output is empty.

## Tools

- `mcp__geos-rag__search_schema` — for PeriodicEvent / SoloEvent / HaltEvent attribute names.
- `mcp__geos-rag__search_technical` — for example Events blocks for the specific physics. Patterns vary across single-step quasi-static, multi-step transient, and event-driven simulations.

## Authoritative sources

- Schema slice: `/plugins/orchestrator/schema_slices/events.xsd`.
- Full doc: `/geos_lib/src/coreComponents/events/docs/EventManager.rst`.
