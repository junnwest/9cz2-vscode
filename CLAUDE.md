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

#### If hostname is `Kenneths-MacBook-Pro.local` — Personal machine (macOS, set up July 6, 2026)

No vault, no WSL — this machine has real Linux-compatible OpenSSH natively, so it works the same way as the lab Mac.

Key paths on this machine:
| Resource | Path |
|----------|------|
| Repo | `/Users/junnwest/Desktop/26-summer-research/9cz2-vscode` |
| SSH config | `~/.ssh/config` — has a `Host midway3` entry (`HostName midway3.rcc.uchicago.edu`, `User junseo`, `ControlMaster auto`, `ControlPath ~/.ssh/cm-%r@%h:%p`, `ControlPersist 1h`) |
| GitHub SSH | already working (`~/.ssh/id_ed25519`, `Host github.com` entry); no deploy key needed on this machine |
| git binary | system git at `/usr/bin/git` (no CLT/Xcode license issue here) |
| VSCode Remote-SSH | extension not yet installed — install `ms-vscode-remote.remote-ssh` from the Extensions panel (⇧⌘X); the `code` CLI is not on PATH here |

Session connection flow is the same as the lab Mac: user runs `ssh midway3` in a terminal to open the ControlMaster socket (password + DUO), then Claude's Bash tool reuses that socket via plain `ssh midway3 "<command>"`.

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
ssh midway3 "grep 'TIMING' /project2/haddadian/junseo/beagle3-jobs/control_prod/step7_37.out 2>/dev/null | tail -1"
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
- **Walltime (resolved June 22; extended June 25)**: prior 1.5 TB run was >29.5h and unfinished, and **AF2 inference does NOT checkpoint** → a timeout = total loss. RCC (Dossay Oryspayev) first extended the TimeLimit in place to **4 days** (June 22), then to **14 days** (June 25) on request — hard kill now **~July 5 19:03**. As of June 28 the job is at **~152h elapsed**, healthy (PID 2108493, 806% CPU, 748 GB RSS), monitor `0/1`, only features.pkl written — **still no PDB model**. Runtime now exceeds the optimistic LLM estimate (~125h), approaching mid estimates (~160–200h); pessimistic O(N³) estimate ~380h. Self-imposed decision point: cancel if no output by ~July 1 (day 10).
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

## Current Systems (as of July 17, 2026 — Day 36)

**Always verify these against the live cluster at session start (Step 3 above).**

**IMPORTANT — Beagle3 is now the primary cluster for all 5 production/equilibration systems.**
Direct Beagle3 access (`ssh beagle3`, same ControlMaster pattern as `midway3`) was granted July 8 and
compute submission rights (`beagle3-exusers` account) confirmed shortly after — the earlier "staged,
awaiting resubmission by Kaylie" workflow described later in this section is now **obsolete**; do not
follow it. `/project2/haddadian` (shared Lustre storage) is directly readable/writable from both
Midway3 and Beagle3 login nodes — no need to bounce through Midway3 for cross-cluster file checks.

### The 5 systems

| Name | Protein content | Lipid composition | Status (July 24, session close) |
|---|---|---|---|
| `control` | none (membrane-only baseline) | Composition #1 | Conventional NAMD production (job 52611795, 48h — resubmitted to fix a missing `--constraint=a100`, see job-queue snapshot below) **and** GaMD equilibration (job 52610940, from `step7_21` — see correction below) in parallel |
| `dome-model` | dome only (24 HflK/HflC chains, no FtsH) | Composition #1 | Conventional NAMD production **continuing** (job 52595314, 48h, `TARGET_NS` cap removed July 24) **and** GaMD equilibration (job 52527113) — both running in parallel, not sequential |
| `dome-bact` | dome only | Composition #2 | Same as `dome-model`: conventional NAMD production continuing (job 52595315, 48h) **and** GaMD equilibration (job 52527114) in parallel |
| `full-model` | full dome + FtsH | Composition #1 | Conventional NAMD production (job 52609176, 48h; 1 GPU offload) **and** GaMD equilibration (job 52610941, from `step7_20`) in parallel |
| `full-bact` | full dome + FtsH | Composition #2 | Production continuing (job 52595316, 48h; 10.05 ns cumulative as of session close). **GaMD not yet started** — waiting until it crosses 20 ns |
| `martini-dome` (optional) | dome only CG (24-chain Martini 3 protein) | Real Model composition (DPPE 70/POPG 12.5/DOPG 12.5/TOCL 5 — no longer redistributed, see July 22–24 Martini section) | Equilibrated, production running (job 52594023) |

**CORRECTION (July 24) — the earlier "20 ns cap, conventional MD done, GaMD runs after" framing was
misleading and has been reversed.** `TARGET_NS=20` was never meant to permanently stop conventional NAMD
production for `dome-model`/`dome-bact` — **conventional NAMD and GaMD run as two separate, parallel
tracks for these two systems, not a sequential handoff.** The `TARGET_NS=20` line has been removed from
both systems' `job-submit-beagle3-prod.sbatch`, and continuing production jobs were submitted alongside
their already-queued GaMD equilibration jobs.

**Production now LOOPS within a job (as of July 20).** `run_prod_gpu.sh` was rewritten to run sequential
1 ns chunks until the wall-time allocation is nearly used (or a per-job 12-chunk cap), matching Rajiv's
convention (iterate many ns, processed in 1 ns chunks) — no more per-ns manual resubmits. Per-system knobs
are set via env in each sbatch: `DEVICES` (GPU list) and, historically, `TARGET_NS` — **now removed for
dome-model/dome-bact per the correction above; not used for control/full-model/full-bact.** Still nothing
auto-chains ACROSS jobs — resubmit for another allocation's worth.

**Wall-time convention updated July 24: submit all production jobs at 48h (`2-00:00:00`)**, the actual
QOS maximum (`beagle3-prio` MaxWall, confirmed via `sacctmgr show qos`) — up from the earlier 36h
(`1-12:00:00`) convention. Applies going forward to new submissions; jobs already running at 36h were
left as-is rather than restarted.

**GaMD chosen over coarse-graining as the enhanced-sampling approach** after research (July 17–20): a
Martini AA-protein/CG-membrane hybrid couples the protein–lipid *interface* only at CG resolution (loses
the lipid-specificity our question depends on) and is documented to over-stabilize protein conformational
dynamics — the exact thing we study. See progress log. (The separate, fully-CG `martini-dome` comparison
system above is a different, complementary effort — a speed/sanity check, not this hybrid approach.)

