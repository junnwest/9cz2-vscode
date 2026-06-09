# Progress Log

Entries are chronological, oldest first. Add new entries at the bottom.
Format: `## YYYY-MM-DD (Day N) — [brief title]`

---

## 2026-03-24 — First meeting
- Research question established: What causes the opening — membrane composition or protease? What is the effect of the dome on the opening?

## 2026-03-26 — Paper reading
- Read: Ghanbarpour et al. (2025), *EMBO Journal* — "An asymmetric nautilus-like HflK/C assembly controls FtsH proteolysis of membrane proteins"

## 2026-03-27 — CHARMM-GUI setup
- Created CHARMM-GUI account
- Received second paper (biorxiv)
- Meeting: Look into GaMD for longer effective timescales

## 2026-03-28 — CHARMM-GUI membrane builder
- Running CHARMM-GUI membrane builder (Job ID: 7472534433)

## 2026-04-10 — Cluster benchmarking (CPU)
- System: 9cz2 without dome (membrane-embedded portion only — temporary test system)
- 1 CPU node (48 CPUs, caslake): ~0.90 ns/day (~26.7 h/ns)

## 2026-04-12 — Cluster benchmarking (GPU + 10 nodes)
- Same no-dome test system
- 1 GPU node (4 GPUs): ~1.55 ns/day (~15.5 h/ns)
- 10 CPU nodes (480 CPUs): ~7.7 ns/day (~3.1 h/ns)

## 2026-04-13 — Cluster scaling analysis + build planning
- Established optimal node/queue tradeoff (see CLAUDE.md)
- Goals: build control membrane system, attempt dome superimposition

## 2026-04-17 — Control system membrane composition decided
- DPPE 70%, POPG 12.5%, DOPG 12.5%, LOACL1 2.5%, TLCL1 2.5%
- VMD scripts written to copy chains A, B, T and superimpose onto X, V, W via RMSD on resid 269–348

## 2026-04-20 — Dihedral angle notes
- PHI of PRO216: atoms 3017–3034–3035–3036 (C–N–CA–C)
- PSI of LEU215: atoms 3015–3016–3017–3034 (N–CA–C–N)
- HflC missing residues 161–190 confirmed from paper

## 2026-04-24 — AlphaFold region docked
- Rotated/translated AlphaFold-generated region into docked structure
- Active residues: `resid 1 to 161 or resid 171 to 188 or resid 190 to 334`

## 2026-04-29 — Monomer z-translation
- System: single-chain monomer (used to test stability of AlphaFold-generated region 161–190)
- Translated 60 Å along z-axis for CHARMM-GUI membrane positioning

## 2026-04-30 — No-dome system preparation
- VMD selection for water near protein: `same residue as water and within 5 of {segname PROV PROW PROX PROY PROZ PRAA}`
- Cut the dome (top part of chains), kept only the membrane-embedded portion → this "no-dome" system was run to isolate the effect of the dome on protein function
- **Both the monomer test and no-dome system are now retired — context established, moving to full system**

## 2026-05-15 — Meeting
- Goal: improve Rajiv's dome structure
- Get lipid analysis script from Rajiv and learn to run it
- Rajiv's analysis scripts shared at `/project2/haddadian/rajiv/analysis` (pi-haddadian group access required)

## 2026-05-26 — Zoom meeting
- Fix structure from Rajiv
- Next meeting: in Korea (early August)

## 2026-06-08 (Day 1) — Official start
*(Note: a June 2 plan to run the control membrane with 10 nodes was drafted but not executed)*
- **Structure 01**: Rajiv's structure without water → `9cz2minimized_08jun_01.pdb`
- Ran through CHARMM-GUI membrane bilayer builder — wrong membrane position detected
- Z-translated by 56.4 Å → `9cz2_tm_centered_for_charmmgui.pdb`
- Additional z-translate by 30 in CHARMM-GUI step 2
- Submitted control system (2 nodes, 12 hours)

## 2026-06-09 (Day 2) — Control system restart
- Control system finished (2.42 ns/day)
- Resubmitted control system (4 nodes, 36 hours)
- Main system still running in CHARMM-GUI; expected to finish Day 3

---
<!-- Add new entries below this line -->
