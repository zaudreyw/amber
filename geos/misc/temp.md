  2. The 17-task subset — what, why, how

  What: Yes, fixed across all my runs. Stored in misc/memory_split.json under key test. 17 of the 35 E03-scored tasks.

  Why: To iterate faster. Running 17 tasks takes ~10-40 min; running 36 takes 60-90. The other 18 are labeled train in the same JSON.

  How selected (not random): From the 35 tasks E03 scored successfully, sorted descending by E03 TreeSim score, then alternating assignment — rank 1 → train, 2 → test, 3 → train, etc. This ensures
  both halves cover the full difficulty range. Train-mean 0.826, test-mean 0.831 — nearly identical, no systematic bias.

  The split was originally built for the memory experiment (train trajectories → build cheatsheet, test tasks → evaluate). Once built I kept using the same 17-test list across all follow-up runs for
   consistent paired comparisons.

  Caveats:
  - If a task wasn't in E03's scored set, it's not in either split. ExampleSPE11b (which timed out in E03) is in neither.
  - Task ExampleThermalLeakyWell IS in my 17-test set but was NOT in Brian's E02 (plug+minimax) run — that's why when I "restrict E02 to the test subset" I get 16/17 not 17/17.

  3. Means exclude unscored tasks — yes

  batch_evaluate.py only writes *_eval.json for tasks that scored successfully (valid XML, gt exists, no scorer exception). My reported means are over whatever *_eval.json files exist. Unscored =
  excluded from the denominator.

  This means runs with more failures look artificially better on "scored mean." The fairer framings I've used:
  - Scored mean — what I usually report. Excludes failures. Use with caution.
  - Paired mean — for comparing two runs, only use tasks both scored successfully. This is what compare_runs.py outputs.
  - Failures-as-zero — include all N tasks in denominator, count unscored as 0. Penalizes runs with more failures. I computed this for E16/E17/E18 earlier.

  4. Why E02 was "restricted to 12 tasks"

  Three-step narrowing (each step smaller):

  Step 0 — E02 (Brian's plug+minimax+v2) full run = 36 tasks, 34 scored successfully (2 failures in Brian's original run), reported mean 0.809.

  Step 1 — Restrict to our 17-test subset: E02 has 16 of those 17 scored (it was missing ExampleThermalLeakyWell — Brian didn't include that task in his run). Mean on those 16: 0.776.

  Step 2 — For paired comparison vs E16 (which failed to score 5 tasks), use only tasks both E02 and E16 scored successfully = 16 (from step 1) intersected with E16's 12 scored = 12 common. E02's
  mean on those 12: 0.793.

  The 12 is the "paired" number — tightest apples-to-apples comparison. The 17 is our "test budget" and the 16 is "what Brian happened to have" and the 12 is "what both had."

  This narrowing matters because if runs have different unscored tasks, comparing their scored-only means is unfair — paired is the defensible framing.