**GaMD technical notes (verified July 22, 2026):**
- **Resident mode is incompatible with GaMD** (tested, job 52473685: NAMD FATAL-errors at startup with `GPUresident is incompatible with... accelMD` and related options). The fast ~8 ns/day resident production is off the table — GaMD structurally requires offload mode.
- **2-GPU offload GaMD benchmark** (job 52473718): 0.0844 s/step = **~2.0 ns/day** (1.28× speedup over 1 GPU). Scaling is moderate (GaMD boost overhead doesn't parallelize as cleanly as plain dynamics), but real.
- **GaMD equilibration timeline for dome systems** (52 ns target): ~26 days wall-clock, running both `dome-model` and `dome-bact` GaMD in parallel on separate 2-GPU allocations.
- **Recommendation**: Launch both dome GaMD runs on 2 GPU / 16 PE offload (Rajiv's templates used 1 GPU; bumping to 2 saves ~one week per system).

**Possible fix for the resident-mode-incompatible-with-GaMD limitation — Dr. Haochuan Chen's NAMD GPU-resident GaMD patch (lead surfaced July 23, 2026):**
- Learned of this via an email thread forwarded by Dr. Haddadian (originally sent to him July 15, thread dated July 2–9) between Prof. Stephen Meredith / Dr. Shirin Ardekani (UChicago, unrelated T-cell-receptor GaMD project) and Arvind Ramanathan / Moeen Meigooni (Argonne National Lab), about running GaMD on ALCF's Polaris/Aurora.
- Per that thread, **Dr. Haochuan Chen** (Beckman Institute, UIUC — NAMD/TCBG developer) has implemented **GPU-resident GaMD support for NAMD**, referenced as merge requests **`!489`** and **`!504`** on `gitlab.com/tcbgUIUC/namd`, described in the thread as "completed and pending review" (not yet in a mainline NAMD release as of early July). Meigooni's email: "since Haochuan says fully GPU-resident GaMD is available, it's likely that NAMD's new GaMD could be on par with OpenMM's GaMD in terms of performance." Dr. Meredith's email adds MR 504 targets **NVIDIA or AMD GPUs** (tested on Polaris) — plausibly buildable on Beagle3's A100s too, since that's the same GPU family (unlike Aurora's Intel GPUs, which the patch does NOT support).
- **Why this matters here**: this is the exact same wall documented above (resident mode FATAL-errors with `accelMD`, job 52473685) — if Chen's patch works and can be applied to a Beagle3 NAMD build, it could recover the ~4× resident-vs-offload speedup seen in this project's non-GaMD benchmarks (offload GaMD is currently ~0.87–2.0 ns/day; resident-mode plain MD reaches ~8 ns/day) for the dome-model/dome-bact GaMD equilibration runs.
- **Status (July 23)**: requested and received `gitlab.com/tcbgUIUC/namd` access, but could not locate MR 489/504 or any related branch/work from Dr. Chen in the repo.
- **RESOLVED (July 24) — built and verified working.** Dr. Chen granted direct GitLab access to the actual branch: `haochuan/gpu_accelmd_2` (commit `ebed67284e6ab8f72dcb6b15bd32ed0117e10193`; reports as **NAMD 3.1alpha4pre**, a dev version, not a tagged release). Cloned to `/scratch/beagle3/junseo/namd-chen-gpuresident/` (private repo — this local checkout is the only copy Beagle3 staff can access, since they don't have GitLab approval themselves).
  - **Build**: Charm++ 8.0.0 (`github.com/charmplusplus/charm` tag v8.0.0) via `./build charm++ multicore-linux-x86_64 --with-production` (cmake/4.3.0 loaded first — without it, `./build` silently falls back to the legacy `buildold` path). TCL 8.6.17 threaded + FFTW from `ks.uiuc.edu/Research/namd/libraries/` — **this branch specifically requires TCL 8.6.x, not the older 8.5.9** some other NAMD builds use (per its own release notes, needed for Colvars/TCL-forces support in GPU-resident mode). NAMD configured via `./config Linux-x86_64-g++ --charm-arch multicore-linux-x86_64 --with-single-node-cuda --cuda-prefix /software/cuda-11.5-el8-x86_64`, built with `make -j16` on a compute node (GPU node, though CUDA compilation itself doesn't strictly need a live GPU). Binary: `/scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3`.
  - **Test result (job 52586965)**: ran the existing GaMD benchmark (`accelMD`+`accelMDG` dual-boost, dome-model system) with `CUDASOAintegrate on` + 16 PE / 2 GPU — completed 5,000 steps cleanly, **no FATAL error** (the exact thing that crashes stock 3.0.1), sane energies. **8.57 ns/day**, vs. ~0.87–0.88 ns/day for the equivalent PE-fixed *offload*-mode benchmark on stock `namd/3.0.1-multicore-cuda` — **~10× speedup**. Would cut the ~26-day GaMD equilibration estimate to a few days.
  - **Email sent to Beagle3 support (July 24)**: requested review/adoption as a supported module, pointing at the local checkout above (not the GitLab URL, since staff don't have access) plus the exact build commands and the benchmark result.
- **Not yet done**: longer validation run (5,000 steps was a smoke test, not a steady-state confirmation) before actually redirecting the real `gamd-dome-model-equil`/`gamd-dome-bact-equil` jobs (52527113/52527114, still PENDING in offload-mode config) to this build.

**Martini CG comparison system** (optional, July 22 decision): full dome-only system (protein AND membrane
both coarse-grained to Martini 3 — not a mixed AA-protein/CG-membrane hybrid; that hybrid approach was
considered and rejected, see GaMD-vs-coarse-graining discussion above) built via `martinize2` + `insane`
(CHARMM-GUI's Martini Bilayer Maker turned out unable to handle a system this size — see full pipeline
under "Martini 3 CG Dome System" below). Rationale: Martini delivers ~50× speedup vs AA (worth a speed
sanity check), but lipid specificity is lost — CG beads represent lipid classes, not individual atoms.
This tradeoff is acceptable for a *comparison* run (does CG dynamics show opening at all?), not a
replacement of the AA results. **Not in the primary analysis path**, but keeps the option open.

**Composition #1** ("generic model"): DPPE 70% / POPG 12.5% / DOPG 12.5% / LOACL1 2.5% / TLCL1 2.5%.
Matches the textbook whole-cell/bulk *E. coli* inner-membrane average (~70-80% PE, ~20-25% PG, ~5% CL)
closely — this was the project's original/default composition before the two-lipid-comp plan existed.

**Composition #2** ("bacterial"/cardiolipin-microdomain): 74% PG (37% POPG + 37% DOPG), 20% cardiolipin
(10% LOACL1 + 10% TLCL1), 6% DPPE. Does NOT match any bulk bacterial membrane average in the
literature — it's the inverse of composition #1 (PG/CL-dominant, PE-depleted). Dr. Haddadian calls
this one "the bacterial lipid," which makes sense under this reading: cardiolipin-enriched
microdomains (CMDs) are a *distinctively bacterial* signature (no eukaryotic membrane looks like
this), concentrate at *E. coli* cell poles/septum, and cardiolipin specifically controls HflK/C's
membrane localization (Escherichia coli SPFH Membrane Microdomain Proteins HflKC paper,
PMC10434171) — composition #2 likely represents the actual local lipid environment HflK/C lives in,
vs. composition #1 being a generic PE-heavy model membrane that happens to use bacterial lipid species.

Both `dome-model`/`full-model` and `dome-bact`/`full-bact` are built from the exact same AF3
ic-minimized protein structure (`dome_m3_af3_ic_minimized_final.pdb` /
`dome_m3_af3_ic_minimized_final_noftsh.pdb`) — confirmed directly, not assumed — so the
composition-#1-vs-#2 comparison isn't confounded by a different protein build.

**Beagle3 paths** (mid-reorganization to `/scratch/beagle3/junseo/`):
- `control` — `/scratch/beagle3/junseo/control/` (moved)
- `dome-bact` — `/scratch/beagle3/junseo/dome-bact/` (built here from the start)
- `full-bact` — `/scratch/beagle3/junseo/full-bact/` (built here from the start)
- `dome-model` — still `/project2/haddadian/junseo/beagle3-jobs/domeonly_equil/` (move deferred — has a live production job; don't rename a directory a running SLURM job has as its WorkDir)
- `full-model` — still `/project2/haddadian/junseo/beagle3-jobs/full_equil/` (move deferred — production being launched here; see first-production-block transition note above)

**Reorg plan refined July 24, 2026** — now scaling to 5 systems × 3 methods (NAMD/GaMD/Martini), so the
target structure is **system-first for NAMD+GaMD** (`{system}/{namd,gamd}/`, since they share large PSF/
PDB/toppar inputs — method-first would mean duplicating or symlinking those) and **method-first only for
Martini** (`martini/{system}/`, since it shares nothing with the AA systems). Same "don't move a directory
a running job has as WorkDir" rule applies throughout. Status: `/scratch/beagle3/junseo/martini/dome-model`
created as a **symlink** to the still-live `martini-dome-cg/` (has job `martini-prod-1` running out of it)
— gives the clean path now with zero risk; swap for a real move once that job finishes. NAMD/GaMD
`{namd,gamd}/` migration not started — `control-prod`/`full-model-prod`/`full-bact-prod` all live as of
this session's close, wait for each to idle before touching its directory.

### Beagle3 job queue snapshot — July 24, 2026, session close (start here next session)

**Morning startup checklist:**
1. `ssh beagle3 "squeue -u junseo"` — compare against the table below.
2. Check `martini-prod-1` (52594023) — was ~10+h into its 12h allocation at session close, should be
   done or very close. Once done, launch the next Martini production block using the fastest *confirmed*
   config, **32 threads / 2 GPU (2,116 ns/day)** — beats the 24t/1gpu config that block actually ran with.
3. Check `full-bact-prod` (52595316) cumulative ns — once it crosses 20 ns, build and submit its GaMD
   equilibration the same way `control`/`full-model` were done today (see Martini/GaMD sections below).
4. Chen's NAMD build (resident-mode GaMD) was only smoke-tested (5,000 steps, ~2 min) — worth a longer
   validation run before trusting it for anything real.
5. `gamd-hmr4fs-2gpu` (from the original 6-job GaMD speed-test sweep) failed early and was never
   diagnosed — minor, still open.

**Running:**
| Job ID | Name | What it is |
|---|---|---|
| 52611795 | control-prod | Normal `control` production, resubmitted 48h — **fixed a missing `--constraint=a100`** in this system's script (only one missing it; every other job pins A100, this one could have silently landed on an A40) |
| 52595314 | dome-model-prod | Normal `dome-model` production, resubmitted 48h, `TARGET_NS=20` cap **removed** (see correction below) |
| 52595315 | dome-bact-prod | Same for `dome-bact` |
| 52595316 | full-bact-prod | Normal `full-bact` production, resubmitted 48h |
| (pending resubmit) | full-model-prod | 52609176 completed/replaced in the course of today's resubmission round — check `squeue` for the current job ID next session |
| 52594023 | martini-prod-1 | Martini CG production, 24 threads/1 GPU (1,934 ns/day) — see checklist item 2 above |
| 52527113 | gamd-dome-model-equil | GaMD equilibration, from `step7_20` restart |
| 52527114 | gamd-dome-bact-equil | GaMD equilibration, from `step7_20` restart |
| 52610940 | gamd-control-equil | **New today** — GaMD equilibration for `control`, branched from `step7_21` (its exact `step7_20` no longer exists after the July 15 rollback incident) |
| 52610941 | gamd-full-model-equil | **New today** — GaMD equilibration for `full-model`, branched from `step7_20` |

**CORRECTION (July 24) — GaMD is not "3 systems," it's expanding to 4 (of 5).** Earlier framing implied
GaMD was dome-model/dome-bact-only by design. Corrected: GaMD equilibration was built and submitted today
for `control` and `full-model` too (both already past 20 ns of conventional production — the prerequisite
before starting GaMD). Only `full-bact` (10.05 ns as of session close) doesn't have GaMD yet, purely
because it hasn't reached 20 ns — not a scope decision. Both new configs fixed a latent bug found while
adapting the `dome-model` template: it had `accelMDGRestart on` with no actual restart file staged (same
missing-`accelMDGRestartFile` class of bug as the earlier GaMD benchmark fix) — set to `off` for these
fresh starts.

**Wall-time convention (July 24): all production submissions now use 48h (`2-00:00:00`)**, the confirmed
`beagle3-prio` QOS maximum — up from the earlier 36h convention. **GaMD equilibration is a deliberate
exception**, still using `beagle3-long` QOS at 96h (`4-00:00:00`) — pre-existing, reasoned choice
(offload-mode GaMD is slow enough that even 96h may not finish one full 45 ns segment).

**PE-fixed NAMD GaMD offload benchmarks — final numbers** (corrected a ps/ns unit error mid-session
before reporting — 2 fs = 0.000002 ns, not 0.002):
| GPUs | s/step | ns/day |
|---|---|---|
| 1 | 0.110 | 1.57 |
| 2 | 0.0625 | 2.77 |
| 3 | 0.0475 | 3.64 |
| 4 | 0.0382 | 4.53 |

Real, meaningful GPU scaling once the `+p4` PE-starvation bug was fixed (1.8×→5.2× over the original
broken 0.878 ns/day flat-line) — resolves the "2-GPU shows no benefit" open question from earlier this
summer, which was itself an artifact of that same bug. Still all *offload* mode (stock NAMD 3.0.1 can't
do resident+GaMD) — Chen's resident-mode build hit 8.57 ns/day in its smoke test, still meaningfully
ahead of even the best offload number here.

**Lesson reinforced again this session**: a job showing `COMPLETED`/exit 0 is not proof it did anything —
check for real output, not just the exit code. Also: don't trust a user's (or your own) assumption about
which jobs are "done"/"running" without checking `squeue`/`sacct` directly — this session caught several
mismatches between assumed and actual job state this way (both directions: assumed-idle jobs that were
actually running, and assumed-running jobs that had actually already completed).

### Martini 3 CG Dome System — Optional Comparison (built July 22–24, 2026 — production running)

**Purpose**: Speed sanity-check on CG dynamics (does dome opening happen at all in Martini?) — complementary
to primary AA-only path, not replacement. ~50× speedup vs AA once past minimization, but lipid specificity
is lost at the CG membrane level. Useful for ruling out "dome doesn't open in any lipid environment," not
for the mechanistic (which-lipids-drive-opening) question.

**CHARMM-GUI's Martini Bilayer Maker turned out not to be usable for this system, and this is a hard
limit, not a bug to work around**: its upload field is explicitly "Upload All-atom PDB File" — there
is no path to hand it an already-converted CG structure. It does the AA→CG conversion itself internally
(calling `martinize2`), and for any system this size (1.7M AA atoms) that internal step re-writes
a PDB that overflows the format's 5-digit atom-serial field (>99,999 atoms → literal `*****` written into
the file → `martinize2` crashes on `int('*****')`). This happens identically whether you upload PDB or
mmCIF, since CHARMM-GUI's backend still funnels through its own internal PDB writer regardless of
upload format. **This is why the actual working pipeline below bypasses CHARMM-GUI's Martini tools
entirely** and does both the AA→CG protein conversion and the membrane-building ourselves.

**The actual reproducible pipeline** (apply this to any future system needing Martini CG conversion):

1. **Get per-chain protein PDBs.** CHARMM-GUI's GROMACS FF-Converter output (a *different, already-working*
   CHARMM-GUI tool — not the Martini Bilayer Maker) writes one PDB per protein segment automatically:
   `<name>_proa.pdb`, `_prob.pdb`, ... one per chain (e.g. `dome_m3_af3_ic_minimized_final_noftsh_proa.pdb`
   through `_prox.pdb` for our 24-chain dome, ~5,300 atoms each — comfortably under any format limit).
   If a system doesn't have these already, split the AA structure into per-chain PDBs manually (VMD
   `[atomselect ... "chain X"]` + `writepdb`, or MDAnalysis) before conversion — **never feed martinize2 a
   whole multi-hundred-thousand-atom system directly**, even via `.gro` (see gotcha below).

2. **Set up a local Docker environment** (avoids all cluster/local pip version-conflict and
   auth issues — see gotchas). Build once:
   ```dockerfile
   FROM continuumio/miniconda3
   RUN pip install polyply vermouth -q
   RUN pip install "git+https://github.com/Tsjerk/Insane.git" -q
   ```
   `docker build -t martinize2-local .` — this image now has both `martinize2` (via vermouth) and
   `insane` (the actual membrane-builder tool; see gotcha — it's a pip-git package, not a loose script).

3. **Convert each chain separately**, looping over all chain PDBs:
   ```bash
   docker run --rm -v <host-dir>:/data -w /data/martini_chains martinize2-local \
     martinize2 -f /data/<chain>.pdb -o chain_X.top -x chain_X_cg.pdb \
       -name chain_X -ff martini3001 -p backbone -maxwarn 100
   ```
   **Must set `-w` (container working directory) to the intended output folder** — `martinize2` writes
   its `.itp` file(s) relative to CWD, not relative to `-o`/`-x`'s path, so without `-w` the `.itp` lands
   inside the ephemeral container and is lost when `--rm` destroys it. `-name chain_X` also controls the
   `.itp` filename (written as `chain_X_0.itp`) — needed for unique per-chain naming.

4. **Combine the 24 CG chain PDBs into one composite structure.** Verified empirically: `martinize2`
   preserves the *original absolute coordinate frame* (checked chain A's first residue CA vs its BB bead
   — matched to within Martini's normal mapping tolerance), so chains can be concatenated directly with
   sequential atom renumbering — no re-superposition needed.

5. **Download the official Martini 3 lipid parameters** — NOT from the generic `marrink-lab/martini-forcefields`
   repo (only has 3 unrelated lipid types). The real, comprehensive lipidome lives at
   `Martini-Force-Field-Initiative/M3-Lipid-Parameters` on GitHub, under `ITPs/`. Files needed:
   - `martini_v3.0.0.itp` — core bead types / nonbonded parameters
   - `martini_v3.0.0_ffbonded_v2.itp` — **easy to forget** — defines the named bond/angle macros
     (`b_PO4_GL_def`, etc.) that the lipid `.itp` files reference; omitting it causes `gmx grompp`
     to fail with "No default Bond types" for every lipid bond
   - `martini_v3.0.0_phospholipids_PE_v2.itp`, `_PG_v2.itp` — headgroup-specific lipid definitions
   - `martini_v3.0.0_solvents_v1.itp` (Martini water, bead name `W`), `martini_v3.0.0_ions_v1.itp` (`NA`/`CL`)

6. **Handle missing lipid types** (check by grepping for `M3.<NAME>` in `insane`'s own
   `lipids.dat` before assuming a lipid is supported):
   - `DPPE` has no Martini-3 shape template in `insane` (`lipids.dat` has DLPE/DUPE/DMPE/POPE/PAPE
     but not the fully-saturated PE). Fixed by copying `M3.DPPG`'s identical saturated C4 tail
     layout and swapping only the headgroup bead (`GL0`→`NH3`) and charge (`-1`→`0`) to match the real
     `martini_v3.0.0_phospholipids_PE_v2.itp` DPPE parameters — fed to `insane` via a custom `-dat` file.
   - **Cardiolipin has no Martini 3 shape template in `insane` at all** (only Martini-2-era `M2.CDL0/1/2`,
     explicitly commented "Warning not the same names is in .itp" in `lipids.dat` — different bead names/
     count than the real M3 `TMCL`/`TOCL` topology, so unusable directly). **Initially (July 22) worked
     around by redistributing the cardiolipin fraction into POPG/DOPG** — since superseded, see below.
   - **RESOLVED (July 23) — built a real custom `M3.TOCL` shape-template entry** in `custom_lipids.dat`
     (under insane's own `[ cardiolipins ]` block, whose 31-slot geometry was adapted directly to `TOCL`'s
     real bead names/charges from `martini_v3.0.0_phospholipids_CL_v2.itp`: `GLC`/`PO41`/`PO42` linking+
     phosphates, `GL11`/`GL21`/`GL12`/`GL22` glycerols, 4× 4-bead monounsaturated tails). Checked the AA
     structure's real tail bond pattern directly (not assumed) to confirm identity: **`LOACL1` = tetraoleoyl
     cardiolipin — exact match to `TOCL`**; **`TLCL1` = tetralinoleoyl (18:2 tails) — no diene Martini 3
     template exists, `TOCL` is the closest available approximation**, used for both per project decision.
     System now built with the **real** Model composition (DPPE 70 / POPG 12.5 / DOPG 12.5 / TOCL 5),
     not the redistributed 70:15:15 stand-in. Verified against the real AA `dome-model` system's actual
     as-built percentages (converting atom counts → molecules via each lipid's real atom count): AA =
     71.43/12.25/12.25/4.08 (DPPE/POPG/DOPG/CL-combined) vs. CG = 70.07/12.48/12.48/4.98 — within ~1.4
     points on every lipid, consistent with ordinary independent-system lipid-count rounding, not a
     composition bug.

7. **Build the full system**:
   ```bash
   insane -f protein_final_corrected.gro -o system.gro -p system.top \
     -dat custom_lipids.dat -pbc rectangular -x <box-x-nm> -y <box-y-nm> -z <box-z-nm> \
     -l DPPE:70 -l POPG:12.5 -l DOPG:12.5 -l TOCL:5 -sol W -salt 0.15 -ff M3 -fudge 0.9
   ```
   Box dimensions should match the original AA system's equilibrated box (read from the NAMD `.xsc`
   restart file, in Å → convert to nm) for a fair comparison. **`-fudge` (default 0.1) and the input
   protein's pre-translation z-position are both critical and non-obvious — see the membrane-position
   and lipid-exclusion fixes below before reusing this command blind.**

8. **Fix the topology's protein section.** `insane` only knows the protein as one opaque input
   structure and writes a placeholder `Protein  1` line — it has no idea our system is actually 24
   separate moleculetypes. Manually replace this with `#include` lines for all 24 chain `.itp` files
   plus 24 `chain_X_0    1` molecule entries, **in the same order the chains were concatenated** (verify
   this against the `.gro` file's atom-count boundaries between chains — residue numbering resets to 1
   at each chain boundary and is a good sanity check).

9. **Validate with `gmx grompp` before trusting anything** — this is what caught the missing
   `ffbonded` file. A clean run (only a performance NOTE about PME mesh load, zero ERRORs) means the
   topology is real and internally consistent.

10. **Run on a compute node, never the login node.** `gmx mdrun` segfaults immediately on Beagle3's
    login nodes (no GPU, and RCC actively discourages compute there) — always submit via `sbatch`,
    even for a quick energy-minimization test.

**Files** (Beagle3 `/scratch/beagle3/junseo/martini-dome-cg/`, local mirror in
`~/Downloads/charmm-gui-8458758786/` on the Mac):
- `dome_martini_system.gro` / `.top` — current system (168,577 CG beads: 18,264 protein / real
  Model lipid mix — DPPE 1999 + POPG 356 + DOPG 356 + TOCL 142 = 2,853 lipids / ~121k water / ~2.7k ions)
- `martini_chains/chain_*_0.itp` — 24 individual protein chain topologies
- `martini_ff/*.itp` — 7 official Martini 3 parameter files (core, ffbonded, PE, PG, **CL**, solvents, ions)
- `custom_lipids.dat` — hand-built `M3.DPPE` and `M3.TOCL` shape-template entries (see above)
- `em.mdp` / `eq.mdp` / `md.mdp` — minimization / equilibration / production configs, **all verified
  against the official Martini 3 tutorial's validated `insane`-workflow example** (cgmartini.nl, KALP
  transmembrane peptide, `KALP_new/KALP-worked/insane/{minimization,equilibration,dynamic}.mdp`) rather
  than written from general knowledge — the first drafts of these files (PME electrostatics, 1.2 nm
  cutoffs, isotropic barostat, single `tc-grps`, Berendsen throughout) were **not** verified this way and
  had to be corrected; reference values: reaction-field electrostatics (`epsilon_r=15`, `epsilon_rf=0`),
  1.1 nm cutoffs, semi-isotropic `c-rescale` (eq) → `parrinello-rahman` (production) barostat, separate
  `Protein_Membrane`/`W_ION` thermostat groups, 20 fs production timestep. Repo copies:
  `scripts/martini_em_template.mdp`, `scripts/martini_eq_template.mdp`, `scripts/martini_md_template.mdp`.
- `index.ndx` — `Protein_Membrane` (groups 1+13+14+15+16) / `W_ION` (17+18) groups for `tc-grps`;
  must be rebuilt (same selection commands, group numbers are stable) any time the lipid/water counts
  change, since it's atom-index-based, not name-based.
- Backups of superseded builds: `broken_build_backup/` (original, membrane-position bug), `redistributed_build_backup/`
  (cardiolipin redistributed into POPG/DOPG), `oversparse_build_backup/` (real TOCL but default `-fudge`,
  badly under-packed), `fudge03_build_backup/` (`-fudge 0.3`, better but one large void remained).

**Confirmed standard practice, not an extra precaution**: checked the official Martini Force Field
Initiative tutorial (cgmartini.nl) rather than assuming — energy minimization immediately after building
a solvated/ionized system (exactly what `insane` produces) is the documented standard workflow
(minimization → NVT/NPT equilibration → production), specifically *because* placing lipids/water/ions
programmatically creates steric clashes that must be relaxed first. This is not specific to our pipeline.

**EM segfault root-caused and fixed (July 22–23) — was a GROMACS build bug, not a topology problem.**
First `sbatch` attempt (job 52534609) segfaulted inside GROMACS's threaded virtual-site construction.
Ruled out an OpenMP threading race by rerunning single-threaded/CPU-only — still segfaulted in the same
place. Actual cause: the loaded module was `gromacs/2022.4-plumed_2.8.1` (PLUMED-patched build touching
vsite/force code paths). **Always use `gromacs/2025.3` for this system, not the default `2022.4`.**

**Membrane-position bug found and fixed (July 23).** Visual inspection in VMD showed the membrane
crossing through roughly the vertical *middle* of the protein, not near the bottom as it should
biologically (dome sits above a thin membrane-spanning anchor). Quantified against the real AA
`dome-model` system: membrane should sit **~60 Å below the protein's center** (verified: real AA system
= 60.5 Å below center); the broken CG build had it at ~50.7% up the protein's z-extent — i.e., dead
center. **Root cause**: the CG pipeline starts from `dome_m3_af3_ic_minimized_final_noftsh.pdb`, which
was *never* assembled with a membrane (no CHARMM-GUI membrane build in its history) — so `insane` had
no way to know where the true anchor point was and centered on the protein's bulk mass instead.
**Fix**: empirically reverse-engineered `insane`'s actual placement behavior (not simple box-centering —
took iterative test runs to characterize), computed the exact z-translation needed for the pre-`insane`
protein input, and enlarged the box in z from 19.487 → 24.0 nm for proper asymmetric padding (thin below
the membrane, generous above the tall dome). Final result: **59.5 Å below center**, matching the 60.5 Å
real-system reference within noise.

**Lipid under-packing bug found and fixed (July 23–24) — `insane`'s `-fudge` exclusion parameter.**
After the position fix, visual inspection (`resname DPPE POPG DOPG TOCL` in VMD) still showed a large
connected void under the dome. Quantified via a pure-numpy connected-component analysis on a binned
headgroup-density grid (PBC-aware flood fill, since `scipy.ndimage` had its own `libstdc++` version
conflict on this node): **one contiguous void of 147.4 nm² (~6.85 nm equivalent radius)** — about 10×
larger than the next-biggest gap, and ~6× larger in area than a single ~1 nm-diameter helical stalk
should cause. Root cause: `insane`'s protein-lipid exclusion (`-fudge`, default `0.1`) marks a grid cell
"occupied" if its local protein-atom density is above 10% of the single most-crowded cell anywhere —
strict enough that a somewhat flexible/wobbly stalk region (this system's M3/anchor region has
documented residual conformational uncertainty — see the AF3/rotation-search work earlier this summer)
produces a gradual density falloff that fails the threshold over a much wider area than the true atomic
footprint. **Fix**: swept `-fudge` from 0.1→0.3→0.6→0.9; void area dropped from 147.4 → 88.9 → 7.1 nm²
(final: several modest ~5–13 nm² regions, no dominant blob — consistent with ~12 separate reasonable
per-stalk exclusions, matching the real ring of HflK anchors). **Final config: `-fudge 0.9`**, area-per-
lipid ≈ 61.8 Ų (real AA reference range: 52–73 Ų depending on lipid type) — verified this is *not* just
"exclusion disabled" (`-fudge 1.0` would fully disable it) but a genuine, checked improvement.
**`-fudge 0.9` should be treated as system-specific**, not a universal default — it compensates for this
particular dome's unusually sparse/asymmetric membrane-crossing footprint; a typical single-TM-helix
system would not need this.

**1,900+ ns/day production speed is real, not a bug** — verified two ways before trusting it: (1)
internal consistency — GROMACS's own per-operation timing breakdown gives 0.894 ms/step, which
algebraically reproduces the reported 1,933.853 ns/day exactly via `86400/step_time × 0.02 ns/step`;
(2) external corroboration — an unrelated, published GROMACS 2024 benchmark (NHR@FAU, A100, 16 threads)
of an all-atom system at almost exactly the same particle count (170,320 atoms) gets **129.09 ns/day**;
our CG system's ~13× speedup over that is fully explained by the 20 fs vs. 2 fs timestep (10×) plus
cheaper reaction-field-vs-PME/no-explicit-H physics (~1.3×) — no unexplained residual. Same source also
independently confirms a general effect we saw ourselves: their similarly-sized "System 3" is flagged as
"too small to saturate" additional compute resources, matching our own finding that 2 GPU (1,708 ns/day)
was *slower* than 1 GPU (1,721 ns/day) at the same thread count — not a fluke, a known small-system effect.
Source: [HPC-Café: GROMACS 2024 usage and performance (NHR@FAU)](https://hpc.fau.de/files/2024/07/2024-07-09_NHR@FAU_HPC-Cafe_Gromacs-Benchmarks.pdf).

**Production speed benchmark results (July 24)** — full cross-product, 5,000-step tests, `-resetstep 1000`:

| Threads | 1 GPU, CPU update | 2 GPU, CPU update | GPU-update (any config) |
|---|---|---|---|
| 4 | 940 ns/day | — | FAILED |
| 8 | 1,360 ns/day | — | FAILED |
| 16 | 1,721 ns/day | 1,708 ns/day | FAILED |
| 24 | 1,934 ns/day | — | — |
| 32 | 1,883 ns/day (slight regression past 24t) | **2,116 ns/day** ← final best | — |

`-update gpu` (full GPU-resident integration, avoiding CPU↔GPU round-trips) **fails outright for this
system** — not a config error, a genuine GROMACS limitation: "Update task can not run on the GPU... Virtual
sites are not supported" — and Martini protein backbones inherently use virtual sites (same feature that
caused the earlier EM segfault investigation). Not worth pursuing further for any Martini system built
this way. Note the non-monotonic pattern: at 16 threads 2 GPU was *slower* than 1 GPU (small-system
under-saturation, externally corroborated below), but at 32 threads 2 GPU pulls decisively ahead —
GPU count and thread count interact, don't assume a conclusion from one thread count generalizes.
**Final best confirmed config: 32 threads, 2 GPU (2,116 ns/day).** `martini-prod-1`'s first block
actually ran with the 24t/1gpu config (1,934 ns/day), since it launched before the 32t/2gpu result came
in — use 32t/2gpu for the *next* continuation block.

**Equilibration (July 24)** — 1 ns (100,000 steps, `dt=0.01`), `-DPOSRES` on protein backbone, single
combined NVT+NPT stage (matches the validated KALP reference's approach directly, rather than the two
ad-hoc NVT-then-NPT stages used in an earlier, unverified attempt). Completed cleanly in 1m43s
(856 ns/day). Frame output (10 ps/frame, `eq.xtc`) checked against Rajiv's own real AA equilibration
convention (`step6.1-6.6_equilibration.inp`, `/project2/haddadian/rajiv/charmm-gui-closed/namd/`) — his
`dcdfreq 5000` gives 5 ps/frame (steps 1fs) transitioning to 10 ps/frame (steps 2fs) — confirms our
spacing is well within his established range, not excessive. Final state: temperature 302.9 K (target
303.15 K, essentially converged); pressure −6.7 bar (target 1 bar, still relaxing — expected, since this
equilibration is the first one to run on the corrected/re-packed membrane, which needs genuine physical
relaxation time, unlike the KALP reference system which had no such disturbance to recover from).

**Production (started July 24, job 52594023, `martini-prod-1`)** — continuing from `eq.gro`/`eq.cpt`,
24 threads / 1 GPU / CPU update, 12h wall-time (`-maxh 11.83`, large `-nsteps` override so wall-time is
the actual limiter), expected **~950 ns** in this first block. Launched with the fastest *confirmed*
config rather than waiting for the two still-pending benchmarks — if a faster config is confirmed next
session, use it for the *next* continuation block (chaining continuation across blocks doesn't require
matching performance settings between blocks, only the physics in the `.mdp`/topology need to stay fixed).

**Next steps**:
1. Check `martini-prod-1` (52594023) status and the two pending benchmark jobs (32 threads, 1 & 2 GPU).
2. Pick the fastest confirmed config for the next continuation block (`grompp -c <last>.gro -t <last>.cpt ...`).
3. VMD visualization: load via `.tpr` for bond connectivity — but this VMD build's native `.tpr` reader
   fails on GROMACS 2025.3's newer binary format (`ERROR) Could not read file ...tpr`). Use the official
   `cg_bonds.tcl` helper instead (bundled in the Martini `LipidsII` tutorial archive, copied to
   `~/Downloads/charmm-gui-8458758786/cg_bonds.tcl`): load the plain `.gro`, then in VMD's Tk Console,
   `source cg_bonds.tcl` → `cg_bonds -top dome_martini_system.top -cutoff 6.2 -topoltype "martini"` —
   reads bonds directly from the `.top`/`.itp` text, no GROMACS install or working `.tpr` reader needed.
4. For New Cartoon rendering: VMD's STRIDE can't recognize Martini backbone beads (no atom literally
   named `CA`), so secondary structure has to be transferred from the original AA per-chain PDBs
   (`dome_m3_af3_ic_minimized_final_noftsh_pro{a..x}.pdb`, uploaded to Beagle3 at
   `/scratch/beagle3/junseo/martini-dome-cg/aa_chains/` for use there too) via a helper script:
   `~/Downloads/charmm-gui-8458758786/transfer_secondary_structure.tcl` — computes real STRIDE on each AA
   chain, maps residue numbering by the per-chain offset (CG resid = AA resid − offset, offset = each
   chain's real first AA resid − 1, computed automatically per chain, not hardcoded), and copies the
   H/E/C labels onto the CG molecule's `structure` field. Requires the CG molecule loaded via `.tpr` (or
   `cg_bonds.tcl`) so VMD's `fragment` index correctly separates the 24 chains (fragments 0–23 = chains
   a–x, in concatenation order). Display-only — never touches any simulation file.
5. Residue numbering gotcha: `martinize2` renumbers every chain starting from 1 (discards real AA
   numbering). Fixed offset per chain = real AA start resid − 1 (e.g. HflK chains: AA 79–419 → CG 1–341,
   offset 78; the M3 tail AA 356–419 → CG resid 278–341). Resid also resets independently for every one
   of the 24 chains, so a bare `resid` selection matches all 24 unless combined with `fragment` or a
   resname-based protein filter (`resname ALA ARG ASN ASP GLN GLU GLY HSD ILE LEU LYS MET PHE PRO SER
   THR TRP TYR VAL`) to exclude water/lipid/ion atoms sharing the same resid range.
6. Ion naming gotcha: `insane` writes both Na⁺ and Cl⁻ under **resname `ION`** (not `NA`/`CL` as residue
   names) — the species is only distinguished by **atom name** (`name NA` / `name CL` within `resname ION`).
   `resname NA CL` matches zero atoms.
7. Lipid headgroup selection: phosphate only (marks the two leaflet planes, what this session's own
   diagnostic scripts used) = `name PO4 PO41 PO42` (unique to lipids, safe alone). Full chemical
   headgroup needs splitting by lipid class since bead names differ: `(resname DPPE and name NH3 PO4)
   or (resname POPG DOPG and name GL0 PO4) or (resname TOCL and name GLC PO41 PO42)` — `GL1`/`GL2`
   (`GL11`/`GL21`/`GL12`/`GL22` for cardiolipin) are the glycerol backbone linking to tails, not headgroup.

### NAMD vs OpenMM — decided (NAMD wins)

A systematic benchmark sweep (~35 configs, on `dome-model`, replicated where results looked
inconsistent) found **NAMD 3.0.1, GPU-resident mode, HMR+4fs, 2 GPU/16 PE, A100-pinned = 16.71
ns/day**, beating the best OpenMM config (8.2.0, plain HMR+4fs, force-switch preserved,
replicated) at 10.91 ns/day by ~53%. Full methodology/results in
`analysis/namd_vs_openmm_benchmark_plan.md` and the session's Claude Artifact chart.
Key findings, all now baked into the production configs below:
- **GPU-model confound**: Beagle3 mixes A100 (nodes 0001-0022) and A40 (nodes 0023-0044); always pin `--constraint=a100`, or results are not comparable.
- **Multi-GPU scaling is non-monotonic**: 2 GPU is the sweet spot; 3-4 GPU regress *below* 1-GPU performance (not fully root-caused; suspected single-GPU PME serialization bottleneck).
- **HMR decision**: HMR (mass repartitioning + 4fs timestep) gives ~2x speedup but measurably compromises kinetic/dynamical properties (diffusion coefficients, anything time-resolved) — structural/thermodynamic properties are fine, but this project's core question touches membrane/lipid dynamics. **Not adopted for production** — `control` and `dome-model` both run non-HMR (2fs, standard piston). Isolated HMR's exact contribution empirically on the identical config: HMR on = 16.71 ns/day, HMR off = 8.23 ns/day, almost entirely from the doubled timestep (per-step wall time nearly identical either way).
- **Production config**: NAMD 3.0.1, non-HMR (standard PSF, 2fs, standard piston 50/25fs), A100-pinned. **Two variants, split by whether the system contains FtsH:**
  - **Dome-only + membrane-only systems** (`control`, `dome-model`, `dome-bact`): GPU-**resident** mode (`CUDASOAintegrate on`), 2 GPU / 16 PE (control: 4 GPU / 32 PE). ~8 ns/day.
  - **FtsH systems** (`full-model`, `full-bact`): GPU-**offload** mode (`CUDASOAintegrate off`), 1 GPU / 8 PE. **Resident mode crashes these** (see transition note below) — offload is the proven-stable fallback, but ~4× slower (~2 ns/day at 1 GPU). A 2-GPU-offload benchmark was submitted July 20 to see if the speed can be recovered.
- **Equilibration config for all 5 systems** (different from production — proven-robust, not speed-optimized): NAMD 3.0.1, 1 GPU, **offload mode** (`CUDASOAintegrate off`) — resident mode can't survive the harsh minimize→velocity-reassignment transition at step6.1, but is fine for production once already-equilibrated.
- **FtsH resident-mode crash → run FtsH systems in OFFLOAD (resolved July 17–20)**: NAMD3 GPU-**resident** production (`CUDASOAintegrate on`) crashes the FtsH systems with `SequencerCUDA: Atoms moving too fast`, and this is NOT fixable with a warm-up. The full diagnostic chain on `full-model`:
  - Plain resident first block (job 52301891) died at **timestep 361**. Suspected a localized FtsH-region strain (the only feature `full-model` has that `dome-model`, which crosses this transition fine in resident, lacks).
  - An offload warm-up (`minimize 5000` + `reinitvels` + 50 ps offload → `step7_0`) helped — the next resident block survived to **timestep 13,758 (~27 ps)** — but then crashed the same way. So it's **not** a simple local clash a minimization fixes.
  - **Offload diagnostic (job 52351830) ran a full 1 ns cleanly.** Offload uses the same forces, so a broken structure would crash it too → the structure is fine; it's a **resident-mode numerical fragility** specific to this large FtsH system. (Context: `full-model` is the first FtsH system run in resident-mode production this summer; the older Midway3 full-dome benchmark that ran resident fine was a *different, pre-AF3* build and only 100 ps.)
  - **Resolution**: FtsH systems (`full-model`, `full-bact`) run production in **offload mode** (`CUDASOAintegrate off`, 1 GPU / 8 PE), ~2 ns/day. The offload warm-up is still used as the first block (`step7_0`) since offload also crosses the equilibration→production transition cleanly. `full-model`'s offload-diagnostic ns was reused as its `step7_1` (not wasted). Dome-only/membrane-only systems keep the faster resident mode.
  - **Open**: whether resident-mode speed (~4× faster) is recoverable for FtsH systems (e.g. via `margin`, timestep, or a NAMD build fix) — not yet investigated; offload is the safe working path meanwhile.
- **CHARMM-GUI gotcha, every fresh download**: `CUDASOAintegrate` is missing entirely by default from step6.x/step7_production.inp — must be patched in manually (insert before `rigidBonds all`) or GPU mode silently falls back to something else.

### Production: 1 ns chunks, looped within a job (updated July 20)

`BLOCK_STEPS=500000` (1 ns) matches Rajiv's convention (`step7_1`, `step7_2`, …). Chunk size doesn't
affect throughput (NAMD's per-step cost is block-length-independent; startup overhead <1% of a 1 ns block).
**As of July 20, `run_prod_gpu.sh` LOOPS these chunks within one job** — it runs sequential 1 ns chunks
until the wall-time allocation is nearly used (measured-chunk-duration check) or a per-job `MAX_CHUNKS=12`
cap, then stops cleanly. This is Rajiv's actual pattern (iterate many ns, processed in 1 ns chunks) and
removes the per-ns manual-resubmit babysitting the earlier single-chunk script required. Still nothing
auto-chains ACROSS jobs — resubmit for another allocation's worth.

Per-system config is set by env vars in each sbatch (not hardcoded in the script), so one `run_prod_gpu.sh`
serves all five:
- `DEVICES` — GPU list for `+devices` (`"0"` 1-GPU offload for FtsH systems, `"0,1"` 2-GPU, `"0,1,2,3"` control's 4-GPU).
- `TARGET_NS` — stop when cumulative reaches this (e.g. `20` for `dome-model`/`dome-bact`; unset = unlimited for the rest).
- Resident vs offload is set by `CUDASOAintegrate` in `step7_production.inp` (on/off), independent of the script.

### Two incidents from July 15-16 — read before touching `run_prod_gpu.sh` again

1. **Data loss on `control`** (fixed): the self-heal step in `run_prod_gpu.sh` (finds "the latest
   completed block" via `ls -t step7_*.restart.coor`) matched a leftover benchmark restart file that
   was still sitting in the live production directory (never archived). Self-heal renamed it onto the
   existing `step7_45.*` filenames with a plain `mv`, silently overwriting and destroying a real 8ns
   block. **Fix deployed** (both `control_prod/run_prod_gpu.sh` and `domeonly_equil/run_prod_gpu.sh`):
   glob tightened to `grep -E '^step7_[0-9]+\.restart\.coor$'` (excludes anything with extra suffix
   text), plus a hard check that refuses to rename onto an existing target instead of overwriting it.
   `control`'s trajectory was rolled back to the last verified-good checkpoint (`step7_37`, 37.53 ns) —
   the corrupted 37.53→45.53 ns window no longer exists in any form.
   **Rule going forward**: archive a system's benchmark files into a sibling `benchmarks_archive/`
   folder *before* production ever starts in that directory, not "later."
2. **Script-overwrite race condition on `dome-model`** (fixed, no data lost): overwriting a
   `run_prod_gpu.sh` file on disk while a *previous* invocation of that same script is still
   mid-execution (paused waiting on a many-hour NAMD run) can corrupt that already-running bash
   process when it resumes reading the file afterward — it may read a mangled mix of old/new content
   and crash. The underlying NAMD run itself is unaffected (separate process, already dispatched) —
   only the bash wrapper's post-run bookkeeping (the ledger append) can fail. If this happens: check
   whether the actual `.out` log shows `End of program` cleanly (if so, the block is real and just
   needs its ledger line added by hand) before assuming data loss.

### M3 Grafted Dome — NAMD Minimization (COMPLETE — ready for CHARMM-GUI)
- **Input**: `dome_m3_rotated.pdb` — Rajiv's dome + AF3 HflK M3 tails (356–419) grafted onto all 12 HflK chains; junction gaps closed; 2D omega/phi rotation search (2° steps) with inward constraint applied
- **Clash summary before minimization**: 0 severe clashes on chains Q, S; 1–13 on remaining chains
- **Minimization pipeline**: `minimize_m3/` — solvated (1,452,343 atoms, 284.5 × 272.5 × 197.5 Å, water only, no membrane); M3 free (B=0), dome restrained (B=10 per Dr. Haddadian); DCD output every 100 steps
- **Versions**:
  - v1 (job 51015689, 4 nodes, B=500): no DCD; outputs at `dome_m3_minimized_v1.*`
  - v2_1n (job 51031241, 1 node, B=500): 11 clashes < 1.5 Å, min dist 1.205 Å
  - **v3 (job 51034782, 2 nodes, B=10)**: CLEAN — 12 contacts all at LEU355 C ↔ ASP356 N peptide bond (correct geometry, not clashes); `dome_m3_minimized_v3.dcd` local
  - v3_1n (job 51034788, 1 node, B=10): completed; outputs at `dome_m3_minimized_v3_1n.*` on Midway3
- **Extracted PDBs (local)**:
  - `dome_m3_minimized_v3_protein.pdb` — full complex (HflK + HflC + FtsH, no water); note: `dome_m3_rotated.pdb` included FtsH
  - `dome_m3_minimized_v3_dome.pdb` — dome-only (126,696 atoms, HflK + HflC only, FtsH stripped)
  - **Caveat**: both have VMD hex atom numbers (>99,999 atoms) — renumber before CHARMM-GUI upload
- **Python environment**: `~/mda_env` on Midway3 (MDAnalysis 2.7.0, membrane-curvature, matplotlib)
- **Note**: NAMD parameter files must use `namd/toppar/` (CHARMM-GUI preprocessed), NOT root `toppar/`. Full parameter set from step6.1 required (e.g. ON3 from toppar_water_ions.str needs par_all36_na.prm).

### AF2 dome-24 — FAILED (job 50972223, TIMEOUT, no model ever produced)
- **Final status**: `sacct` confirms `State=TIMEOUT`, `ExitCode=0:0`, Start 2026-06-21T19:02:58 → End 2026-07-05T19:03:14, Elapsed exactly **14-00:00:16**
- Only `features.pkl` (454 MB) + `msas/` ever written; zero PDB models (unrelaxed/ranked) in `af2_dome24_output/dome_24chain_input/` — total loss of the full 14-day bigmem allocation, as feared (AF2 inference does not checkpoint mid-model)
- stderr shows it began `model_1_multimer_v3_pred_0` inference on June 21 19:12 CDT and never finished a single model in 14 days
- **Superseded** — the AF3 `opt1_extended` → `ic` minimization pipeline below is now the primary path; AF2 dome-24 is a dead end, not being retried

### AF3 M3 Prediction — opt1_extended COMPLETE; ic/op minimizations COMPLETE (July 6–7, 2026)
- **Input** (`server_opt1_extended.json`): HflK 200–419 × 12 + HflC 200–334 × 12 (4,260 tokens); extended into the resolved helical stalk (200–355) to give AF3 directional context so the disordered 356–419 tail wouldn't fold into the dome interior (as happened in an earlier, shorter-query attempt)
- **Template**: left unconstrained (`useStructureTemplate: true`, `maxTemplateDate: 2026-01-01`, no forced 9CZ2). Result: AF3 did **not** pick up 9CZ2 — it templated on **7VHQ/7VHP** (the group's earlier 2021 closed, symmetric cryo-EM structure of the same FtsH-HflK/C complex) and **8Z5G** (related SPFH complex). Confirmed via `_entry.id` in the downloaded template CIFs.
- **Output**: `fold_hflk_m3_opt1_extended/` (5 models, local, untracked) — completed July 6
- **Chain mapping problem**: AF3 predicted 12 sequence-identical HflK copies with no inherent correspondence to physical dome chain positions (A, C, E, G...). Two mapping strategies were built and minimized in parallel on Midway3:
  - `minimize_m3_af3_ic/` — **"interchangeable"**: predicted chains reassigned to whichever dome position they best geometrically fit (job 51481766, 10,000-step NAMD minimization, COMPLETE)
  - `minimize_m3_af3_op/` — **"order-preserving"**: predicted chains kept in AF3's raw output order (job 51481765, COMPLETE)
  - Both solvated (~1.456M atoms), both converged cleanly — **zero M3-vs-dome clashes <2.0 Å** in either variant after minimization (checked directly on final frames, not just log convergence)
- **Chose `ic`**: M3 tail CA-displacement during minimization (a proxy for how good the initial chain assignment was) is lower for `ic` in 10 of 12 chains — overall RMSD 2.19 Å (ic) vs 2.28 Å (op). Final NAMD potential energy was nearly identical between the two (diluted by the huge water box, not a useful discriminator).
- **Local files kept** (root of repo, untracked):
  - `dome_m3_af3_ic_minimized_final.pdb` — full complex, 36 chains (HflK/HflC dome + FtsH), 11 MB
  - `dome_m3_af3_ic_minimized_final_noftsh.pdb` — dome-only, 24 chains (A–X), FtsH stripped, 10 MB
- **Sent to Dr. Ghanbarpour** (July 7–8) with full methodology, including the 9CZ2-vs-7VHQ/7VHP template finding
- **Deleted locally for storage** (still recoverable — `op`/`_solv` variants live on Midway3 under `minimize_m3_af3_ic/` and `minimize_m3_af3_op/`; `dome_m3_rotated.pdb`/`dome_with_m3_grafted.pdb` are in git history): `dome_m3_af3_ic_solv.pdb`, `dome_m3_af3_op_minimized_final.pdb`, `dome_m3_af3_op_solv.pdb`, `dome_m3_rotated.pdb`, `dome_with_m3_grafted.pdb`
- **Next step**: use `dome_m3_af3_ic_minimized_final_noftsh.pdb` as CHARMM-GUI input for the dome-only membrane system (HflK resid 1–78 already excluded from the AF3 query, so no further trimming needed)

**Abandoned branches from this effort**:
- Midway3 local AF3 (job 51372128, HflK 319–419 × 12 + HflC full × 12): superseded by the server `opt1_extended` result before it was needed
- AF3 server `opt2_halfdome` (HflK 79–419 × 6 + HflC 1–334 × 6): not pursued once `opt1_extended` succeeded
- First AF3 server attempt (HflK 319–419 × 12 + HflC 270–334 × 12, short query): M3 tails entangled with dome interior — root cause was insufficient directional context, fixed by extending the query in `opt1_extended`
- **AF3 local gotcha** (for future reference): if `templates` is set in the JSON, `unpairedMsa`/`pairedMsa` must also be set (all-or-nothing rule) — omit all three to let the pipeline search automatically

### GPU Benchmark — Midway3 A100 (partial results)
- **Purpose**: Characterize GPU scaling for 1.7M atom system; informed by Dr. Trung's data (1 GPU + 8 PE = 13 ns/day for 1M atoms on Beagle3 A100; multi-GPU gives no benefit)
- **System**: main 9cz2 full dome + membrane (1,733,042 atoms), from step6.6 restart
- **Config**: 50,000 steps, `CUDASOAintegrate on` (GPU-resident), `namd/3.0.1-multicore-cuda`
- **Scripts**: `charmm-gui-9cz2fulldome-8119908655/namd/benchmark_gpu/`

| Job ID | Config | GPUs | PEs | ns/day | Status |
|--------|--------|------|-----|--------|--------|
| 51044706 | bench_1gpu_8pe | 1 | 8 | ~3.8 | COMPLETE |
| 51044707 | bench_1gpu_16pe | 1 | 16 | ~5.6 | COMPLETE |
| 51044708 | bench_2gpu_16pe | 2 | 16 | ~7.4 | COMPLETE |
| 51044709 | bench_4gpu_32pe | 4 | 32 | — | PENDING |

- 2-GPU only 1.32× faster than 1 GPU — strong diminishing returns (consistent with Dr. Trung)
- 16 PE outperforms 8 PE by 47% — larger system (1.7M vs Trung's 1M) better saturates GPU with more CPU threads

### ThinLinc / VMD visualization — segfault root-caused, workaround in progress (July 7–8, 2026)
- **Symptom**: launching `vmd` in a ThinLinc session on Midway3 segfaults immediately after loading plugins
- **Root cause**: default ThinLinc web URL (`midway3.rcc.uchicago.edu`) load-balances onto a GPU-less login node (landed on login5); VMD falls back to `llvmpipe` software OpenGL (`No CUDA accelerator devices available`), which crashes on this cluster's Mesa/VMD 1.9.4a55 combination
- **Workaround attempted**: `sinteractive -p gpu -G 1 --time 02:00:00 --account=pi-haddadian` — works (grants a GPU node with X11 forwarding set up) but requires a queue wait; Midway2's `sviz` shortcut does not exist on Midway3
- **RCC escalation**: emailed Dossay Oryspayev; he suggested trying login3/login4 directly. Web ThinLinc client can't force this — it reconnects to the existing login5 session regardless of URL, since **the web client has no "end existing session" option** (only the native/standalone ThinLinc client does, via an Options/Advanced checkbox). Native-client test with that checkbox not yet confirmed working.
- **Also emailed Dr. Trung** (same thread as the earlier GPU-scaling question) with the same segfault report
- **Fallback that always works**: download trajectory + install VMD locally (`~/Downloads/vmd2.0.0a7-pre2-macarm.dmg` → installed to `/Applications/VMD 2.0.0a7-pre2.app` on this Mac, July 7) and view natively — best performance, no ThinLinc/GPU-queue dependency; used this path for the ic/op minimization comparison

### Retired / superseded directories — do not use

- `beagle3-jobs/main_equil/` — **stale**, predates the AF3 ic-minimized structure and the direct-Beagle3-access workflow; superseded by `full_equil/` (→ `full-model`). Not cleaned up yet, ignore it.
- The old Midway3-hosted `charmm-gui-9cz2fulldome-8119908655/` and `charmm-gui-7628525516/` (equilibration-era paths for what are now `full-model` and `control`) — superseded by the Beagle3 paths in the table above. `control`'s Midway3-era trajectory (`step7_1`-`step7_21`, 26.4 ns) is still real/valid and is part of its current cumulative total; it's just no longer where *new* production runs happen.
- "Staged, awaiting resubmission by Kaylie" workflow — obsolete since direct Beagle3 compute access was granted (see note at the top of this section).

### `control` analysis

Thickness/curvature/order-parameter/area-per-lipid results live in `analysis/control/<Nns>/<script>/`
(31ns = old baseline before this week's rebuild; 35ns = current, computed on the corrected
post-incident trajectory). See progress log July 15-16 entry for methodology notes (Voronoi APL,
order-parameter alkene-carbon fixes, curvature grid-resolution fix). The Voronoi APL script
(`control_apl_voronoi_35ns.py`, on Midway3 in `26summer-research/analysis/` — **code lives only on
Midway3; the repo tracks just the `.npy`/`.png` outputs** in `analysis/control/35ns/apl/`) should be
reused unchanged for the other 4 systems for a fair comparison, not reimplemented per-system.

**How the Voronoi APL script works** (walked through July 16, for reuse/explanation):
- Per frame, drops **one point per lipid at its whole-molecule center of mass** (projected to XY) —
  not the headgroup P. Headgroup atom (`name P or name P1`) is used *only* to assign leaflet
  membership (via per-frame median headgroup-z split), never as the tessellation point.
- **Cardiolipin (LOACL1/TLCL1) is treated as one lipid = one Voronoi cell** — the `name P or name P1`
  selector deliberately grabs only cardiolipin's `P1` (not `P2`), giving exactly one point per lipid
  (an `assert` enforces this). Consequence: cardiolipin reads ~71–73 Å² (≈2× the ~53–56 Å² of the
  single-phosphate lipids), correct for a dimeric 4-tail lipid counted as one molecule.
- Each leaflet tessellated **separately**; points tiled into a **3×3 periodic supercell** so edge
  cells are bounded under PBC, then only the central copy's cell areas are read (shoelace formula).
- Trajectory = 22 stitched DCDs (Midway3 `step7_1`–`step7_21` + Beagle3 `step7_37`), first **350
  frames = 35 ns** (0.1 ns/frame), the verified-intact post-incident window.
- Results (`control`, 35 ns): combined **54.35 Å²**; DPPE 52.93, POPG 54.60, DOPG 56.34, LOACL1 71.49,
  TLCL1 73.27. Built-in drift check (first vs second half): 55.40 → 53.29 Å² (~2 Å² downward drift).

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
