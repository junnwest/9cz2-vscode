# Systems

All actual simulation files live on Midway3 at `/scratch/midway3/junseo/26summer-research/`.
This directory tracks metadata and notes about each system — not the files themselves.

---

## The 5 current systems (as of July 16, 2026)

Superseded the `control` (partial) + `main` (planned) + `dome-only` (AF2-based, abandoned) entries
below — AF2 dome-24 failed outright (14-day TIMEOUT, no model ever produced) and was replaced by
the AF3 ic-minimized pipeline. Full detail, statuses, and paths now live in CLAUDE.md's
"Current Systems" section (kept there instead of duplicated here, since it needs to stay in sync
with the live cluster each session). Quick reference:

| Name | Protein | Lipid comp | 
|---|---|---|
| `control` | none | #1 (generic model) |
| `dome-model` | dome only | #1 |
| `dome-bact` | dome only | #2 (bacterial/cardiolipin-microdomain) |
| `full-model` | dome + FtsH | #1 |
| `full-bact` | dome + FtsH | #2 |

All 5 use NAMD 3.0.1 (not the 2.14 CPU-MPI version this file previously described for `control` —
that was retired mid-project once GPU-resident NAMD 3.0.1 was benchmarked as decisively faster).

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
