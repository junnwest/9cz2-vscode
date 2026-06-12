# Systems

All actual simulation files live on Midway3 at `/scratch/midway3/junseo/26summer-research/`.
This directory tracks metadata and notes about each system — not the files themselves.

---

## control — Membrane-only baseline

- **Path**: `charmm-gui-7628525516/namd/`
- **Purpose**: Isolate membrane behavior without protein; reference baseline for comparison with full system
- **Membrane**: DPPE 70%, POPG 12.5%, DOPG 12.5%, LOACL1 2.5%, TLCL1 2.5%
- **Atoms**: 632,689 (lipids + water + ions, no protein)
- **CHARMM-GUI session**: 7628525516 (built April 16, 2026)
- **NAMD**: version 2.14 (CPU MPI)
- **Status**: step7_1–step7_12 complete (12 ns production); step7_13–20 running (SLURM 50676351, 5 nodes, 36h); target 20 ns total
- **Performance**: ~4.0 ns/day (4–5 caslake nodes, ~0.043 s/step); earlier 2.42 ns/day figure was from a slower run
- **Equilibration**: step6.1–6.6 (CHARMM-GUI standard protocol, all complete)
- **Production**: 1 ns/iteration (500,000 steps × 2 fs), iterated via `run_step7_13plus_cpu.sh`
- **Key files**:
  - `step5_input.psf` — topology (632,689 atoms)
  - `step7_12.coor/.vel/.xsc` — last completed state
  - `job-submit-step7-13plus-cpu.sbatch` — active job (SLURM 50676351)

---

## main — 9cz2 + membrane

- **Path** (planned): `charmm-gui-9cz2fulldome-8119908655/namd/`
- **Input structure**: `9CZ2/9cz2minimized_08jun_01_ftsh_fixed.pdb`
  - Derived from `9cz2minimized_08jun_01.pdb` (Rajiv's complete structure)
  - FtsH TM chain IDs renamed (A–J → 1–9/0, segment IDs AP2–JP2 → 1P2–0P2) to fix CHARMM-GUI 26-segment cap
  - Z-translated +56.4 + 30 in CHARMM-GUI step 2
- **CHARMM-GUI session**: 8119908655 — all 36 chains selected (PROA–PRAJ); submitted June 11, 2026
  - Previous session 8095657229 was broken: 10 FtsH TM chains silently dropped due to chain ID collision
- **Status**: Building in CHARMM-GUI (as of 2026-06-11); on hold pending AF2 dome-24 result
- **Once done**: Download as NAMD format; scp to `charmm-gui-9cz2fulldome-8119908655/` on Midway3
- **Next**: Conventional MD equilibration (step6.1–6.6) → production step7 → GaMD

---

## RETIRED: no-dome-cpu — 9cz2 without dome (CPU run, Rajiv)

- **Path**: `namd_caslake/`
- **System**: FtsH embedded in membrane, HflK/C dome removed; same membrane composition
- **Purpose**: Benchmark + baseline (test effect of dome on simulation behavior)
- **Production**: step7_2 through step7_11 (10 ns complete)
- **Equilibration**: step6.1–6.6 complete
- **NAMD**: 2.14 CPU MPI, caslake partition
- **Note**: `step5_input.psf` is smaller than control (fewer atoms — no dome means smaller membrane patch)

---

## RETIRED: no-dome-gpu — 9cz2 without dome (GPU run, Rajiv)

- **Path**: `namd/`
- **System**: Same no-dome system as above
- **Purpose**: GPU benchmarking
- **Production**: step7_2, step7_3 (~2 ns)
- **NAMD**: 3.0.1 multicore-cuda

---

## RETIRED: hflc-monomer — Single HflC chain test

- **Path**: `namd-af-singlechain/`
- **System**: Single HflC chain in POPC membrane (simple test composition)
- **Purpose**: Test stability of AlphaFold-generated residues 161–190 in isolation
- **CHARMM-GUI session**: monomer-75-7828079160
- **Production**: None — ran only through step6.4 equilibration
- **Outcome**: AF-generated region appeared stable enough; moved on to full system

---

## RETIRED: full-dome-mini — Clash-resolution minimization (Rajiv)

- **Path**: `full_dome/`
- **System**: Full 9cz2 solvated and ionized (no membrane, pre-CHARMM-GUI)
- **Purpose**: Resolve steric clashes at chain V / chain A interface after chain V rotation
- **Box**: 287.2 × 299.53 × 220.23 Å³
- **Run**: 10,000 minimization steps (timestep 1 fs), NAMD 2.14, 4 caslake nodes
- **Restraints**: chain V res 1–266 + chain A res 266–292 free; everything else fixed (B=500)
- **Output**: `9cz2-mini-final.pdb`
