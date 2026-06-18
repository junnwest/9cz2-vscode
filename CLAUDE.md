# 9cz2 Research — Session Context

---

> **MANDATORY FOR CLAUDE — FIRST ACTION EVERY SESSION, NO EXCEPTIONS:**
> Before responding to ANY user request, complete the SESSION SETUP steps below.
> Do NOT answer questions, run commands, or help with any task until Step 2 (connection verified) is done.

---

## SESSION SETUP — Do This First Every Session

**This section is for Claude to act on immediately when a new session starts.**

### Step 0 — Identify the machine and set up accordingly

Run `hostname` to determine which machine this is, then follow the matching path below.

```bash
hostname
```

---

#### If hostname is `BSCD401-5` — Lab machine (shared, encrypted vault required)

All project files and the deploy key live inside an AES-256 encrypted sparse bundle.
Check if the vault is already mounted:

```bash
ls /Volumes/kenneth 2>/dev/null && echo "MOUNTED" || echo "NOT MOUNTED"
```

If not mounted, **tell the user:**

> Please mount the vault:
> ```
> hdiutil attach ~/kenneth.sparsebundle
> ```
> Enter your password when prompted — it mounts at `/Volumes/kenneth`. Let me know when done.

Key paths on this machine:
| Resource | Path |
|----------|------|
| Repo | `/Volumes/kenneth/9cz2-vscode/` |
| Deploy key | `/Volumes/kenneth/.ssh/9cz2_deploy` |
| SSH config | `~/.ssh/config` |
| git binary | `/Library/Developer/CommandLineTools/usr/bin/git` |
| VSCode folder | `/Volumes/kenneth/9cz2-vscode` |
| Lock vault | `hdiutil detach /Volumes/kenneth` |

---

#### If hostname is `[YOUR-PERSONAL-HOSTNAME]` — Personal machine

> **TODO**: Update this section after setting up the personal device.
> Record: repo path, deploy key path, any machine-specific notes.

Key paths on this machine:
| Resource | Path |
|----------|------|
| Repo | `~/9cz2-vscode/` *(update if different)* |
| Deploy key | `~/.ssh/9cz2_deploy` *(update if different)* |
| SSH config | `~/.ssh/config` |
| VSCode folder | `~/9cz2-vscode` *(update if different)* |

---

### Step 1 — Open the SSH ControlMaster socket (user action required)

The Bash tool reaches Midway3 by tunneling through an SSH ControlMaster socket on the local machine. This socket expires after 1 hour of inactivity. Without it, every `ssh midway3` command will fail with an authentication error.

**Tell the user:**

> Before we can access Midway3, open a local terminal and run:
> ```
> ssh midway3
> ```
> Complete the DUO two-factor authentication prompt. You can then leave that terminal open or close it — the socket persists for 1 hour (`ControlPersist 1h` in `~/.ssh/config`). Let me know when done.

### Step 2 — Verify the connection

Once the user confirms, verify the socket is alive:

```bash
ssh midway3 "echo OK"
```

If it prints `OK` immediately (no DUO prompt), the connection is ready. If it fails or prompts for DUO again, ask the user to re-run `ssh midway3` in their local terminal.

### Step 3 — Run the startup status check

After the connection is confirmed, run these commands and report the results:

```bash
# Active and pending jobs
ssh midway3 "squeue -u junseo --format='%.10i %.12j %.6D %.8T %.10M %.10l %Z'"
```

```bash
# Progress of the control system (Midway3) and Beagle3
ssh midway3 "ls /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_*.coor 2>/dev/null | sort -V | tail -1"
ssh midway3 "ls /project2/haddadian/junseo/beagle3-jobs/control_prod/step7_*.coor 2>/dev/null | sort -V | tail -1"
ssh midway3 "grep 'TIMING' /project2/haddadian/junseo/beagle3-jobs/control_prod/step7_22.out 2>/dev/null | tail -1"
```

```bash
# Progress of the AF2 dome-24 run (check for completed model output files)
ssh midway3 "ls /scratch/midway3/junseo/26summer-research/alphafold/9cz2/af2_dome24_output/dome_24chain_input/*.pdb 2>/dev/null | sort | tail -5"
```

Summarize: which jobs are running/pending, how far the control system has progressed on both Midway3 and Beagle3, and how many AF2 dome-24 models have completed.

Also check Beagle3 jobs (files synced to Midway3 project2):
```bash
# Main 9cz2 equilibration on Beagle3 — check which step6.x completed
ssh midway3 "ls /project2/haddadian/junseo/beagle3-jobs/main_equil/namd/step6.*.dcd 2>/dev/null | sort -V"
# AF2 dome-24 on Beagle3
ssh midway3 "ls /project2/haddadian/junseo/beagle3-jobs/af2_dome24/output/dome_24chain_input/*.pdb 2>/dev/null | sort | tail -5"
```

