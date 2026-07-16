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

## Current Systems (as of July 16, 2026 — Day 35)

**Always verify these against the live cluster at session start (Step 3 above).**

**IMPORTANT — Beagle3 is now the primary cluster for all 5 production/equilibration systems.**
Direct Beagle3 access (`ssh beagle3`, same ControlMaster pattern as `midway3`) was granted July 8 and
compute submission rights (`beagle3-exusers` account) confirmed shortly after — the earlier "staged,
awaiting resubmission by Kaylie" workflow described later in this section is now **obsolete**; do not
follow it. `/project2/haddadian` (shared Lustre storage) is directly readable/writable from both
Midway3 and Beagle3 login nodes — no need to bounce through Midway3 for cross-cluster file checks.

### The 5 systems

| Name | Protein content | Lipid composition | Status (July 16) |
|---|---|---|---|
| `control` | none (membrane-only baseline) | Composition #1 | Production, 37.53 ns cumulative |
| `dome-model` | dome only (24 HflK/HflC chains, no FtsH) | Composition #1 | Production, 8.05 ns cumulative |
| `dome-bact` | dome only | Composition #2 | Equilibrating (step6.5 of 6) |
| `full-model` | full dome + FtsH | Composition #1 | Equilibration COMPLETE, production not yet started |
| `full-bact` | full dome + FtsH | Composition #2 | Equilibrating (step6.5 of 6) |

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
- `full-model` — still `/project2/haddadian/junseo/beagle3-jobs/full_equil/` (move deferred, same reason — equilibration just finished, production not started yet)

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
- **Production config for all 5 systems**: NAMD 3.0.1, GPU-resident mode (`CUDASOAintegrate on`), non-HMR (standard PSF, 2fs, standard piston 50/25fs), 2 GPU / 16 PE, A100-pinned.
- **Equilibration config for all 5 systems** (different from production — proven-robust, not speed-optimized): NAMD 3.0.1, 1 GPU, **offload mode** (`CUDASOAintegrate off`) — resident mode can't survive the harsh minimize→velocity-reassignment transition at step6.1, but is fine for production once already-equilibrated.
- **CHARMM-GUI gotcha, every fresh download**: `CUDASOAintegrate` is missing entirely by default from step6.x/step7_production.inp — must be patched in manually (insert before `rigidBonds all`) or GPU mode silently falls back to something else.

### Production chunk size: 1 ns blocks

Matches Rajiv's own original convention (`step7_1`, `step7_2`, ... in `/project2/haddadian/rajiv/namd/`
— he later scaled up to 10ns+ blocks once established, but 1ns was his starting point). Chunk size
doesn't meaningfully affect throughput (NAMD's per-step cost is independent of block length; the fixed
toppar-parsing startup overhead is <1% of even a 1ns block's runtime) — the only real tradeoff is more
frequent manual resubmission, since nothing auto-chains yet. `run_prod_gpu.sh`'s `BLOCK_STEPS=500000`
in both `control_prod/` and `domeonly_equil/`.

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
(`control_apl_voronoi_35ns.py`, on Midway3 in `26summer-research/analysis/`) should be reused
unchanged for the other 4 systems for a fair comparison, not reimplemented per-system.

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
