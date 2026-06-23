# Research Progress Log — 9cz2 FtsH•HflK/C Project

**PI**: Dr. Haddadian  
**Researcher**: Jun-Seo Yang  
**Start date**: June 8, 2026  
**Cluster**: Midway3 (`/scratch/midway3/junseo/26summer-research/`)

---

## June 22, 2026 — Day 15

**M3 tail grafting — AF3 monomer approach**
- Downloaded AF3 HflK monomer prediction (`fold_hflk_full_model_0.cif`) from alphafoldserver.com — residues 79–419 (biological), includes M3 tail (356–419)
- Grafted M3 (356–419) from AF3 onto all 12 HflK chains in Rajiv's dome (`9cz2minimized_08jun_01_ftsh_fixed.pdb`): superimposed AF3 anchor (79–355) onto each chain, extracted M3, appended with renumbered residue IDs
- Output: `dome_with_m3_grafted.pdb` — junction gaps 3.7–19.4 Å (ideal peptide bond = 1.33 Å); clashes 1–130 per chain

**M3 declashing — 2D rotation search**
- Wrote `scripts/rotate_m3_declash.py`: closes C355–N356 junction gap to ideal peptide geometry, sweeps omega × phi dihedrals (2° steps, 180×180 = 32,400 combos per chain) with inward constraint (M3 COM must point toward dome centroid)
- Key fix: resid 355 in Rajiv's dome uses CHARMM C-terminal naming (OT1/OT2 not O) — script updated to fall back to OT1
- Result (`dome_m3_rotated.pdb`): all 12 M3 tails point inward; severe clashes (<1.5 Å) reduced to 0–13 per chain (Q and S: 0; best five chains ≤6)

**NAMD minimization — dome + M3, water only**
- Built minimization pipeline in `scripts/minimize_m3/`:
  - `01_fix_and_split.py` — splits `dome_m3_rotated.pdb` into 36 per-segment PDB files
  - `02_build_psf.tcl` — psfgen with `top_all36_prot.rtf`; 139,776 protein atoms
  - `03_solvate.tcl` — VMD solvate (15 Å) + autoionize (0.15 M NaCl); 1,452,343 atoms total; box 284.516 × 272.457 × 197.517 Å
  - `04_make_restraints.py` — B=0 for M3 (resid 356–419, HflK chains); B=500 for dome + water + ions
  - `05_minimize.conf` — NAMD 2.14, 10,000 steps CG minimization, full CHARMM36m parameter set (matched to step6.1)
  - `06_job_minimize.sbatch` — 4 caslake nodes, 4h
- Repeated failures fixed: missing `exclude scaled1-4`, wrong toppar path (root `toppar/` vs NAMD-compatible `namd/toppar/`), missing `par_all36_na.prm` for ON3 atom type
- Current job: **51015689** (PENDING as of session end)

**Control system analysis**
- Confirmed control system total: 21 ns (Midway3 step7_1–21) + ~10 ns (Beagle3 step7_22 via Kaylie, job cut by wall time) = **~31 ns**
- Set up Python virtualenv `~/mda_env` on Midway3 with MDAnalysis 2.7.0 and membrane-curvature
- Wrote and ran `scripts/analysis/control_thickness.py` and `scripts/analysis/control_curvature.py` on all 31 ns
- Output (downloaded locally to `analysis/`): `control_thickness_31ns.{png,npy}`, `control_curvature_31ns.{png,npy}`
- Analysis job: **51015382** (completed)

**AF2 dome-24 (job 50972223)**
- 26h+ elapsed; features.pkl complete; no PDB models yet (CPU inference still running); 4-day wall time, not at risk

**Emails drafted**
- NAMD mailing list: multi-node GPU feasibility for 1.7M atom system
- Dr. Zand (UChicago): multi-node GPU parallelization question (referred by Dr. Haddadian)
- Rajiv: M3 grafting progress + GaMD script request

---

## June 21–22, 2026 — Day 14

