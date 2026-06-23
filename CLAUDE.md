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

#### If hostname is `DESKTOP-P24OLOH` — Personal machine (Windows 11, set up June 21, 2026)

**CRITICAL — SSH must go through WSL on this machine, NOT Windows-native ssh.**

Windows OpenSSH (both PowerShell's native build and Git-Bash/MSYS) **cannot maintain
ControlMaster socket multiplexing** — every attempt fails with `getsockname failed: Not a
socket` or `read from master failed: Connection reset by peer`. Since RCC/Midway3 **requires
password+DUO on every fresh connection** (public-key auth is NOT accepted), the persistent
socket is the *only* way to avoid re-DUOing every command — and the Bash tool (non-interactive)
cannot answer DUO prompts. Therefore all Midway3 access is routed through **WSL2 Ubuntu**, which
has real Linux OpenSSH (9.6p1) that supports ControlMaster sockets, exactly like the lab Mac.

Key paths on this machine:
| Resource | Path |
|----------|------|
| Repo | `c:\Users\Kenneth\Desktop\UChicago\Research\9cz2-vscode` |
| Claude Code Bash tool | Git-Bash / MSYS (`/usr/bin/ssh` here CANNOT multiplex — do not use for Midway3) |
| WSL distro | `Ubuntu` (WSL2; logs in as **root**, `HOME=/root`) |
| WSL SSH config | `/root/.ssh/config` (has `ControlMaster auto` / `ControlPath ~/.ssh/cm-%r@%h:%p` / `ControlPersist 1h`) |
| Windows SSH config | `C:\Users\Kenneth\.ssh\config` (plain, NO ControlMaster — native ssh chokes on it) |
| Midway3 socket | `/root/.ssh/cm-junseo@midway3.rcc.uchicago.edu:22` (inside WSL) |
| Deploy key | Not needed for Midway3 (RCC ignores pubkeys); GitHub deploy key only relevant for pushing |

**Session connection flow on this machine:**
1. **User** opens a terminal, runs `wsl` to enter Ubuntu, then `ssh midway3`, completes
   password+DUO once, and **leaves the WSL window open** (keeps the WSL instance + socket alive).
2. **Claude** routes every Midway3 command through that socket:
   ```bash
   wsl.exe -d Ubuntu -- bash -lc 'ssh midway3 "<remote command>"'
   ```
   (Pipe through `| grep -v getpwuid` to drop the harmless WSL uid-mapping warning.)
3. Verify with: `wsl.exe -d Ubuntu -- bash -lc 'ssh -o BatchMode=yes midway3 "echo OK"'` — if it
   prints `OK` with no DUO, the socket is live. If it errors, ask the user to redo step 1.

> **Note for Step 1 / Step 2 below:** on THIS machine, substitute the plain `ssh midway3` in
> those steps with the `wsl.exe -d Ubuntu -- bash -lc 'ssh midway3 "..."'` form above. The
> ControlMaster socket lives inside WSL, not on the Windows side.

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

### AlphaFold Run — HflK Monomer (completed June 17, 2026)
- **Script**: job on Midway3 A100 GPU, job ID 50799910; output at `af2_hflk_mono_output/`
- **Input**: HflK full sequence (1–419 aa); custom template = `hflk_fullmin_chain_a.pdb` (Rajiv's resolved chain A, segname AP1, resid 79–355)
- **Output**: `ranked_0.pdb` — locally at `hflk_mono_ranked_0.pdb` (504 KB)
- **pLDDT per region**: TM (1–78) = 44.8, resolved (79–355) = 90.3, M3 tail (356–419) = 44.5
- **Interpretation**: Low pLDDT on M3 reflects intrinsic disorder, not wrong secondary structure; high confidence on resolved region validates the custom template approach

### AlphaFold Run — Dome-24 (RUNNING on 1.5 TB node, job 50972223, since June 21, 2026)
- **Active script**: `job_dome24_model1_1536g.sh` — **job 50972223**, RUNNING on `midway3-0318` since June 21 19:03 CDT
- **Input**: `dome_24chain_input.fasta` — 24 chains alternating HflK/HflC (A–X), full sequences (419 aa HflK, 334 aa HflC); 9,036 residues total
- **MSA**: precomputed from 13-chain run (`--use_precomputed_msas=True`); only 2 unique sequences so A/ and B/ dirs cover all 24 chains
- **Template**: `--max_template_date=2026-06-10` — includes 9cz2 as structural template; known regions are templated, gap regions predicted
- **Goal**: Fill in all three missing regions with full dome context: HflK M3 (356–419), HflC 161–190, lower halves of chains X/V/W
- **Model**: model_1_multimer_v3 only (`run_af2_model1_only.py`); `models_to_relax=none`
- **MEMORY — KEY LESSON**: RSS footprint is steady **~589 GB**, with peak exceeding 750 GB → **MUST run on the 1.5 TB node `midway3-0318`** (pin with `#SBATCH --nodelist=midway3-0318`). The 768 GB node (`midway3-0317`) OOM-kills it.
- **Partition/QOS**: bigmem partition has only 2 nodes (0317=768 GB, 0318=1.5 TB). `bigmem` QOS `MaxWall = 36h` (hard cap; a 4-day request is rejected `QOSMaxWallDurationPerJobLimit`). `bigmem-pr+` QOS allows 4 days but pi-haddadian access unconfirmed.
- **Failure history** (all produced NO model output):
  - 50698644 — 750 GB → OUT_OF_MEMORY (Jun 12)
  - 50737753 — 1.5 TB (0318) → ran model_1 ~29.5h, **manually cancelled** Jun 18 (not OOM, not finished)
  - 50894863 — 750 GB (0317) → OUT_OF_MEMORY Jun 19, exit 137 (this script lacked `--nodelist` → wrong node)
- **Walltime (resolved June 22)**: prior 1.5 TB run was >29.5h and unfinished, and **AF2 inference does NOT checkpoint** → a timeout = total loss. After the RCC request, job 50972223 now runs under a **4-day wall time** (no longer at the 36h `bigmem` cap) — not at risk as of June 22 (26h+ elapsed, features.pkl complete, no PDB models yet).
- **Fallback (ready)**: `hflk_af2_m3rotated.pdb` + `replace_hflk.py` if dome-24 fails.
- **Post-run plan**: Use best-ranked model output directly as input to CHARMM-GUI for dome-only membrane system; discard HflK M1/M2 (1–78) predictions as TM region is unreliable without membrane context

### Monomer M3 Approach — Attempted and Abandoned (June 16–17, 2026)
Tried using `hflk_mono_ranked_0.pdb` to add M3 tails to all 12 HflK chains in `9cz2minimized_ftsh_fixed.pdb`:
1. Superimposed AF2 monomer onto each HflK chain (CA resid 79–355), extracted M3 (356–419): `scripts/superimpose_hflk_m3.tcl`
2. Rotated each M3 tail in 15° steps about the CA(355)→CA(356) bond axis to minimize CA-CA clashes: `scripts/declash_m3.tcl` (Rodrigues rotation, VMD batch mode)
3. **Result**: Min CA-CA = 0.83 Å (down from 0.65 Å), min all-atom = 0.17 Å, 2,191 all-atom clashes < 1.5 Å — unacceptably severe
4. **Fatal flaw**: Rotation was clash-driven with no dome geometry awareness; several M3 tails oriented outward (away from dome interior) rather than inward — structurally wrong
- **Decision**: Abandoned in favor of (a) the AF3-monomer M3 graft + 2D dihedral declash → NAMD minimization pipeline (Day 15, `scripts/minimize_m3/`), and (b) the dome-24 multimer run which predicts all 24 M3 tails simultaneously in dome context → correct inward orientation guaranteed by multimer modeling

### Output of structure preparation
- `9cz2minimized_08jun_01.pdb` — Rajiv's complete structure (no water); at root of `26summer-research/`
- `9cz2_tm_centered_for_charmmgui.pdb` — z-translated by 56.4 Å (corrected membrane position); used for original (broken) CHARMM-GUI session 8095657229
- `9cz2minimized_08jun_01_ftsh_fixed.pdb` — **corrected CHARMM-GUI input** (local copy in repo root); FtsH TM chain IDs A–J renamed to digits 1–9/0 and segment IDs AP2–JP2 → 1P2–0P2 to resolve chain ID collision; all 36 segments (PROA–PRAJ) now imported correctly; z-translation +56.4 + 30 applied in CHARMM-GUI step 2; **chain assignments**: HflK = A,C,E,G,I,K,M,O,Q,S,U,X (start res 79); HflC = B,D,F,H,J,L,N,P,R,T,V,W (start res 1); FtsH = 0-9,Y,Z (start res 31)
- `9cz2_dome_original.pdb` — dome-only (24 HflK/HflC chains, no FtsH), extracted from vanilla 9CZ2.cif, zero-occupancy atoms filtered out; HflC starts at res 18, HflK at res 79; visual reference only (NOT for pipeline input — lacks Rajiv's AF2-filled regions)
- `hflk_mono_ranked_0.pdb` — AF2 HflK monomer best model (504 KB); resid 1–419; local copy
- `hflk_fullmin_chain_a.pdb` — Rajiv's resolved HflK chain A (segname AP1, resid 79–355); extracted from `9cz2minimized_ftsh_fixed.pdb`; used as custom AF2 template

### Chain ID / Segname mapping in ftsh_fixed.pdb
- **HflK chains**: A, C, E, G, I, K, M, O, Q, S, U, X → segnames AP1, CP1, EP1, GP1, IP1, KP1, MP1, OP1, QP1, SP1, UP1, XP1
- **HflC chains**: B, D, F, H, J, L, N, P, R, T, V, W → segnames BP1, DP1, FP1, HP1, JP1, LP1, NP1, PP1, RP1, TP1, VP1, WP1
- **FtsH chains**: Y, Z (soluble, segnames YP1, ZP1) + 0–9 (TM, segnames 0P2–9P2)
- Always use segname for selection — chain IDs are less reliable

### HflK M3 Rotation (June 18, 2026)
**Problem**: AF2 HflK monomer (ranked_0.pdb, trimmed to res 79–419) has M3 (356–419) predicted without dome context, causing clashes when superimposed onto the dome.

**Approach**: Rigid-body 2D rotation search of M3 around the 355/356 hinge:
- Spin axis: chain direction (centroid of CA 348–355 → centroid of CA 356–363)
- Tilt axis: perpendicular to spin axis, projected against global Z
- Pivot: Cα of residue 355
- Grid: spin 0–355° (5° step) × tilt ±60° (5° step) = 1800 combinations
- Clash metric: heavy atoms within 2.0 Å of non-HflK atoms after Kabsch superimposition onto all 12 chains

**Result**: spin 80°, tilt +60° → **1 total clash across all 12 chains** (vs. 338 at original position)
- Output: `hflk_af2_m3rotated.pdb` (res 79–419, M3 repositioned, in original AF2 coordinate frame)
- Scripts: `find_m3_rotation.py` (rotation search), `replace_hflk.py` (replace 12 HflK chains in dome)

**Next step**: Visual check in Chimera (superimpose onto dome), then run `replace_hflk.py` to build the full dome structure, then NAMD minimization → CHARMM-GUI → equilibration → NPT.

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

## Current Systems (as of June 22, 2026 — Day 15)

**Always verify these against the live cluster at session start (Step 3 above).**

### M3 Grafted Dome — NAMD Minimization (ACTIVE)
- **Input**: `dome_m3_rotated.pdb` — Rajiv's dome + AF3 HflK M3 tails (356–419) grafted onto all 12 HflK chains; junction gaps closed; 2D omega/phi rotation search (2° steps) with inward constraint applied
- **Clash summary**: 0 severe clashes on chains Q, S; 1–13 on remaining chains
- **Minimization**: `minimize_m3/` pipeline — solvated (1,452,343 atoms, 284.5 × 272.5 × 197.5 Å, water only, no membrane); M3 free (B=0), dome restrained (B=500)
- **Current job**: **51015689** PENDING on Midway3 (4 caslake nodes, 4h)
- **Output**: `minimize_m3/dome_m3_minimized.*` (not yet produced)
- **Python environment**: `~/mda_env` on Midway3 (MDAnalysis 2.7.0, membrane-curvature, matplotlib)
- **Note**: NAMD parameter files must use `namd/toppar/` (CHARMM-GUI preprocessed), NOT root `toppar/` (raw CHARMM with scripting). Full parameter set from step6.1 required to cover all cross-referenced atom types (e.g. ON3 from toppar_water_ions.str needs par_all36_na.prm).
- **Long-term solution**: AF2 dome-24 job 50972223 (see below) — predicts all M3 tails in dome context from scratch; use its ranked_0.pdb instead of the grafted structure once available

### Dome-Only MD System — PRIMARY (pending AF2)
- **Input**: Best-ranked AF2 dome-24 output model (job **50972223**, RUNNING on Midway3 bigmem)
- **Chains**: 24 HflK/HflC, no FtsH; HflK resid 1–78 trimmed before CHARMM-GUI
- **AF2 status**: 26h+ elapsed as of June 22; features.pkl complete (454 MB); no PDB models yet; 4-day wall time (not at risk); running on midway3-0318
- **Pipeline**: AF2 output → trim HflK 1–78 → verify M3 inward orientation → CHARMM-GUI membrane build → equilibration → production
- **Rationale**: Dome-only is sufficient to study opening mechanism; FtsH excluded to reduce cost and because it does not drive dome asymmetry
- **M3 rotation fallback**: `hflk_af2_m3rotated.pdb` (res 79–419) was computed June 18 with 1 clash across 12 chains; if dome-24 fails, assemble full dome with `replace_hflk.py` then minimise before CHARMM-GUI

### Main System — 9cz2 full dome + membrane (equilibration queued)
- **Path**: `/scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/namd/`
- **Input**: `9cz2minimized_08jun_01_ftsh_fixed.pdb` (z-translated +56.4 + 30 in CHARMM-GUI step 2)
- **CHARMM-GUI session**: 8119908655 — all 36 chains selected (PROA–PRAJ); completed June 14, 2026
- **System size**: 1,733,042 atoms (full protein + membrane + water/ions)
- **Status**: Equilibration **PENDING** — SLURM job 50776983, 6 nodes, 36h wall time; also staged for Beagle3 GPU (see below)
  - step6.1–6.3: 125,000 steps (0.25 ns each); step6.4–6.6: 250,000 steps (0.5 ns each); total 2.25 ns
- **Pipeline**: ~~CHARMM-GUI build~~ → equilibration (step6.1–6.6) ← **HERE** → production → GaMD

### Control System — Membrane-only baseline
- **Path**: `/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/`
- **PSF**: `step5_input.psf` — 632,689 atoms, lipids only (TLCL1, DPPE, POPG, DOPG, LOACL1 + water/ions)
- **CHARMM-GUI session**: 7628525516, built April 16, 2026
- **Status**: ~31 ns complete — step7_1–21 on Midway3 (21 ns) + step7_22 partial on Beagle3 via Kaylie (~10 ns, job cut by wall time); Midway3 also has an independent step7_22 (~6.5 ns, ignore in favor of Beagle3 version)
- **Performance**: ~4.0 ns/day (4–5 caslake nodes); ~6.7 ns/day on Beagle3 4× A100 (with CUDASOAintegrate off)
- **Analysis completed (June 22)**: Thickness map and mean curvature map over ~31 ns; results at `analysis/control_thickness_31ns.{png,npy}` and `analysis/control_curvature_31ns.{png,npy}`
- **Purpose**: Baseline to isolate membrane effects from protein effects

### Beagle3 GPU Jobs — Staged, Awaiting Resubmission by Kaylie
- **Staging location (Midway3)**: `/project2/haddadian/junseo/beagle3-jobs/`
- **Local scripts**: `scripts/beagle3/` (committed)
- **Lab contact**: Kaylie (has Beagle3 access); submits from Beagle3 scratch

| Job | Staging dir | Status | Issues fixed |
|-----|------------|--------|--------------|
| Main equil (step6.1–6.6) | `beagle3-jobs/main_equil/namd/` | Ready to resubmit | chmod removed from sbatch; `CUDASOAintegrate off` added to all 6 step6 inp files |
| Control prod (step7_22+) | `beagle3-jobs/control_prod/` | Ready to resubmit | chmod removed; `step5_input.str` staged |
| AF2 dome-24 | `beagle3-jobs/af2_dome24/` | Contingency only | Keep Midway3 job 50737753 as primary; Beagle3 if Midway3 fails |

**NAMD3 GPU fix**: All NAMD3 step6 configs have `CUDASOAintegrate off` before `rigidBonds all` — this prevents RATTLE constraint failures from single-precision GPU arithmetic on large systems.

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
│   ├── job_dome24_model1_1536g.sh    # 24-chain dome, model_1 only, pinned to 1.5TB node ← ACTIVE (job 50972223)
│   ├── job_dome24_model1.sh          # same but no nodelist → ran on 768GB node → OOM (job 50894863)
│   ├── job_dome24_1536g.sh           # 1.5TB-pinned (job 50737753, cancelled at ~29.5h)
│   ├── job_dome24_bigmem.sh          # all-5-models bigmem run (job 50698644, OOM)
│   ├── af2_hflc_mono_output/         # HflC monomer prediction output [Rajiv]
│   ├── af2_hflk_mono_output/         # HflK monomer output (job 50799910, complete Jun 17)
│   ├── af2_opening_output_13chain/   # 13-chain MSA output (reused for dome-24)
│   ├── af2_dome24_output/            # Dome-24 output (in progress; only msas/ + features.pkl so far, NO model yet)
│   │   └── dome_24chain_input/       # Model PDBs appear here when complete
│   ├── dome_24chain_input.fasta      # 24-chain HflK/HflC input
│   └── *.fasta                       # Other input sequences
│
├── 9cz2_dome_original.pdb            # Dome-only from vanilla 9CZ2.cif (occ>0, no FtsH) ← AF2 visual ref
│
├── hflk_af2_ranked0_notm.pdb         # AF2 HflK monomer res 79–419 (M1/M2 trimmed)
├── hflk_af2_m3rotated.pdb            # AF2 HflK with M3 rotated (spin 80°, tilt +60°, 1 clash across 12 chains)
│
├── charmm-gui-7628525516/            # CONTROL SYSTEM — membrane-only CHARMM-GUI build
│   ├── step3-5_assembly.*            # Assembly steps
│   ├── step5_input.inp               # NAMD input config template
│   └── namd/                         # ← ACTIVE SIMULATION DIRECTORY
│       ├── step5_input.psf           # 632,689 atoms
│       ├── step5_input.str           # Box dimensions — must be staged alongside PSF
│       ├── step6.1-6.6_equilibration.* # Equilibration (complete)
│       ├── step7_1 through step7_21.*  # 21 ns production (complete)
│       ├── job-submit-step7-cpu.sbatch  # Pending job (50769634, 5 nodes)
│       └── run_prod_cpu.sh           # Loops step7_22+
│
├── charmm-gui-9cz2fulldome-8119908655/  # MAIN SYSTEM — 9cz2 full dome + membrane
│   ├── 9cz2minimized_08jun_01_ftsh_fixed.pdb  # Input PDB (also local repo root)
│   ├── toppar/                       # CHARMM36m force field files (includes top_all36_prot.rtf)
│   └── namd/                         # ← ACTIVE SIMULATION DIRECTORY
│       ├── step5_input.psf           # 1,733,042 atoms
│       ├── step6.1-6.6_equilibration.inp  # Equilibration configs (CUDASOAintegrate off added)
│       └── job-submit-equilibration.sbatch  # Pending job (50776983, 6 nodes)
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

### Beagle3 Staging (on Midway3, shared lab space)
```
/project2/haddadian/junseo/beagle3-jobs/
├── main_equil/namd/          # 9cz2 full dome equilibration (step6.1–6.6), 1,733,042 atoms
│   ├── step5_input.psf/.pdb  # System files
│   ├── step6.1-6.6_*.inp     # All have CUDASOAintegrate off (RATTLE fix for NAMD3 GPU)
│   └── job-submit-beagle3.sbatch  # 4 GPUs, 36h, beagle3-prio
├── control_prod/             # Control membrane production (step7_22+), 632,689 atoms
│   ├── step5_input.psf/.pdb/.str  # System files (str = box dims, was missing → fixed)
│   └── job-submit-beagle3.sbatch  # 4 GPUs, 36h, beagle3-prio
└── af2_dome24/               # Contingency: AF2 dome-24 on Beagle3 bigmem
    ├── dome_24chain_input.fasta
    └── job-submit-beagle3.sbatch
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
