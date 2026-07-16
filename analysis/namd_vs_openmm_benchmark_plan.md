# NAMD vs. OpenMM Benchmark Plan — dome-only system

**Status**: Planning complete, awaiting data. Not yet executed.
**Trigger**: Dr. Haddadian suggested OpenMM may be faster than NAMD (July 10, 2026 conversation).
**System**: dome-only (24 chains, no FtsH), CHARMM-GUI session 8349249136, 1,742,229 atoms —
same system built two ways: NAMD input (already staged, `domeonly_equil/`) and OpenMM input
(generating via CHARMM-GUI as of July 10).

## Goal

Decide whether to switch the project's production engine from NAMD to OpenMM, based on measured
steady-state throughput on our actual system/hardware — not on published benchmarks for other
systems (see `analysis/` conversation history: public NAMD-vs-OpenMM comparisons are scarce and
none are on our hardware/system).

## Decision metric

**Steady-state ns/day**, not wall-clock-to-completion-including-queue-wait. Production runs last
weeks, so one-time queue wait amortizes away; the number that determines total simulation-days
achievable is the steady-state rate once running.

## Fairness / confound control

1. **Same cluster for both engines.** Run the full sweep (NAMD and OpenMM) on Beagle3, not split
   across Beagle3/Midway3 — avoids conflating a hardware/queue difference with an engine
   difference. (Do NOT reuse the old Midway3 NAMD numbers in `analysis/namd_performance.md` as
   the NAMD side of this comparison — re-measure NAMD on Beagle3.)
2. **Same physics settings.** Cutoff/switching distance, PME grid spacing, constraint algorithm,
   timestep, thermostat/barostat targets and coupling constants must match between the NAMD and
   OpenMM CHARMM-GUI outputs. Diff the two output configs before running anything — CHARMM-GUI
   has been known to pick different defaults per engine.
3. **Benchmark on production-like settings, not early equilibration.** step6.1–6.6 carries
   restraints (positional + colvars) that change progressively across the six steps, so "the
   equilibration rate" isn't one stable number. Benchmark on step7-production-style segments (or
   at minimum step6.6, least-restrained) — that's the number that predicts real wall-clock cost
   over the coming weeks/months.
4. **Exclude warm-up from every timing.** OpenMM JIT-compiles CUDA kernels on first step; NAMD
   has its own startup/autotuning overhead. Fixed protocol: discard first N steps, measure
   steady-state rate over the next M. (Pick N/M once we know typical run length — e.g. discard
   first 2,000–5,000 steps, measure over the following 20,000–50,000.)
5. **Exclusive node access** for every timed run (already the default in our sbatch scripts) —
   no shared-node contention skewing the measurement.

## Resource axes — unconstrained

Per user direction (2026-07-10): GPU count, PE count, and other backend config are NOT held fixed
for fairness — they're free variables each engine gets to optimize over. We only care about the
best number each engine can produce, not what configuration produced it.

- **NAMD**: GPU count (1/2/4), PE count per GPU, `CUDASOAintegrate` on/off. Prior data (Midway3,
  full-dome system) showed 16 PE beating 8 PE by 47%, and 2-GPU only 1.32× over 1-GPU (strong
  diminishing returns) — good starting points, not assumed to hold for this system/cluster.
- **OpenMM**: precision mode (single/mixed), PME parallelization strategy, single-GPU vs.
  multi-GPU-as-independent-replicas (OpenMM's CUDA platform is built around one simulation per
  GPU — splitting one simulation across multiple GPUs is a known-poor use case for it, unlike
  NAMD's native multi-GPU mode). So OpenMM's ">1 GPU" answer is likely "N independent replicas,"
  not "1 sim across N GPUs" — treat as a different axis, not a direct analog to NAMD's GPU count.

## Submission strategy

- Slurm can't resize a running allocation, so each distinct GPU-count variant needs its own
  `sbatch`. Same-GPU-count variants (different PE counts, precision modes) can share one
  allocation and loop through sequentially (like `run_equilibration_gpu.sh` already does).
- Beagle3's `beagle3-prio` queue was 70 jobs deep as of 2026-07-10 (our own job waited ~21h for a
  resubmission with resources technically available). Submit 1-GPU variants first (most likely to
  clear quickly); only submit larger-GPU-count variants once smaller ones show whether they're
  already competitive — no point queuing days for a config that may not matter.

