# 9cz2 Research — Session Context

## Project Overview
Summer 2026 research investigating the opening mechanism of the dome structure in the FtsH•HflK/C complex (PDB: 9cz2) in *E. coli*.

**PI**: Dr. Haddadian  
**Predecessor**: Rajiv (Kenneth Yang) — built the complete structure and ran early test systems prior to this summer  
**Start date**: June 8, 2026  
**Cluster**: Midway3 — `/scratch/midway3/junseo/26summer-research/`  
**Note**: Aug 8 – Sep 8, 2026 user is in Korea (remote work only)

## Research Question
What causes the opening of the dome — membrane composition or protease? What is the effect of the dome on the opening?

## Biological Background
9cz2 is the FtsH•HflK/C super-complex — an asymmetric nautilus-shaped assembly where 24 alternating HflK/HflC subunits form a dome around 1–2 FtsH hexamers. The dome has an opening that allows membrane-embedded substrates to enter and be degraded by FtsH.

**Paper 1**: Ghanbarpour et al. (2025), *EMBO Journal* — "An asymmetric nautilus-like HflK/C assembly controls FtsH proteolysis of membrane proteins"
- PDB 9cz2 = primary DDM-extracted map (~4.4 Å resolution, C1 symmetry)
- HflC resolved regions: residues 1–160 and 191–329 (residues 161–190 missing in all HflC chains)
- Chains X, V, W are near the dome opening — their bottom halves are unresolved in 9cz2, likely due to flexibility
- Primary opening ~70–100 Å wide

**Paper 2**: Iqbal, Keller, Ghanbarpour (2025), *biorxiv* — "Structural Plasticity of the Membrane-Bound Protein Degradation Assembly Supports Bacterial Adaptation to Stress"
- Engineered disulfide-crosslinked HflK/C (HflK/C^SS) to stabilize the closed conformation
- Key result: closed conformation significantly impairs bacterial recovery from aminoglycoside (tobramycin) stress → open/flexible state is the biologically active one
- Under tobramycin stress, a NEW conformation appears with TWO openings on opposite sides (~30–50 Å secondary opening near second FtsH hexamer)
- The opening originates from the coiled-coil domain of four HflK/C subunits (chains near the opening)
- Supports the model: conformational flexibility of HflK/C fine-tunes FtsH proteolysis, especially under stress

## Structure Preparation (Done by Rajiv, prior to summer 2026)

Two classes of missing regions were filled before MD:

### 1. HflC residues 161–190 (all HflC chains)
- Generated with AlphaFold and inserted into all HflC subunits

### 2. Chains X, V, W (bottom halves missing)
- These chains sit near the dome opening and are mobile/flexible
- Fixed by copying resolved chains A, B, T respectively, then superimposing via RMSD on the TM helix region (resid 269–348) using VMD
- VMD superimposition script (key parts):
  ```tcl
  # Example for chain X ← chain A
  set ref_AX [atomselect 0 "chain X and name CA and resid 269 to 348"]
  set mob_AX [atomselect 1 "name CA and resid 269 to 348"]
  set M_AX [measure fit $mob_AX $ref_AX]
  set all_AX [atomselect 1 "all"]
  $all_AX move $M_AX
  # Repeated for B→V, T→W
  ```
- Helix structure notes for chain X: resid 248–337 = main helix, 245–247 = 3₁₀ helix, 241–244 = coil
- Active residues used: `resid 1 to 161 or resid 171 to 188 or resid 190 to 334`
- Dihedral angle references: PHI of PRO216 = atoms 3017–3034–3035–3036 (C–N–CA–C); PSI of LEU215 = atoms 3015–3016–3017–3034 (N–CA–C–N)

### AlphaFold Runs (Rajiv)
All AlphaFold scripts at `/scratch/midway3/junseo/26summer-research/alphafold/9cz2/`

- **HflC monomer** (`job3_hflc_mono.sh`): monomer_ptm preset, A100 GPU, 4h; output at `af2_hflc_mono_output/`
- **13-chain opening region** (`job1_msa.sh` + `job2_infer.sh`): AlphaFold2.3.2 multimer, 5 CPU nodes (MSA), then GPU inference
  - Chains: 3 near opening (X=HflK, V=HflC, W=HflC) + 4 flanking (U=HflK, A=HflK, T=HflC, B=HflC) + 12 FtsH = 19 chains
  - `max_template_date=2024-01-01` to exclude 9cz2 from templates (forces de novo prediction of missing regions)
  - Output at `af2_opening_output_13chain/`