### What does NOT need per-session setup

- **SSH key** — already installed on Midway3; no password after the ControlMaster socket is open
- **pi-haddadian group** — already a member; `/project2/haddadian/rajiv/analysis` is accessible
- **NAMD modules** — loaded inside SLURM job scripts (`module load namd/2.14`); no manual loading needed
- **Git** — configured locally; Midway3 files are never committed anyway
- **Python** — no analysis environment set up yet; will be needed when analysis work begins (future)
- **VSCode Remote SSH** — optional, for file browsing; also reuses the ControlMaster socket once it's open

## Local Machine Setup (BSCD401-5, lab Mac)

This is a shared lab computer. Project files are stored in an encrypted vault.

- **Vault**: `~/kenneth.sparsebundle` (AES-256, 5 GB sparse bundle)
- **Mount**: `hdiutil attach ~/kenneth.sparsebundle` → `/Volumes/kenneth`
- **Unmount**: `hdiutil detach /Volumes/kenneth`
- **Resize if needed**: `hdiutil resize -size 10g ~/kenneth.sparsebundle`
- **VSCode working folder**: `/Volumes/kenneth/9cz2-vscode`
- **Deploy key**: `/Volumes/kenneth/.ssh/9cz2_deploy` (referenced in `~/.ssh/config`)
- **SSH config**: `~/.ssh/config` (outside vault — contains no secrets, only hostnames/options)
- **git binary**: `/Library/Developer/CommandLineTools/usr/bin/git` (system git blocked by Xcode license; CLT installed as workaround June 18, 2026)

---

## Project Overview

Summer 2026 research investigating the opening mechanism of the dome structure in the FtsH•HflK/C complex (PDB: 9cz2) in *E. coli*.

**PI**: Dr. Haddadian  
**Predecessor**: Rajiv (Kenneth Yang) — built the complete structure and ran early test systems prior to this summer  
**Start date**: June 8, 2026  
**Cluster**: Midway3 — `/scratch/midway3/junseo/26summer-research/`  
**Note**: Aug 8 – Sep 8, 2026 user is in Korea (remote work only, same SSH setup applies)

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
  - MSA stage completed (features.pkl generated); inference OOMed on A100 (~986 GB estimated)
  - Output at `af2_opening_output_13chain/` — MSA dirs A/ (HflK) and B/ (HflC) reused for dome-24 run

### AlphaFold Run — Dome-24 (current, June 10, 2026)
- **Script**: `job_dome24_bigmem.sh` — SLURM job 50698644
- **Partition**: bigmem (1 node, 48 CPUs, 768 GB RAM, no GPU), 36h wall time
- **Input**: `dome_24chain_input.fasta` — 24 chains alternating HflK/HflC (A–X), full sequences (419 aa HflK, 334 aa HflC)
- **MSA**: precomputed from 13-chain run (`--use_precomputed_msas=True`); only 2 unique sequences so A/ and B/ dirs cover all 24 chains
- **Template**: `--max_template_date=2026-06-10` — includes 9cz2 as structural template; known regions are templated, gap regions predicted
- **Goal**: Fill in all three missing regions with full dome context: HflK M3 (356–419), HflC 161–190, lower halves of chains X/V/W
- **Output**: 5 predicted structures (5 model weights × 1 prediction each) at `af2_dome24_output/`
- **Inference**: CPU-only (JAX_PLATFORM_NAME=cpu, XLA 48-core parallel); expected 1–2 models in 36h
- **Post-run plan**: Use best-ranked model output directly as input to CHARMM-GUI for dome-only membrane system; discard HflK M1/M2 (1–78) predictions as TM region is unreliable without membrane context

### Output of structure preparation
- `9cz2minimized_08jun_01.pdb` — Rajiv's complete structure (no water); at root of `26summer-research/`
- `9cz2_tm_centered_for_charmmgui.pdb` — z-translated by 56.4 Å (corrected membrane position); used for original (broken) CHARMM-GUI session 8095657229
- `9cz2minimized_08jun_01_ftsh_fixed.pdb` — **corrected CHARMM-GUI input** (local copy: `9CZ2/`); FtsH TM chain IDs A–J renamed to digits 1–9/0 and segment IDs AP2–JP2 → 1P2–0P2 to resolve chain ID collision; all 36 segments (PROA–PRAJ) now imported correctly; z-translation +56.4 + 30 applied in CHARMM-GUI step 2
- `9cz2_dome_original.pdb` — dome-only (24 HflK/HflC chains, no FtsH), extracted from vanilla 9CZ2.cif, zero-occupancy atoms filtered out; chains A–X (A=HflK, B=HflC alternating); HflC chains start at res 18 (post-TM), HflK chains start at res 79; used for visual inspection and as AF2 template reference

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
| 4 CPU nodes | ~4.0 ns/day (~0.043 s/step) |