**New personal device set up (Windows 11, `DESKTOP-P24OLOH`)**
- Midway3 SSH must route through **WSL2 Ubuntu**, not Windows-native ssh
  - Windows OpenSSH (PowerShell native + Git-Bash/MSYS) cannot maintain ControlMaster socket multiplexing (`getsockname failed: Not a socket` / `read from master failed: Connection reset by peer`)
  - RCC requires password+DUO on every fresh connection (public-key auth NOT accepted) → the persistent socket is the only way to avoid re-DUOing every command, and the non-interactive Bash tool can't answer DUO
  - WSL2 Ubuntu has real Linux OpenSSH (9.6p1) that supports ControlMaster, like the lab Mac
  - Flow: user runs `wsl` → `ssh midway3` → DUO once (keep window open); Claude routes via `wsl.exe -d Ubuntu -- bash -lc 'ssh midway3 "..."'`. WSL config at `/root/.ssh/config`. Full details in CLAUDE.md.

**AF2 dome-24 — root-caused all prior failures; resubmitted on correct node**
- Discovered **no dome-24 model was ever produced** — `af2_dome24_output/dome_24chain_input/` has only `msas/` + `features.pkl` (June 10); no ranked/unrelaxed PDBs, no result pkls
- Failure history (all attempts):
  | Job | Mem / node | Result |
  |-----|-----------|--------|
  | 50698644 | 750 GB | OUT_OF_MEMORY (Jun 12) |
  | 50737753 | 1.5 TB (node 0318) | ran model_1 ~29.5h, **manually CANCELLED** Jun 18 (not OOM, not finished) |
  | 50894863 | 750 GB (node 0317) | **OUT_OF_MEMORY** Jun 19, exit 137 |
- **Root cause of the OOM:** `job_dome24_model1.sh` had **no `--nodelist`**, so SLURM placed it on `midway3-0317` (768 GB). AF2 RSS for this system is steady **~589 GB**; peak exceeds 750 GB → cgroup OOM-kill. The 1.5 TB run (which pins `--nodelist=midway3-0318`) never OOM'd — it was cancelled, not killed.
- **Fix:** created `job_dome24_model1_1536g.sh` = model_1 script + `#SBATCH --nodelist=midway3-0318` (the only 1.5 TB bigmem node) + log rename. Walltime kept at 36h — `bigmem` QOS `MaxWall = 1-12:00:00` is a hard cap (a 4-day request was rejected `QOSMaxWallDurationPerJobLimit`).
- **Resubmitted: job 50972223** — RUNNING on midway3-0318 (1.5 TB), started Jun 21 19:03 CDT; RSS steady ~589 GB, CPU ~700%, model_1_multimer_v3 only, precomputed MSAs. Will not OOM.
- **Walltime risk (open):** prior 1.5 TB run was >29.5h and unfinished; 36h cap leaves ~6.5h margin, and **AF2 inference does not checkpoint** → a timeout = total loss (no partial output). User is emailing RCC to either **extend the running job 50972223's TimeLimit in place** (`scontrol update job=... TimeLimit=...`, admin-only, preserves progress) or grant access to the **`bigmem-pr+` QOS** (`MaxWall = 4-00:00:00`). Email ideally answered within ~33h.

**bigmem partition facts (verified)**
- Only **2 nodes**: `midway3-0317` (768 GB), `midway3-0318` (1.5 TB)
- `bigmem` QOS: `MaxWall = 36h`, `MaxTRESPU cpu=96`
- `bigmem-pr+` QOS: `MaxWall = 4 days` (access for pi-haddadian unconfirmed)

**System status at session start**
- No jobs running/pending at session start (queue empty)
- Control system: `step7_22.restart.coor` on both Midway3 and Beagle3 (~22 ns) — unchanged since Day 11; jobs not currently running
- Beagle3 main_equil: only `step6.1_equilibration.dcd` present
- HflK monomer AF2 output intact (`af2_hflk_mono_output/`, ranked_0–4)

---

## June 18, 2026 — Day 11