### Output of structure preparation
- `9cz2minimized_08jun_01.pdb` — Rajiv's complete structure (no water); at root of `26summer-research/`
- `9cz2_tm_centered_for_charmmgui.pdb` — z-translated by 56.4 Å (corrected membrane position)
  - Further translated z by 30 in CHARMM-GUI step 2

### Rajiv's Pre-production Minimization (`full_dome/`)
Before building the membrane system, Rajiv ran a NAMD minimization to fix steric clashes at the chain V / chain A interface (caused by the chain V rotation during structure building):
- Input: `9cz2-solvated-ionized.pdb/.psf`
- Config: `9cz2-mini.conf`
- 10,000 steps minimization (timestep 1 fs)
- Box: 287.2 × 299.53 × 220.23 Å³
- Restraint strategy: chain V res 1–266 and chain A res 266–292 free to move (B=0); everything else fixed (B=500 in `9cz2-restrain.pdb`)
- Force field: CHARMM36m
- Ran on 4 caslake nodes via `job-submit-9cz2.sbatch`
- Output: `9cz2-mini-final.pdb`

## Simulation Stack

| Component | Tool |
|-----------|------|
| MD engine | NAMD 2.14 (CPU) / NAMD 3.0.1 (GPU) |
| System builder | CHARMM-GUI Membrane Bilayer Builder |
| Enhanced sampling | GaMD (Gaussian Accelerated MD) — planned next |
| Visualization / scripting | VMD |
| Analysis | Python (scripts on Midway3) |
| Cluster | Midway3, caslake partition |

### Membrane Composition
| Lipid  | Fraction |
|--------|----------|
| DPPE   | 70%      |
| POPG   | 12.5%    |
| DOPG   | 12.5%    |
| LOACL1 | 2.5%     |
| TLCL1  | 2.5%     |

### NAMD Production Parameters (all runs)
- Force field: CHARMM36m (`par_all36m_prot.prm`, `par_all36_lipid.prm`, etc.)
- Timestep: 2 fs (`rigidBonds all`)
- Temperature: 303.15 K (Langevin thermostat, damping 1 ps⁻¹)
- Pressure: 1.01325 bar (Langevin piston NPT, period 50 fs, decay 25 fs)
- cutoff: 12 Å, switchdist: 10 Å, pairlistdist: 16 Å
- PME: yes, PMEGridSpacing 1.0 Å
- `wrapAll on`, `useFlexibleCell yes`, `useConstantRatio yes`
- DCD output: every 50,000 steps (100 ps)
- 1 ns per production iteration (500,000 steps)
- Equilibration: CHARMM-GUI standard 6-step protocol (step6.1–step6.6), progressively releasing restraints

### Midway3 Performance (caslake)
Benchmarks from April 2026 are for the **no-dome test system** (retired):
| Config | Speed | Queue wait |
|--------|-------|------------|
| 1 CPU node (48 CPUs) | ~0.9 ns/day | ~4 h |
| 10 CPU nodes (480 CPUs) | ~7.7 ns/day | ~35 h |
| 1 GPU node (4 GPUs) | ~1.55 ns/day | — |

**Control membrane system** (632,689 atoms, no protein):
| Config | Speed |
|--------|-------|
| 4 CPU nodes | 2.42 ns/day (~0.0687 s/step) |

Scaling is ~linear; speedup and wait time roughly cancel for small jobs.

**Optimal node choice**:
- ≤2 ns → 2–4 nodes
- 2–10 ns → 4–6 nodes (best balance)
- ≥10 ns → 8–10 nodes

## Current Systems (as of June 9, 2026 — Day 2)

### Main System — 9cz2 + membrane
- **Input**: `9cz2_tm_centered_for_charmmgui.pdb`
- **Status**: In CHARMM-GUI Membrane Bilayer Builder — expected to finish Day 3 (June 10)
- **Pipeline**: CHARMM-GUI output → conventional MD equilibration → GaMD

### Control System — Membrane-only baseline
- **Path**: `/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/`
- **PSF**: `step5_input.psf` — 632,689 atoms, lipids only (TLCL1, DPPE, POPG, DOPG, LOACL1 + water/ions)
- **CHARMM-GUI session**: 7628525516, built April 16, 2026
- **Status**: step7_1 through step7_11 complete (11 ns production); step7_12 PENDING (4 nodes, 36h, SLURM job 50623759)
- **Performance**: 2.42 ns/day (4 caslake nodes, ~9.9h per ns)
- **Purpose**: Baseline to isolate membrane effects from protein effects