*Note: earlier figure was 2.42 ns/day — updated from step7_12 benchmarks (job 50623759, June 10, 2026). Variation likely due to queue/node-load conditions.*

Scaling is ~linear; speedup and wait time roughly cancel for small jobs. Expect slower speeds for the full 9cz2 system (much larger).

**Optimal node choice**:
- ≤2 ns → 2–4 nodes
- 2–10 ns → 4–6 nodes (best balance)
- ≥10 ns → 8–10 nodes

## Current Systems (as of June 11, 2026 — Day 4)

**Always verify these against the live cluster at session start (Step 3 above).**

### Dome-Only MD System — PRIMARY (planned)
- **Input**: Best-ranked AF2 dome-24 output model (job 50698644, pending)
- **Chains**: 24 HflK/HflC, no FtsH; HflK M1/M2 (1–78) trimmed before CHARMM-GUI
- **Status**: Waiting for AF2 run to complete
- **Pipeline**: AF2 output → trim TM region → CHARMM-GUI membrane build → equilibration → production
- **Rationale**: Dome-only is sufficient to study opening mechanism; FtsH excluded to reduce cost and because it does not drive dome asymmetry

### Main System — 9cz2 full dome + membrane (on hold)
- **Path** (planned): `/scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/namd/`
- **Input**: `9CZ2/9cz2minimized_08jun_01_ftsh_fixed.pdb` (z-translated +56.4 + 30 in CHARMM-GUI step 2)
- **CHARMM-GUI session**: 8119908655 — all 36 chains selected (PROA–PRAJ); submitted June 11, 2026
  - Previous session 8095657229 was broken: FtsH chains AP2–JP2 shared chain IDs A–J with dome P1 chains; CHARMM-GUI's 26-segment cap silently dropped the 10 FtsH TM chains; fixed by renaming FtsH chain IDs to digits
- **Status**: On hold pending AF2 dome-24 result; CHARMM-GUI build in progress
- **Pipeline**: CHARMM-GUI NAMD output → equilibration (step6.1–6.6) → production → GaMD

### Control System — Membrane-only baseline
- **Path**: `/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/`
- **PSF**: `step5_input.psf` — 632,689 atoms, lipids only (TLCL1, DPPE, POPG, DOPG, LOACL1 + water/ions)
- **CHARMM-GUI session**: 7628525516, built April 16, 2026
- **Status**: 12 ns complete; step7_13–20 job submitted (SLURM 50676351, 5 nodes, 36h); target 20 ns total
- **Performance**: ~4.0 ns/day (4–5 caslake nodes)
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
├── alphafold/9cz2/                   # AlphaFold predictions
│   ├── job1_msa.sh                   # 13-chain MSA (5 CPU nodes, 24h) [Rajiv]
│   ├── job2_infer.sh                 # GPU inference [Rajiv, OOMed]
│   ├── job3_hflc_mono.sh             # HflC monomer (A100 GPU, 4h) [Rajiv]
│   ├── job_dome24_bigmem.sh          # 24-chain dome run (bigmem, job 50698644) ← ACTIVE
│   ├── af2_hflc_mono_output/         # Monomer prediction output
│   ├── af2_opening_output_13chain/   # 13-chain MSA output (reused for dome-24)
│   ├── af2_dome24_output/            # Dome-24 output (in progress)
│   ├── dome_24chain_input.fasta      # 24-chain HflK/HflC input
│   └── *.fasta                       # Other input sequences
│
├── 9cz2_dome_original.pdb            # Dome-only from vanilla 9CZ2.cif (occ>0, no FtsH) ← AF2 visual ref
│
├── charmm-gui-7628525516/            # CONTROL SYSTEM — membrane-only CHARMM-GUI build
│   ├── step3-5_assembly.*            # Assembly steps
│   ├── step5_input.inp               # NAMD input config template
│   └── namd/                         # ← ACTIVE SIMULATION DIRECTORY
│       ├── step5_input.psf           # 632,689 atoms
│       ├── step6.1-6.6_equilibration.* # Equilibration (complete)
│       ├── step7_1 through step7_12.*  # 12 ns production (complete)
│       ├── job-submit-step7-13plus-cpu.sbatch  # Active job (50676351)
│       └── run_step7_13plus_cpu.sh   # Loops steps 13–20
│
├── charmm-gui-9cz2fulldome-8119908655/  # MAIN SYSTEM — 9cz2 full dome + membrane (on hold, building)
│   └── [to be populated once CHARMM-GUI session 8119908655 completes]
│
│   # NOTE: charmm-gui-9cz2fulldome-8095657229/ was superseded (broken PSF, FtsH chains dropped)
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
- SSH config: `~/.ssh/config` — ControlMaster auto, ControlPersist 1h, ServerAliveInterval 60