**AF2 dome-24 — job 50737753 cancelled; RCC investigation**
- Job 50737753 was cancelled at 11:33 CDT, cause unknown. It had completed all MSA/template processing and was mid-inference (`model_1_multimer_v3_pred_0`, 9036 residues, 3072 MSA rows) when killed — the most compute-intensive phase.
- Met with RCC staff; they will investigate the cancellation and optimize the script.
- Copied all AF2 files to `/project2/haddadian/junseo/af2_dome24_rcc/` (16 GB) for RCC to access:
  - All job scripts (`job_dome24_bigmem.sh`, `job_dome24_model1.sh`, `run_af2_model1_only.py`, etc.)
  - Error logs from cancelled jobs (50737753, 50698644)
  - Precomputed MSAs (`af2_opening_output_13chain/`, 6.5 GB)
  - Partial output (`af2_dome24_output/`, 1.6 GB)

**New AF2 job 50894863 queued**
- Script: `job_dome24_model1.sh` — runs only `model_1_multimer_v3` via custom Python wrapper `run_af2_model1_only.py`
- Partition: bigmem, 1 node, 48 CPUs, 750 GB RAM, **4-day wall time** (extended from 36h)
- Includes background monitor logging CPU/RAM/progress every 10 min
- Estimated start: June 20, 2026 ~01:06 CDT; end by June 24

**Other jobs (no change)**
- Control system: 21 ns complete; job 50769634 PENDING
- Main system equil: job 50776983 PENDING

---

## June 15, 2026 — Day 6

**Job queue status (all three jobs PENDING as of this morning — none running)**

| Job ID | Name | System | Status |
|--------|------|--------|--------|
| 50737753 | af2_dome24_1 | AF2 24-chain dome | PENDING (bigmem), no output yet |
| 50769634 | 9cz2_prod | Control system production | PENDING (caslake, 5 nodes) |
| 50776983 | 9cz2_equil | Main system equilibration | PENDING (caslake, 6 nodes) |

- Control system last completed checkpoint: `step7_21.restart.coor` → **21 ns total production done**
- AF2 dome-24: still no `.pdb` output in `af2_dome24_output/dome_24chain_input/`
- Main system equilibration: hasn't started yet (input files in place, PENDING)

**Beagle3 transfer plan — meeting with lab member at 4pm June 15**
- Lab member (new to lab) has Beagle3 access; Dr. Haddadian suggested asking her to run jobs there
- Goal: offload all 3 PENDING jobs to Beagle3 (faster/stronger than Midway3 for GPU and bigmem jobs)
- Staging plan: copy files to `/project2/haddadian/junseo/beagle3-jobs/` on Midway3 (shared lab space), then she rsync's from Beagle3
- TODO before 4pm: run the staging rsync commands (see meeting guide in session or below)

**Files to stage per job:**

*Job A — AF2 dome-24 (1.2 GB MSA + 64 KB FASTA):*
```bash
mkdir -p /project2/haddadian/junseo/beagle3-jobs/af2_dome24/msas
rsync -av /scratch/midway3/junseo/26summer-research/alphafold/9cz2/dome_24chain_input.fasta \
    /project2/haddadian/junseo/beagle3-jobs/af2_dome24/
rsync -av /scratch/midway3/junseo/26summer-research/alphafold/9cz2/af2_dome24_output/dome_24chain_input/msas/ \
    /project2/haddadian/junseo/beagle3-jobs/af2_dome24/msas/
```

*Job B — Control system production resume from step7_21 (~60 MB):*
```bash
mkdir -p /project2/haddadian/junseo/beagle3-jobs/control_prod
rsync -av \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step5_input.psf \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_21.restart.coor \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_21.restart.vel \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_21.restart.xsc \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_production.inp \
    /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/run_prod_cpu.sh \
    /project2/haddadian/junseo/beagle3-jobs/control_prod/
rsync -av /scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/toppar/ \
    /project2/haddadian/junseo/beagle3-jobs/control_prod/toppar/
```