## Midway3 Directory Structure

```
/scratch/midway3/junseo/26summer-research/
├── 9CZ2.cif                          # Original PDB CIF structure
├── 9cz2_cut_open.pdb                 # Intermediate cut structure
├── 9cz2-full-minimized.pdb           # Full minimized structure
├── 9cz2minimized_08jun_01.pdb        # Rajiv's complete structure (no water)
├── step5_assembly.*, step5_input.*   # Root-level CHARMM-GUI files (reference)
├── toppar.str
│
├── alphafold/9cz2/                   # AlphaFold predictions (Rajiv)
│   ├── job1_msa.sh                   # 13-chain MSA (5 CPU nodes, 24h)
│   ├── job2_infer.sh                 # GPU inference
│   ├── job3_hflc_mono.sh             # HflC monomer (A100 GPU, 4h)
│   ├── af2_hflc_mono_output/         # Monomer prediction output
│   ├── af2_opening_output_13chain/   # 13-chain multimer output
│   └── *.fasta                       # Input sequences
│
├── charmm-gui-7628525516/            # CONTROL SYSTEM — membrane-only CHARMM-GUI build
│   ├── step3-5_assembly.*            # Assembly steps
│   ├── step5_input.inp               # NAMD input config template
│   └── namd/                         # ← ACTIVE SIMULATION DIRECTORY
│       ├── step5_input.psf           # 632,689 atoms
│       ├── step6.1-6.6_equilibration.* # Equilibration (complete)
│       ├── step7_1 through step7_11.*  # 11 ns production (complete)
│       ├── job-submit-step7-12-restart-cpu.sbatch  # Pending job
│       └── run_step7_12_restart_cpu.sh
│
├── charmm-gui-monomer-75-7828079160/ # HflC monomer CHARMM-GUI build (POPC membrane)
│
├── control_system/                   # Empty directory (unused)
│
├── full_dome/                        # Rajiv's clash-resolution minimization
│   ├── 9cz2-solvated-ionized.pdb/.psf
│   ├── 9cz2-mini.conf                # 10,000 step minimization
│   ├── 9cz2-restrain.pdb             # B-factor restraint file
│   └── toppar/
│
├── namd/                             # RETIRED: no-dome GPU run (Rajiv)
│   ├── step6.1-6.6 equilibration     # Complete
│   └── step7_2, step7_3             # ~2 ns production
│
├── namd_caslake/                     # RETIRED: no-dome CPU run (Rajiv)
│   ├── step6.1-6.6 equilibration     # Complete
│   └── step7_2 through step7_11     # 10 ns production
│
└── namd-af-singlechain/              # RETIRED: HflC monomer test
    ├── step6.1-6.4 equilibration     # Ran through step6.4 only
    └── restraints/ (POPC membrane)
```

### Retired Systems
| System | Directory | Purpose | Status |
|--------|-----------|---------|--------|
| No-dome 9cz2 (GPU) | `namd/` | Rajiv's no-dome production, GPU | Retired |
| No-dome 9cz2 (CPU) | `namd_caslake/` | Benchmarks + 10 ns production | Retired |
| HflC monomer | `namd-af-singlechain/` | Test stability of AF-generated residues 161-190 in POPC | Retired at step6.4 |

## Analysis Scripts
Rajiv's full analysis scripts directory:
`/project2/haddadian/rajiv/analysis`

Access requires `pi-haddadian` group membership (already set up).

Key script: lipid analysis (select/color lipids around the protein).
- Known issue: wrapping artifacts mess up the center-of-mass calculation
- Fix: unwrap the trajectory before running the script

## Workflow
- All large files (PDB, DCD, PSF, restart) live on Midway3 — do NOT commit them here
- This repo tracks: scripts, configs, analysis notebooks, and progress notes
- Connect to Midway3 via VSCode Remote SSH for live file access
  - Project path: `/scratch/midway3/junseo/26summer-research/`
  - Rajiv's scripts: `/project2/haddadian/rajiv/analysis`
- SSH config uses ControlMaster for DUO-bypass multiplexing (`~/.ssh/config`)
