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
- **Status**: step7_1–step7_11 complete (11 ns production); step7_12 PENDING (SLURM job 50623759)
- **Performance**: 2.42 ns/day (4 caslake nodes, ~9.9h per 1 ns iteration)
- **Equilibration**: step6.1–6.6 (CHARMM-GUI standard protocol, all complete)
- **Production**: 1 ns/iteration (500,000 steps × 2 fs), iterated via `run_step7_12_restart_cpu.sh`
- **Key files**:
  - `step5_input.psf` — topology (632,689 atoms)
  - `step7_11.coor/.vel/.xsc` — last completed state
  - `job-submit-step7-12-restart-cpu.sbatch` — current restart job

---

## main — 9cz2 + membrane

- **Input structure**: `9cz2_tm_centered_for_charmmgui.pdb`
  - Derived from `9cz2minimized_08jun_01.pdb` (Rajiv's complete structure)
  - Z-translated 56.4 Å to fix membrane position; additional +30 in CHARMM-GUI step 2
- **Status**: In CHARMM-GUI Membrane Bilayer Builder (as of 2026-06-09); expected to finish 2026-06-10
- **Once done**: New CHARMM-GUI session directory will appear with step5_input.psf/.pdb/.crd
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