*Job C — Main system equilibration (full directory, 2.1 GB):*
```bash
rsync -av /scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/namd/ \
    /project2/haddadian/junseo/beagle3-jobs/main_equil/
```

**What to ask the lab member (fill in job scripts with her answers):**
1. Her Beagle3 username → scratch path `/scratch/beagle3/<username>/`
2. CPU partition name → `sinfo` on Beagle3
3. NAMD module name → `module avail namd` on Beagle3
4. AlphaFold module → `module avail alphafold` on Beagle3 (may not be installed)
5. Account name on Beagle3 → probably `pi-haddadian`, confirm with her

**Job script changes needed for Beagle3** (Midway3 → Beagle3):
- `--partition=caslake` → her Beagle3 CPU partition
- `--account=pi-haddadian` → confirm account name
- `module load namd/2.14` → match what's on Beagle3
- AF2 script: remove `JAX_PLATFORM_NAME=cpu` and `XLA_FLAGS` if running on GPU; update all hardcoded paths

**After meeting:**
- Update CLAUDE.md with Beagle3 job IDs once submitted
- If Beagle3 jobs submitted, decide whether to `scancel 50737753 50769634 50776983` on Midway3

**Files created this session:**
- `beagle3-cheatsheet.md` — command reference for Beagle3 (sinfo, squeue, module avail, rsync, etc.)

---

## June 12, 2026 — Day 5

**RFdiffusion — module available, planning deferred**
- RCC installed `rfdiffusion/1.1.0` on Midway3; weights at `/software/rfdiffusion-1.1.0-all/weights/`; invoked via `run_inference` wrapper
- Module loads CUDA → needs GPU (beagle3), not bigmem; bigmem has no GPU
- Plan: after AF2 dome-24 finishes, run RFdiffusion on beagle3 for the opening region (chains W/V/X + flanking U/A/T/B = 7 chains, ~2,750 residues); full 24-chain dome (~7,800 residues) would OOM on a single A100
- Deferred: no beagle3 access confirmed yet; will revisit after AF2 output is in hand
- Relevant checkpoint: `InpaintSeq_ckpt.pt` (fills missing regions in known structure)

**Job limits checked (Midway3 SLURM QOS)**
- caslake: MaxSubmit = 1000 — no practical limit
- bigmem: MaxSubmit = 10 — currently 1 running (9 slots free)
- No per-user account limits set

**System status at session end (~9:40 AM)**
- Control system: step7_14 complete, step7_15 in progress → ~14–15 ns total; job 50676351 running
- AF2 dome-24: ~16h elapsed of 36h, no PDB output yet (normal); job 50698644 running
- CHARMM-GUI 8119908655: status not confirmed (check website for completion)

---

## June 11, 2026 — Day 4

**Main system — CHARMM-GUI rebuild (full 9cz2, all 36 chains)**
- Root cause of previous broken PSF (session 8095657229): chain ID collision — dome and FtsH chains A–J shared the same single-letter chain IDs; CHARMM-GUI's 26-segment limit silently dropped all 10 FtsH P2 chains
- Fix: renamed FtsH P2 chains (AP2–JP2) to digit chain IDs 1–9 and 0 in both column 22 and segment ID columns 73–76 → `9CZ2/9cz2minimized_08jun_01_ftsh_fixed.pdb`
- Verified: 36 unique chain IDs and segment IDs; HflK × 12 (79–355), HflC × 12 (1–329), FtsH TM × 12 (31–97)
- Submitted to CHARMM-GUI Membrane Builder (NAMD format) with z-translation +56.4 + 30 in step 2
- **CHARMM-GUI session: 8119908655** — all 36 chains selected (PROA–PRAJ)

---

## June 10, 2026 — Day 3

**AlphaFold dome-24 run submitted**
- Decision: run dome-only (24 HflK/HflC chains, no FtsH) on bigmem node to fill in all missing regions
  - FtsH excluded: reduces residue count from ~10,277 to 9,036 → fits in 768 GB bigmem RAM
  - No FtsH needed for dome-only MD (FtsH does not drive dome asymmetry)
