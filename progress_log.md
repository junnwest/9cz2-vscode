# Research Progress Log — 9cz2 FtsH•HflK/C Project

**PI**: Dr. Haddadian  
**Researcher**: Jun-Seo Yang  
**Start date**: June 8, 2026  
**Cluster**: Midway3 (`/scratch/midway3/junseo/26summer-research/`)

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