## Correctness check (before trusting any speed number)

At least one config per engine must be sanity-checked against the existing NAMD equilibration
behavior: final temperature/pressure at target, no energy blowup, comparable RMSD/RMSF over the
equilibration window. A faster engine that's silently running different physics isn't a win.

**Open question, check before investing in the full sweep**: does CHARMM-GUI's OpenMM output for
this session reproduce our restraint scheme (colvars file `step5_input.colvar.str` + B-factor
positional restraints) the same way NAMD does? OpenMM doesn't have a native Colvars module the
same way NAMD does (separate `openmm-colvars` plugin, not confirmed installed on Beagle3/Midway3).
No point optimizing speed on a script that can't actually run our restraints.

## Extrapolation methodology (apply once first round of data exists)

Don't take the best-tested point as "optimal" without checking whether the curve has plateaued —
a monotonically-increasing result at the edge of the tested range means the true optimum is
untested, not that the edge value is best.

1. **Fit a saturating curve** to each ordinal/continuous axis (PE count, GPU count — NOT
   categorical knobs like `CUDASOAintegrate on/off` or precision mode, which just get enumerated):
   ```
   rate(N) = R_max * N / (K + N)      # Michaelis-Menten-style saturation
   ```
   via least-squares (`scipy.optimize.curve_fit`) against tested `(N, ns/day)` pairs. Matches the
   project's existing convention in `analysis/namd_performance.md` (control-system fit:
   `ns/day ≈ 1.53 × nodes^0.69`, R²≈0.99).
2. **Stopping rule**: compute marginal gain between the top two tested points,
   `(rate_high - rate_next) / rate_next`. If ≥10%, extend the sweep upward (test the next
   doubling). If <10%, the plateau is real — stop, take the best-tested point.
3. **Hardware ceiling caps extrapolation.** Beagle3 nodes: 32 CPUs / 4 GPUs each. The fit can say
   "still climbing at 32 PEs, worth testing higher" only within a node — crossing to multi-node
   is a different scaling regime (network overhead enters, could reverse gains) and must be
   *tested*, not inferred from the single-node fit.

## Switching threshold

Migrating to OpenMM means rebuilding: restart/checkpoint chaining (no OpenMM equivalent yet of
`run_prod_gpu.sh`'s cumulative-ns ledger), restraint files, and team familiarity with a new
pipeline. Decide the minimum speedup that justifies this cost before seeing the numbers, so the
decision isn't rationalized after the fact. (Threshold not yet set — revisit with Dr. Haddadian
once first-round data exists; earlier public-benchmark research hinted at a possible 4–6× gap,
but that was cross-system/cross-hardware and not to be trusted as-is.)

## Status / next steps

- [ ] OpenMM CHARMM-GUI output — generating (user, in progress as of 2026-07-10)
- [ ] Diff physics settings between NAMD and OpenMM CHARMM-GUI outputs for this session
- [ ] Confirm colvars/restraint reproduction in OpenMM output
- [ ] Re-benchmark NAMD on Beagle3 (do not reuse Midway3 numbers) — 1-GPU variants first
- [ ] Benchmark OpenMM on Beagle3 — 1-GPU variants first
- [ ] Apply extrapolation methodology; extend sweeps where curves haven't plateaued
- [ ] Correctness check on at least one config per engine
- [ ] Set switching threshold with Dr. Haddadian, compare final numbers, decide