- Input: `dome_24chain_input.fasta` — 12 HflK + 12 HflC alternating (full sequences, 419 aa / 334 aa)
- Reused precomputed MSAs from 13-chain run (A/ = HflK, B/ = HflC) — skips multi-day database search
- Template: `--max_template_date=2026-06-10` — 9cz2 used as structural scaffold; gap regions predicted from MSA + context
- Missing regions to be filled: HflK M3 (356–419), HflC 161–190, lower halves of chains X/V/W
- SLURM job 50698644, bigmem partition, 36h; expected 1–2 of 5 models in 36h
- Post-run: use best-ranked model directly as CHARMM-GUI input (no grafting needed); trim HflK 1–78 before build

**Structure files created**
- `9cz2_dome_original.pdb` — dome-only PDB from vanilla 9CZ2.cif (no FtsH, occ>0 only)
  - HflC chains: residues 18–160 and 191–329 (gap at 161–190 visible)
  - HflK chains: residues 79–355 (M3 region absent)
  - Used for visual inspection in VMD and as AF2 template reference

**Control system**
- step7_12 completed successfully — control system now at **12 ns** total production
- Measured performance: ~4.0 ns/day at 4 nodes (192 CPUs), ~0.043 s/step
- New job scripts submitted (SLURM 50676351): loops steps 7_13–7_20, targets 20 ns total
  - 5 nodes, 36h; estimated ~4.5–5.0 ns/day

**Main system (on hold)**
- CHARMM-GUI build (session 8095657229) completed but downloaded as CHARMM format (wrong)
- Re-running from step 5 with NAMD selected; expected June 11, 2026
- On hold pending AF2 dome-24 result — may pivot to dome-only MD instead

**Meeting with Dr. Haddadian**
- Suggested exploring MARTINI force field (CG lipids + AA protein/water) to reduce computational cost of full dome system
  - MARTINI 3 (2021) is current standard; Martini3-IDP (March 2025) adds improved parameters for disordered proteins — directly relevant to flexible HflK/C regions
  - Hybrid CG-AA approach is established in literature but **requires GROMACS, not NAMD** — decided against for now as too large a pipeline pivot; revisit later if needed
- Identified second unresolved region: **HflK M3 = residues 355-419** (C-terminal, sits as disordered loop at the dome apex/interior top); not addressed in Rajiv's structure — needs verification in `9cz2minimized_08jun_01.pdb`
- Discussed AlphaFold context problem for unresolved regions:
  - RFdiffusion inpainting can handle multiple disjoint missing regions simultaneously conditioned on full complex context — worth exploring for M3 and HflC 161-190 together
  - Key caveat: RFdiffusion is a design tool and will generate structured output even for disordered regions; useful for getting a clash-free starting geometry, not for predicting disorder
  - AF3 server worth trying for a small multimer (chain V + neighbors) as an intermediate option
- Friday June 13: meeting with WashU biological collaborator — questions logged in `meeting_questions.md`

**Other**
- Reviewed Rajiv's analysis scripts (`/project2/haddadian/rajiv/analysis/`):
  - `lipid-prox-*.tcl` — per-frame lipid counts within cutoff of protein TM regions
  - `com_lipids.py` — MDAnalysis COM-based lipid proximity (PBC-aware, faster)
  - `color_lipids.tcl` — VMD visualization coloring lipids by class per frame
  - `thickness.py` — 2D bilayer thickness map from phosphorus headgroup positions

---

## June 9, 2026 — Day 2

**Control system**
- step7_11 finished; initial performance measurement: 2.42 ns/day (later revised to ~4.0 ns/day in step7_12 benchmarks on Day 3)
- Submitted step7_12 restart job (SLURM 50623759) — 4 CPU nodes, 36h

**Main system**
- CHARMM-GUI build in progress (session 8095657229); expected to complete June 10

---

## June 8, 2026 — Day 1

**Orientation and setup**
- Reviewed Rajiv's completed work: structure preparation, AlphaFold runs, pre-production minimization, and retired test systems
- Familiarized with the two active systems:
  - **Control system** (`charmm-gui-7628525516/namd/`): membrane-only baseline, 11 ns complete at end of day
  - **Main system**: 9cz2 full dome + membrane, submitted to CHARMM-GUI Membrane Bilayer Builder

**Structure pipeline for main system**
- Input: `9cz2minimized_08jun_01.pdb` (Rajiv's structure, no water)
- Ran through CHARMM-GUI Membrane Bilayer Builder — wrong membrane position detected
- Z-translated by 56.4 Å → `9cz2_tm_centered_for_charmmgui.pdb`
- Additional z-translate by +30 applied in CHARMM-GUI step 2
- Control system initially submitted with 2 nodes, 12h

---

## Pre-summer history

## 2026-05-26 — Zoom meeting
- Fix structure from Rajiv
- Next meeting: in Korea (early August)

## 2026-05-15 — Meeting
- Goal: improve Rajiv's dome structure
- Get lipid analysis script from Rajiv and learn to run it
- Rajiv's analysis scripts shared at `/project2/haddadian/rajiv/analysis` (pi-haddadian group access required)

## 2026-04-30 — No-dome system preparation
- VMD selection for water near protein: `same residue as water and within 5 of {segname PROV PROW PROX PROY PROZ PRAA}`
- Cut the dome (top part of chains), kept only the membrane-embedded portion → this "no-dome" system was run to isolate the effect of the dome on protein function
- Both the monomer test and no-dome system are now retired — context established, moving to full system

## 2026-04-29 — Monomer z-translation
- System: single-chain monomer (used to test stability of AlphaFold-generated region 161–190)
- Translated 60 Å along z-axis for CHARMM-GUI membrane positioning

## 2026-04-24 — AlphaFold region docked
- Rotated/translated AlphaFold-generated region into docked structure
- Active residues: `resid 1 to 161 or resid 171 to 188 or resid 190 to 334`

## 2026-04-20 — Dihedral angle notes
- PHI of PRO216: atoms 3017–3034–3035–3036 (C–N–CA–C)
- PSI of LEU215: atoms 3015–3016–3017–3034 (N–CA–C–N)
- HflC missing residues 161–190 confirmed from paper

## 2026-04-17 — Control system membrane composition decided
- DPPE 70%, POPG 12.5%, DOPG 12.5%, LOACL1 2.5%, TLCL1 2.5%
- VMD scripts written to copy chains A, B, T and superimpose onto X, V, W via RMSD on resid 269–348

## 2026-04-13 — Cluster scaling analysis + build planning
- Established optimal node/queue tradeoff (see CLAUDE.md)
- Goals: build control membrane system, attempt dome superimposition

## 2026-04-12 — Cluster benchmarking (GPU + 10 nodes)
- Same no-dome test system
- 1 GPU node (4 GPUs): ~1.55 ns/day (~15.5 h/ns)
- 10 CPU nodes (480 CPUs): ~7.7 ns/day (~3.1 h/ns)

## 2026-04-10 — Cluster benchmarking (CPU)
- System: 9cz2 without dome (membrane-embedded portion only — temporary test system)
- 1 CPU node (48 CPUs, caslake): ~0.90 ns/day (~26.7 h/ns)

## 2026-03-28 — CHARMM-GUI membrane builder
- Running CHARMM-GUI membrane builder (Job ID: 7472534433)

## 2026-03-27 — CHARMM-GUI setup
- Created CHARMM-GUI account
- Received second paper (biorxiv)
- Meeting: Look into GaMD for longer effective timescales

## 2026-03-26 — Paper reading
- Read: Ghanbarpour et al. (2025), *EMBO Journal* — "An asymmetric nautilus-like HflK/C assembly controls FtsH proteolysis of membrane proteins"

## 2026-03-24 — First meeting
- Research question established: What causes the opening — membrane composition or protease? What is the effect of the dome on the opening?

---
