# Research Progress Log — 9cz2 FtsH•HflK/C Project

**PI**: Dr. Haddadian  
**Researcher**: Jun-Seo Yang  
**Start date**: June 8, 2026  
**Cluster**: Midway3 (`/scratch/midway3/junseo/26summer-research/`)

---

## August 8-15, 2026 — GaMD requeue data loss root-caused, full-model/full-bact equilibration debugged,
## v10/v11 read out (real SS does NOT fix pre-collapse), all-11-variant VMD tooling, idle-job sweep

### GaMD data loss from the Aug 6 maintenance window, root-caused

Reconnected Aug 8 after the maintenance window closed. `control` and `dome-bact` GaMD segment-2 jobs
were running again under their original job IDs — but their DCD frame counts looked wrong. Parsed
the DCD header directly (`NSET`/`ISTART` fields) rather than trust the log: both had been **silently
restarted from the beginning of segment 2**, not resumed. Root cause: Slurm's default `Requeue=1`
resubmits a preempted job under the same ID, and `gamd-equilN.inp` has a fixed `firsttimestep`
pointing at the segment's original start — it has no way to know how far the previous attempt got.
NAMD just reran the whole segment, overwriting the DCD in place.

**Confirmed losses**: `control` lost ~12.76 ns (was at 18.70M/22.5M, restarted at 12.32M), `dome-bact`
lost ~5.54 ns (was at 8.18M, restarted at 5.41M). Not corrupted — a valid restart from a valid
checkpoint — just wasted wall-clock, roughly 2.5 days and 1 day respectively.

**Fixed**: `scontrol update JobId=X Requeue=0` on both live jobs (confirmed this works on an
already-running job, no restart needed), then `--no-requeue` added to every NAMD/GaMD sbatch script
in the project (audited all of `control`/`dome-model`/`dome-bact`/`full-model`/`full-bact`'s
production and equilibration scripts — none had it). `run_prod_gpu.sh`-driven production wasn't
actually at risk (it self-heals by finding the latest completed 1 ns block on restart — verified
`control-prod`'s `step7_105`→`106` was continuous straight through the maintenance window), but
patched those scripts too for a cleaner failure mode regardless.

Also restarted `dome-model`'s GaMD (which TIMEOUT'd cleanly, not requeued — no data at risk there)
via `make_gamd_restart.py`, with `--no-requeue` added to the generated script pre-emptively.

### full-model/full-bact equilibration — two real bugs, one false alarm

**Bug 1**: `full-model-equil` failed instantly — `step5_assembly.str` was never uploaded when the
system was set up Aug 5 (only `namd/` was copied, not the CHARMM-GUI download's parent directory).

**Bug 2, found while investigating bug 1**: `full-bact`'s `step5_assembly.str` on the cluster turned
out to be a **Jul 15 leftover from the superseded 31-97 build**, not the Aug 5 rebuild — box
dimensions differ by several Å (A: 308.3→306.2, C: 201.2→205.8). This one had already been silently
in use for 9 hours of a real equilibration run (step6.1-6.4 complete) before being caught.

**False alarm, but investigated properly rather than assumed**: checking whether the box was
actually too small (protein top reaches +144 Å above the membrane, water box only to +104 Å)
initially looked alarming. User pushed back — asked whether visual inspection should happen before
committing to a rebuild, which was the right instinct. Built a quantitative version of that check
instead of a screenshot: periodic-wrap the overflow atoms using the actual box dimensions and
measure distance to the nearest real protein/lipid atom. Result: **zero clashes within 8 Å even at
the worst point** — confirmed with both the correct (205.78 Å) and the actually-used wrong (201.21
Å) box values. The dome's overflow wraps into open bulk water on the far side, not into itself.
**No rebuild was needed.** Stopped the running job per the user's initial instruction, then
re-verified this finding, then un-stopped by just fixing the file and resubmitting fresh rather than
going back to CHARMM-GUI. Lesson banked: "exceeds the declared box" on paper is not the same
question as "does it actually clash with anything" — check the latter before recommending a rebuild.

Both jobs resubmitted clean (`full-model-equil` 53194227, `full-bact-equil` 53194229) — both reached
step6.5 of 6 without incident by Aug 10, confirming the fix held.

**Equilibration timing explained, not assumed slow**: step6.4-6.6 have 2× the steps of step6.1-6.3
(250,000 vs 125,000, read directly from the `.inp` files) — per-step timing matches this exactly
(steps 1-3 each ~3-3.5h, step 4 took 6h55m). Not a slowdown. Both jobs also share node
`beagle3-0020` with an unrelated job from another user (`shoutinghs`) — a real, unquantified
contention factor alongside the step-count explanation.

### v10/v11 read out — the actual answer, and it's not what the working hypothesis expected

Downloaded v10/v11 trajectories (interrupted twice by socket drops and slow transfers before
succeeding) and ran the same Rg/RMSD script used for v1-v9.

**Result: real secondary structure does NOT fix the pre-collapse problem.** Both v10 and v11 start
their production window already contracted (Rg_xy0 76.94/77.07 vs AA's 79.65 and v1/v2's 79.00/79.51)
— the same pre-equilibration-collapse failure mode that invalidated the Go family's comparison. This
was the specific thing v10/v11 were built to test in the first place; the answer, now that it's
measured, is that supplying real secondary structure alone doesn't prevent it.

Within that caveat, v10 vs v11 is a genuine split decision, not a clean winner:

| | Rg_xy0 | ΔRg_xy | ΔRg_z | RMSD |
|---|---|---|---|---|
| AA (ref) | 79.65 | −3.40 | +1.72 | 8.74 |
| v10 (no elastic) | 76.94 | **+1.93** (wrong sign) | −1.25 (wrong) | 16.51 |
| v11 (elastic ef700) | 77.07 | +0.29 (~flat) | **+1.19** (right sign) | 22.45 (worst of all 11) |

v10 drifts less overall (lower RMSD, plateaus after ~8 ns) but its ring actively expands in the
wrong direction. v11 barely moves in-plane and is the only variant of all 11 to get the *vertical*
direction right, at the cost of the highest RMSD of any variant and no sign of convergence by 32 ns.
User asked "which is better" expecting a single answer; the honest answer is that RMSD and shape-
accuracy disagree here, and neither variant's AA-comparison should be treated as clean given the
shared pre-collapse issue.

Open question this leaves for whenever it's picked back up: what in the CG system is causing the
contraction if not secondary structure or restraint scheme — most likely candidate remains the CG
membrane/lipid parameterization (the `TLCL1`→`TOCL` substitution flagged back in the original v1-v6
readout), not yet tested directly.

### VMD tooling — all 11 Martini variants, correctly

Built `trajectories/load_v2_v10_v11.tcl` and `trajectories/load_all_martini.tcl`. Both caught real
bugs by testing headless before handing over, twice:
- An early version of the v2/v10/v11 script drew v11's elastic bonds from **v6's** topology file via
  `cg_bonds`. Wrong — v6 (all-coil/ef300) and v11 (real-SS/ef700) have different bonded chemistry
  entirely; would have rendered the wrong bond network, not just failed. User caught this by
  reporting "the visualization didn't apply on both" rather than assuming it was fine. Rebuilt as one
  `proc` applied identically to every variant, each drawing `cg_bonds` from its own topology.
- Building the all-11 script surfaced that v7/v8/v9's local `.xtc` files were silently truncated
  (18/1/1 frames instead of 33) — leftovers from the original failed-parallel-download attempt days
  earlier that never got the same sequential-redownload fix v10/v11 received. Re-downloaded and
  verified byte-identical to the cluster copies.

Also found: VMD's built-in RMSD Visualizer Tool doesn't work on Martini systems at all — it ANDs
every selection with a hardcoded all-atom backbone filter (`name C CA N O`), which matches zero
Martini beads. Every typed selection fails identically, including `protein` and `all`. Documented
the two workarounds (disable its "Backbone" toggle, or use `measure rmsd` directly).

### Idle-job sweep (Aug 10) and dome-bact local catch-up

Full 15-cell status check found `control-prod`/`dome-model-prod`/`dome-bact-prod` had all finished
cleanly and sat idle for 8-16.5 h — the project's most common failure mode, caught again. Resubmitted
all three. `dome-model`/`dome-bact` GaMD had both recovered into the boosted phase after the earlier
requeue-restart, re-crossing the 7.5M cMD boundary.

Pulled `dome-bact`'s missing 13 ns locally (`step7_81`-`93`) to catch the local copy up to the
cluster's 93 ns — first parallel attempt timed out (same lesson as always), background sequential
retry succeeded, spot-verified byte sizes against remote.

### Found and archived Rajiv's lipid-count heatmap script

Searched `/project2/haddadian/rajiv/analysis` (accessed fine via `ssh beagle3` directly this
session, contrary to the standing "/project2 unreliable" warning — that mount issue may be
intermittent, not constant) for a heatmap showing per-lipid-species spatial count. Not
`thickness-map.py` (bilayer thickness, not count) or `plot_lipid_counts.py`/`new_com_lipids.py`
(both time-series line plots despite the name). The actual match: `lipid_density.py` — 2D XY
histogram of one lipid species' phosphate positions, `plt.imshow` heatmap, colorbar literally
labeled "Average lipid count per bin". Downloaded to `scripts/analysis/rajiv_lipid_density.py`
(prefixed to keep clear it's Rajiv's, not ours), verified byte-identical to source.

---

## August 6, 2026 (session 2) — three-way CHARMM-GUI comparison, restraint-mechanism deep dive, sscache tool

### Found a lipid-only CHARMM-GUI Martini build already existed locally

User referenced "the lipid-only martini system we generated a few days ago." No record of it in
memory, `CLAUDE.md`, or `progress_log.md` — searched all three plus every `~/Downloads/charmm-gui-*`
directory rather than guess. It turned out to be `charmm-gui-8542787498` (dated Jul 30), which had
already been in use all along as the "membrane-only" reference for the earlier CHARMM-GUI
mdp-ladder comparison — just not previously identified to the user as "the lipid-only system."
Confirmed via `system.top`: DPPE/POPG/DOPG + water + ions, zero protein `#include`.

### Added it as a third column to the Martini parameter-comparison artifact

Extended the two-way (CHARMM-GUI protein+lipid vs. ours) table built Aug 5 into a three-way table
(+ CHARMM-GUI pure-lipid), republished as a fresh artifact (the original became unwritable
mid-session — "the artifact you're updating was deleted, or you no longer have write access to it"
— republished under a new file path/URL rather than lose the work).

**Key result the third column settles**: the pure-lipid build matches the protein-containing 2ZXE
build on every physics parameter at every stage, differing only in the two things a protein
mechanically requires (POSRES ramp, one thermostat group). This confirms the gap to our pipeline
isn't "CHARMM-GUI does something different when a protein is present" — it's specifically that we
skip the secondary-structure step and the staged ladder, independent of protein content.

### Restraint-mechanism deep dive — asked "is there a difference in how they restrain lipids vs
protein, or treat it differently"

Went past the force-constant ramp values (already in the table) to the actual mechanism in each
`[position_restraints]` block:

- **Protein `POSRES`**: `fcx=fcy=fcz=POSRES_FC` — full isotropic 3D lock. Counted the actual
  restrained atoms in 2ZXE chain A: 992 of 2,245, every one a `BB` bead. Side chains completely
  free. "Pin the skeleton, let the flesh move."
- **Lipid `BILAYER_LIPIDHEAD_FC`**: `fcx=0, fcy=0, fcz=BILAYER_LIPIDHEAD_FC` — z-only, one bead per
  molecule (the headgroup phosphate). Lateral diffusion deliberately untouched, since that's the
  membrane's defining physical behavior — restraining it would equilibrate a solid, not a membrane.

**Then asked "are those martini force-field defaults"** — checked rather than assumed:
- Protein POSRES comes from `martinize2 -p backbone` **itself**: proved directly, since our own v10
  topology (plain `martinize2 -p backbone`, zero CHARMM-GUI involvement) produces the byte-identical
  block. This is a Martini-tooling (vermouth) convention, upstream of CHARMM-GUI.
- Lipid `BILAYER_LIPIDHEAD_FC` is **not** a community Martini force-field feature — found an
  independent (non-CHARMM-GUI) copy of the identical file (`martini_v3.0.0_phospholipids_v1.itp`,
  from a raw GitHub download used elsewhere in this project) and diffed it against CHARMM-GUI's
  bundled copy: CHARMM-GUI's version has ~50 extra lines (`BILAYER_LIPIDHEAD_FC`,
  `MICELLE_LIPIDHEAD_FC`, `VESICLE_LIPIDTAIL_R` restraint blocks) absent from the upstream file
  entirely. CHARMM-GUI patches these in as a convenience for its own bilayer/micelle/vesicle-building
  workflows.
- **Bonus finding while diffing**: that restraint mechanism only survives in the legacy `_v1`
  combined-lipid file. The current `_PE_v2.itp`/`_PG_v2.itp` files CHARMM-GUI actually includes for
  PE/PG lipids (both reference builds use them) carry **no** `[position_restraints]` block at all —
  confirmed in both the protein+lipid and pure-lipid `system.top`s. So `-DBILAYER_LIPIDHEAD_FC` is a
  **no-op in CHARMM-GUI's own output too**, for the exact lipid classes both real systems use — not
  a gap unique to our pipeline, as the artifact's original "Differs" status implied. Flagged this as
  a correction to the user rather than let the artifact overstate CHARMM-GUI's side.

One-liner drafted for reporting to Dr. Haddadian: "CHARMM-GUI restrains the protein's backbone fully
in 3D — protecting its overall shape — while restraining lipids only vertically and never sideways,
since a membrane's whole point is that lipids slide past each other; but for the phospholipids we
actually use, that lipid restraint turns out to be dead code even in CHARMM-GUI's own official
pipeline, so equilibration is really being steered by the protein restraint alone in both builds."

### `sscache_by_segment.tcl` — per-frame secondary structure caching

User asked to read `~/Downloads/sscache.tcl` (Andrew Dalke's standard VMD script library tool,
ks.uiuc.edu) and apply it. It recomputes SS on every frame change via `vmd_calculate_structure`
and caches the result — useful for scrubbing a trajectory where SS might genuinely change (e.g. the
coiled-coil domain near the dome opening, per Paper 2). Recognized it calls the exact same
whole-molecule STRIDE path that fails silently above 99,999 protein atoms (see the
`stride_by_segment.tcl` fix from Aug 5-6). Wrote
`trajectories/namd/sscache_by_segment.tcl` — identical `start_sscache`/`stop_sscache`/
`reset_sscache` API, but the internal recompute calls `stride_by_segment` instead of
`vmd_calculate_structure`.

**Tested before handing over** (headless VMD on `dome-bact`, 2 equilibration DCDs loaded):
frame 5 first visit 848 ms (real SS codes returned: `B C E G H T`, not falling into the coil bug),
frame 10 first visit 796 ms, frame 5 **revisit 31 ms** — confirms both the per-segment fix works
inside the caching wrapper and the cache itself is real (27× speedup). Cache had exactly 2 entries
after visiting 2 distinct frames.

Full ready-to-paste VMD load block (psf/pdb + equilibration + production with `step 5` + both
SS scripts + `start_sscache`) given to user for pasting after a VMD environment reset.

---

## August 6, 2026 — CLAUDE.md trimmed for context size; full text of removed sections archived below

`CLAUDE.md` had grown to 1,721 lines (~133 KB, ~30-35k tokens) and is loaded in full on every
conversation turn per this project's setup — a fixed cost paid before any actual question is asked.
Combined with running the session on Opus, this was burning through usage far faster than the actual
work justified. Trimmed `CLAUDE.md` down to current-state reference only (active systems, standing
gotchas, operational setup); moved dated narrative/diagnostic content here, where it isn't auto-loaded.
Some of this duplicates entries elsewhere in this log — kept anyway rather than risk losing anything
verifying non-duplication under time pressure.

<details>
<summary>Archive: Structure Preparation narrative (AlphaFold runs, M3 rotation, monomer approach) — cut from CLAUDE.md "Structure Preparation" section</summary>

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
- **Fallback (ready)**: `hflk_af2_m3rotated.pdb` + `replace_hflk.py` if dome-24 fails.
- **Post-run plan**: Use best-ranked model output directly as input to CHARMM-GUI for dome-only membrane system; discard HflK M1/M2 (1–78) predictions as TM region is unreliable without membrane context

(Final status: this run TIMED OUT at exactly 14-00:00:16 with zero model output — see the AF2 dome-24
FAILED entry elsewhere in this log / CLAUDE.md. Total loss of the 14-day bigmem allocation.)

### Monomer M3 Approach — Attempted and Abandoned (June 16–17, 2026)
Tried using `hflk_mono_ranked_0.pdb` to add M3 tails to all 12 HflK chains in `9cz2minimized_ftsh_fixed.pdb`:
1. Superimposed AF2 monomer onto each HflK chain (CA resid 79–355), extracted M3 (356–419): `scripts/superimpose_hflk_m3.tcl`
2. Rotated each M3 tail in 15° steps about the CA(355)→CA(356) bond axis to minimize CA-CA clashes: `scripts/declash_m3.tcl` (Rodrigues rotation, VMD batch mode)
3. **Result**: Min CA-CA = 0.83 Å (down from 0.65 Å), min all-atom = 0.17 Å, 2,191 all-atom clashes < 1.5 Å — unacceptably severe
4. **Fatal flaw**: Rotation was clash-driven with no dome geometry awareness; several M3 tails oriented outward (away from dome interior) rather than inward — structurally wrong
- **Decision**: Abandoned in favor of (a) the AF3-monomer M3 graft + 2D dihedral declash → NAMD minimization pipeline (Day 15, `scripts/minimize_m3/`), and (b) the dome-24 multimer run which predicts all 24 M3 tails simultaneously in dome context → correct inward orientation guaranteed by multimer modeling

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

</details>

<details>
<summary>Archive: old Midway3 performance benchmarks (retired no-dome system) — cut from CLAUDE.md</summary>

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

Scaling is ~linear; speedup and wait time roughly cancel for small jobs.

**Optimal node choice** (for that retired system): ≤2 ns → 2–4 nodes; 2–10 ns → 4–6 nodes; ≥10 ns → 8–10 nodes.

</details>

<details>
<summary>Archive: GaMD-vs-coarse-graining research + Chen's GPU-resident GaMD build saga — cut from CLAUDE.md "Current Systems" section (superseded by the REJECTED conclusion, kept in full here)</summary>

**GaMD chosen over coarse-graining as the enhanced-sampling approach** after research (July 17–20): a
Martini AA-protein/CG-membrane hybrid couples the protein–lipid *interface* only at CG resolution (loses
the lipid-specificity our question depends on) and is documented to over-stabilize protein conformational
dynamics — the exact thing we study. (The separate, fully-CG `martini-dome` comparison system is a
different, complementary effort — a speed/sanity check, not this hybrid approach.)

**GaMD technical notes (verified July 22, 2026):**
- **Resident mode is incompatible with GaMD in _stock_ NAMD** (tested, job 52473685: NAMD FATAL-errors at startup with `GPUresident is incompatible with... accelMD` and related options).
- **2-GPU offload GaMD benchmark** (job 52473718): 0.0844 s/step = **~2.0 ns/day** (1.28× speedup over 1 GPU). Scaling is moderate (GaMD boost overhead doesn't parallelize as cleanly as plain dynamics), but real.
- **GaMD equilibration timeline for dome systems** (52 ns target): ~26 days wall-clock, running both `dome-model` and `dome-bact` GaMD in parallel on separate 2-GPU allocations.
- **Recommendation**: Launch both dome GaMD runs on 2 GPU / 16 PE offload (Rajiv's templates used 1 GPU; bumping to 2 saves ~one week per system).

**Dr. Haochuan Chen's NAMD GPU-resident GaMD patch (lead surfaced July 23, 2026):**
- Learned of this via an email thread forwarded by Dr. Haddadian (originally sent to him July 15, thread dated July 2–9) between Prof. Stephen Meredith / Dr. Shirin Ardekani (UChicago, unrelated T-cell-receptor GaMD project) and Arvind Ramanathan / Moeen Meigooni (Argonne National Lab), about running GaMD on ALCF's Polaris/Aurora.
- Per that thread, **Dr. Haochuan Chen** (Beckman Institute, UIUC — NAMD/TCBG developer) has implemented **GPU-resident GaMD support for NAMD**, referenced as merge requests **`!489`** and **`!504`** on `gitlab.com/tcbgUIUC/namd`, described as "completed and pending review." Dr. Meredith's email adds MR 504 targets **NVIDIA or AMD GPUs** (tested on Polaris) — plausibly buildable on Beagle3's A100s too.
- **RESOLVED (July 24) — built and verified working.** Dr. Chen granted direct GitLab access to the actual branch: `haochuan/gpu_accelmd_2` (commit `ebed67284e6ab8f72dcb6b15bd32ed0117e10193`; reports as **NAMD 3.1alpha4pre**, a dev version). Cloned to `/scratch/beagle3/junseo/namd-chen-gpuresident/` (private repo — only copy Beagle3 staff can access).
  - **Build**: Charm++ 8.0.0 via `./build charm++ multicore-linux-x86_64 --with-production` (cmake/4.3.0 loaded first — without it, `./build` silently falls back to the legacy `buildold` path). TCL 8.6.17 threaded + FFTW from `ks.uiuc.edu/Research/namd/libraries/` — this branch specifically requires TCL 8.6.x, not 8.5.9. NAMD configured via `./config Linux-x86_64-g++ --charm-arch multicore-linux-x86_64 --with-single-node-cuda --cuda-prefix /software/cuda-11.5-el8-x86_64`, built with `make -j16` on a compute node. Binary: `/scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3`.
  - **Test result (job 52586965)**: ran the existing GaMD benchmark with `CUDASOAintegrate on` + 16 PE / 2 GPU — completed 5,000 steps cleanly, no FATAL error, sane energies. **8.57 ns/day**, vs. ~0.87–0.88 ns/day offload — ~10× speedup.
  - **Email sent to Beagle3 support (July 24)**: requested review/adoption as a supported module.
- (This build was later validated more rigorously and its GaMD boost statistics found to be corrupted — see "GPU-resident GaMD REJECTED" elsewhere in this log / CLAUDE.md. The conclusion that survives: DO NOT use resident mode for GaMD; conventional MD in resident mode via this build is fine and is documented in `share_gamd_resident/`.)

</details>

<details>
<summary>Archive: Beagle3 job queue snapshot — July 24, 2026 (fully superseded, cut from CLAUDE.md verbatim)</summary>

**Running (as of July 24, all long since finished/superseded):**
| Job ID | Name | What it is |
|---|---|---|
| 52611795 | control-prod | Normal `control` production, resubmitted 48h — fixed a missing `--constraint=a100` in this system's script (only one missing it) |
| 52595314 | dome-model-prod | Normal `dome-model` production, resubmitted 48h, `TARGET_NS=20` cap removed |
| 52595315 | dome-bact-prod | Same for `dome-bact` |
| 52595316 | full-bact-prod | Normal `full-bact` production, resubmitted 48h |
| 52594023 | martini-prod-1 | Martini CG production, 24 threads/1 GPU (1,934 ns/day) |
| 52527113 | gamd-dome-model-equil | GaMD equilibration, from `step7_20` restart |
| 52527114 | gamd-dome-bact-equil | GaMD equilibration, from `step7_20` restart |
| 52610940 | gamd-control-equil | GaMD equilibration for `control`, branched from `step7_21` |
| 52610941 | gamd-full-model-equil | GaMD equilibration for `full-model`, branched from `step7_20` |

**CORRECTION (July 24) — GaMD is not "3 systems," it's expanding to 4 (of 5).** GaMD equilibration was
built and submitted for `control` and `full-model` too (both already past 20 ns of conventional
production). Only `full-bact` (10.05 ns at session close) didn't have GaMD yet, purely because it hadn't
reached 20 ns. Both new configs fixed a latent bug: `accelMDGRestart on` with no actual restart file
staged — set to `off` for fresh starts.

**Wall-time convention (July 24): all production submissions now use 48h (`2-00:00:00`)**, the confirmed
`beagle3-prio` QOS maximum — up from the earlier 36h convention. GaMD equilibration is a deliberate
exception, still using `beagle3-long` QOS at 96h (`4-00:00:00`).

**PE-fixed NAMD GaMD offload benchmarks — final numbers** (corrected a ps/ns unit error mid-session
before reporting — 2 fs = 0.000002 ns, not 0.002):
| GPUs | s/step | ns/day |
|---|---|---|
| 1 | 0.110 | 1.57 |
| 2 | 0.0625 | 2.77 |
| 3 | 0.0475 | 3.64 |
| 4 | 0.0382 | 4.53 |

Real, meaningful GPU scaling once the `+p4` PE-starvation bug was fixed (1.8×→5.2× over the original
broken 0.878 ns/day flat-line). Still all offload mode (stock NAMD 3.0.1 can't do resident+GaMD) —
Chen's resident-mode build hit 8.57 ns/day in its smoke test.

</details>

<details>
<summary>Archive: Martini 3 CG Dome System build diary — diagnostic narrative cut from CLAUDE.md (recipe + gotchas kept in CLAUDE.md; this is the full bug-hunt detail)</summary>

**EM segfault root-caused and fixed (July 22–23) — was a GROMACS build bug, not a topology problem.**
First `sbatch` attempt (job 52534609) segfaulted inside GROMACS's threaded virtual-site construction.
Ruled out an OpenMP threading race by rerunning single-threaded/CPU-only — still segfaulted in the same
place. Actual cause: the loaded module was `gromacs/2022.4-plumed_2.8.1` (PLUMED-patched build touching
vsite/force code paths). Always use `gromacs/2025.3` for this system.

**Membrane-position bug found and fixed (July 23).** Visual inspection in VMD showed the membrane
crossing through roughly the vertical middle of the protein, not near the bottom as it should
biologically. Quantified against the real AA `dome-model` system: membrane should sit ~60 Å below the
protein's center (verified: real AA system = 60.5 Å below center); the broken CG build had it at ~50.7%
up the protein's z-extent — dead center. Root cause: the CG pipeline starts from
`dome_m3_af3_ic_minimized_final_noftsh.pdb`, which was never assembled with a membrane, so `insane` had
no anchor point and centered on the protein's bulk mass instead. Fix: empirically reverse-engineered
`insane`'s placement behavior, computed the exact z-translation needed, and enlarged the box in z from
19.487 → 24.0 nm for asymmetric padding. Final result: 59.5 Å below center, matching the 60.5 Å reference.

**Lipid under-packing bug found and fixed (July 23–24) — `insane`'s `-fudge` exclusion parameter.**
After the position fix, visual inspection still showed a large connected void under the dome. Quantified
via a pure-numpy connected-component analysis on a binned headgroup-density grid (PBC-aware flood fill,
since `scipy.ndimage` had its own `libstdc++` conflict on this node): one contiguous void of **147.4 nm²**
(~6.85 nm equivalent radius) — ~10× larger than the next-biggest gap. Root cause: `insane`'s
protein-lipid exclusion (`-fudge`, default 0.1) marks a grid cell occupied only if local protein-atom
density exceeds 10% of the most-crowded cell anywhere — too strict for this system's flexible/wobbly M3
stalk region. Fix: swept `-fudge` from 0.1→0.3→0.6→0.9; void area dropped **147.4 → 88.9 → 7.1 nm²**
(final: several modest ~5–13 nm² regions, no dominant blob, consistent with ~12 separate per-stalk
exclusions matching the real ring of HflK anchors). Final config: `-fudge 0.9`, area-per-lipid ≈ 61.8 Ų
(real AA reference range 52–73 Ų) — verified this is a genuine improvement, not just exclusion disabled
(`-fudge 1.0` would fully disable it). `-fudge 0.9` is system-specific, not a universal default.

**1,900+ ns/day production speed is real, not a bug** — verified two ways: (1) internal consistency —
GROMACS's own per-operation timing breakdown gives 0.894 ms/step, which algebraically reproduces the
reported 1,933.853 ns/day exactly; (2) external corroboration — an unrelated published GROMACS 2024
benchmark (NHR@FAU, A100, 16 threads) of an all-atom system at almost exactly the same particle count
(170,320 atoms) gets 129.09 ns/day; our CG system's ~13× speedup over that is fully explained by the
20 fs vs. 2 fs timestep (10×) plus cheaper reaction-field-vs-PME/no-explicit-H physics (~1.3×).
Source: HPC-Café: GROMACS 2024 usage and performance (NHR@FAU), hpc.fau.de.

**Production speed benchmark results (July 24)** — full cross-product, 5,000-step tests, `-resetstep 1000`:

| Threads | 1 GPU, CPU update | 2 GPU, CPU update | GPU-update (any config) |
|---|---|---|---|
| 4 | 940 ns/day | — | FAILED |
| 8 | 1,360 ns/day | — | FAILED |
| 16 | 1,721 ns/day | 1,708 ns/day | FAILED |
| 24 | 1,934 ns/day | — | — |
| 32 | 1,883 ns/day (slight regression past 24t) | **2,116 ns/day** ← final best | — |

`-update gpu` fails outright for this system: "Update task can not run on the GPU... Virtual sites are
not supported" — Martini protein backbones inherently use virtual sites. At 16 threads 2 GPU was slower
than 1 GPU (small-system under-saturation), but at 32 threads 2 GPU pulls decisively ahead. Final best
confirmed config: 32 threads, 2 GPU (2,116 ns/day). `martini-prod-1`'s first block actually ran with the
24t/1gpu config (1,934 ns/day), since it launched before the 32t/2gpu result came in.

**Equilibration (July 24)** — 1 ns (100,000 steps, `dt=0.01`), `-DPOSRES` on protein backbone, single
combined NVT+NPT stage. Completed cleanly in 1m43s (856 ns/day). Final state: temperature 302.9 K
(target 303.15 K, essentially converged); pressure −6.7 bar (target 1 bar, still relaxing as expected for
a freshly re-packed membrane).

</details>

<details>
<summary>Archive: NAMD vs OpenMM — FtsH resident-mode crash full diagnostic chain — cut from CLAUDE.md (resolution kept in CLAUDE.md)</summary>

**FtsH resident-mode crash → run FtsH systems in OFFLOAD (resolved July 17–20)**: NAMD3 GPU-resident
production (`CUDASOAintegrate on`) crashes the FtsH systems with `SequencerCUDA: Atoms moving too fast`,
not fixable with a warm-up. The full diagnostic chain on `full-model`:
- Plain resident first block (job 52301891) died at timestep 361. Suspected a localized FtsH-region
  strain (the only feature `full-model` has that `dome-model`, which crosses this transition fine in
  resident, lacks).
- An offload warm-up (`minimize 5000` + `reinitvels` + 50 ps offload → `step7_0`) helped — the next
  resident block survived to timestep 13,758 (~27 ps) — but then crashed the same way. Not a simple
  local clash a minimization fixes.
- Offload diagnostic (job 52351830) ran a full 1 ns cleanly. Offload uses the same forces, so a broken
  structure would crash it too → the structure is fine; it's a resident-mode numerical fragility
  specific to this large FtsH system.
- Resolution: FtsH systems run production in offload mode (`CUDASOAintegrate off`, 1 GPU / 8 PE),
  ~2 ns/day. The offload warm-up is still used as the first block (`step7_0`).
- Open (never investigated further, now moot — both FtsH systems were rebuilt): whether resident-mode
  speed is recoverable for FtsH systems via `margin`, timestep, or a NAMD build fix.

</details>

<details>
<summary>Archive: Midway3 directory structure (ASCII tree, retired) — cut from CLAUDE.md, all work now on Beagle3</summary>

```
/scratch/midway3/junseo/26summer-research/
├── 9CZ2.cif                          # Original PDB CIF structure
├── 9cz2_cut_open.pdb                 # Intermediate cut structure
├── 9cz2-full-minimized.pdb           # Full minimized structure
├── 9cz2minimized_08jun_01.pdb        # Rajiv's complete structure (no water)
├── step5_assembly.*, step5_input.*   # Root-level CHARMM-GUI files (reference)
├── toppar.str
│
├── alphafold/9cz2/                   # AlphaFold predictions (see archived AlphaFold section above)
│
├── 9cz2_dome_original.pdb            # Dome-only from vanilla 9CZ2.cif ← AF2 visual ref
├── hflk_af2_ranked0_notm.pdb         # AF2 HflK monomer res 79–419 (M1/M2 trimmed)
├── hflk_af2_m3rotated.pdb            # AF2 HflK with M3 rotated
│
├── charmm-gui-7628525516/            # CONTROL SYSTEM — membrane-only CHARMM-GUI build (Midway3-era)
│   └── namd/ — step5_input.psf (632,689 atoms), step6.1-6.6 equil, step7_1-21 (21 ns)
│
├── charmm-gui-9cz2fulldome-8119908655/  # MAIN SYSTEM — 9cz2 full dome + membrane (Midway3-era)
│   └── namd/ — step5_input.psf (1,733,042 atoms), step6.1-6.6 equil configs
│   # NOTE: charmm-gui-9cz2fulldome-8095657229/ was superseded (broken PSF, FtsH chains dropped)
│
├── charmm-gui-monomer-75-7828079160/ # HflC monomer CHARMM-GUI build (POPC membrane)
├── control_system/                   # Empty directory (unused)
├── full_dome/                        # Rajiv's clash-resolution minimization
│
├── namd/                             # RETIRED: no-dome GPU run (Rajiv), step6 equil + step7_2-3 (~2 ns)
├── namd_caslake/                     # RETIRED: no-dome CPU run (Rajiv), step6 equil + step7_2-11 (10 ns)
└── namd-af-singlechain/              # RETIRED: HflC monomer test, step6.1-6.4 only
```

**Beagle3 Staging (old, on Midway3, "awaiting resubmission by Kaylie" workflow — obsolete, do not follow):**
```
/project2/haddadian/junseo/beagle3-jobs/
├── main_equil/namd/          # 9cz2 full dome equilibration, 1,733,042 atoms
├── control_prod/             # Control membrane production, 632,689 atoms
└── af2_dome24/               # Contingency: AF2 dome-24 on Beagle3 bigmem
```

**Retired Systems table:**
| System | Directory | Purpose | Status |
|--------|-----------|---------|--------|
| No-dome 9cz2 (GPU) | `namd/` | Rajiv's no-dome production, GPU | Retired |
| No-dome 9cz2 (CPU) | `namd_caslake/` | Benchmarks + 10 ns production | Retired |
| HflC monomer | `namd-af-singlechain/` | Test stability of AF-generated residues 161-190 in POPC | Retired at step6.4 |

</details>

---

## August 5, 2026 (session 3) — all 5 NAMD systems now exist; full systems rebuilt; submit-script audit

### Both full systems rebuilt and moved onto Beagle3

`full-model` (CHARMM-GUI `8553087068`, 1,916,043 atoms) and `full-bact` (`8553086741`, 1,809,634 atoms),
both from `~/Downloads/`. Identified `8553086741` as the composition-#2 counterpart from its lipid counts
before touching anything — protein content is identical between the two (12 HflK 79–419, 12 HflC 1–329,
12 FtsH 1–120), so the lipid comparison is clean.

**FtsH is 1–120, not the AF3 644.** I flagged that this does not clear the objection that retired the
original full systems — no ATPase, no protease domain. User's decision: "1-120 is enough." Proceeded.

`full-bact/namd/` already held the superseded build, so it was **archived, not overwritten**:
`full-bact/superseded_ftsh31-97/{namd,gamd}` (27 GB + 7.5 GB, 40 ns). Same-filesystem rename, instant,
nothing deleted, no job was using it.

Both got: `CUDASOAintegrate off` patched into all 7 `.inp` files (CHARMM-GUI omits it from every
download), `run_equilibration_gpu.sh` from the proven run, and full validation that every referenced
toppar/restraint/PSF/PDB path resolves. Queued as **53084099** / **53084100**.

⚠️ Both carry a stray 37th segment `PROI` — one free-floating capped LEU 9. Build artifact, harmless,
but it breaks the "36 segments" assumption.

### Submit-script audit found three defects

Asked to verify the scripts against past *successful* jobs. Compared every NAMD/GaMD script:

1. **`--exclude` drift recurred on the GaMD side** — all four `gamd-equil*.sh` (control, dome-bact) were
   missing `beagle3-0006`, the node that kills jobs in 1–2 s writing zero output. Two were live jobs due
   for post-maintenance resubmission. **The July audit command missed them because it globbed
   `*/gamd/*.sbatch` and the GaMD scripts are `*.sh`.**
2. **`dome-model/namd/job-submit-beagle3.sbatch` lacked `--constraint=a100`** — the only one.
3. **36 h equilibration walltime was too tight.** The reference job (52188527) is a genuine success —
   `COMPLETED`, exit 0, `End of program` — but took **30.6 h of 36 h**. The new builds are 6.8% larger
   → ~32.7 h, i.e. ~3.3 h margin on a 30-hour sequential 6-step run. Raised both to 48 h
   (`beagle3-prio` MaxWall, verified) and resubmitted `full-model`. **This one was only visible by
   checking elapsed time, not exit status.**

All 11 scripts now clean on both checks.

### Maintenance outage found while queuing

**`maint_20260806`: Aug 6 08:00–20:00, all 44 beagle3 nodes + bigmem + all midway3.** Surfaced because
the 36 h equilibration wouldn't schedule (`ReqNodeNotAvail, Reserved for maintenance`). It will kill
`control-prod` (~14 h) and both GaMD segment-2 jobs (~28 h each) mid-run. `gamd-dome-model-equil` ends on
its own at Aug 6 01:53, before the outage.

### Resubmitted idle production, staged the GaMD restarts

`dome-model` (56 ns) and `dome-bact` (80 ns) production had both finished clean and sat idle — the
recurring failure mode. Resubmitted as 53084218 / 53084219.

Wrote `/scratch/beagle3/junseo/make_gamd_restart.py` to generate the next GaMD segment, enforcing the
three requirements that have each been gotten wrong before: new `outputName` (+ refuses if the target
`.dcd` exists), `accelMDGRestart on` **with** `accelMDGRestartFile`, and `firsttimestep` = absolute step
from `.restart.xsc` column 1 (**not** the `.gamd` `Vn` field). Asserts
`firsttimestep + run == 22,500,000`. Refuses to run while a job is live, since the `.xsc` is still moving.

**Sandbox-testing it caught a real bug** — a regex ate the `--job-name=` prefix, emitting
`#SBATCH gamd-control-equil3`, which Slurm rejects. Also: Beagle3 login nodes are python 3.6, so
`subprocess.run(capture_output=)` fails.

### GaMD reality check

Production GaMD is **0 ns on all three systems**. The 22.5M-step schedule is *equilibration*.
`control` 83%, `dome-bact` 36%, **`dome-model` 21% and still in the cMD phase (E = k = 0)** — its 9.9 GB
DCD is plain conventional MD, not GaMD data. Corrects the Aug 3 note claiming `dome-bact` was still in
cMD; it has since crossed into the boosted phase.

---

## August 5, 2026 (session 2) — v6 read out and failed; found v2 was minimized with the wrong electrostatics

### v6 completed — and softening the elastic network made everything worse

v6 (53032654) ran 50 ns clean at 2,203 ns/day. Verified past the exit code, since `COMPLETED` has twice
before meant nothing here: full-length trajectory, `=== done ===` reached, all three stages ran. The
`step251b/c.pdb` dumps in that directory are **EM-stage** constraint snapshots (routine for an
`insane`-packed system starting at Epot 2.3e16), not dynamics failures.

| | Rg_xy start | ΔRg_xy | ΔRg_z | RMSD |
|---|---|---|---|---|
| AA dome-model (ref) | 79.65 | −3.40 | +1.72 | 8.74 |
| v2 (ef 700) | 79.51 | −1.90 | −0.94 ✗ | 13.17 |
| **v6 (ef 300)** | 78.70 | **−1.33** | **−1.60** ✗ | **20.34** |

Every metric got worse. **Elastic stiffness was not the limiting factor.** v6 did confirm one thing:
it starts uncollapsed (78.70), so the Go family's pre-compaction is specific to the Go contact map,
not a general CG artifact.

Recomputed all six with a single script to keep them on one footing — it reproduced the recorded v1–v5
values to **±0.00**, which is what makes the v6 number trustworthy. (Basis: 8,040 `BB` beads, geometric
Rg — MDAnalysis cannot guess Martini bead masses, so mass-weighting would silently use garbage.)

### The user's pushback was right, and it exposed a worse problem

Asked why v6 went *softer* when v2's RMSD (13.17) already exceeded AA's (8.74) — i.e. the data said
*more* restraint, not less. Correct. The RMSD time course confirms it: v2 crosses AA's value at ~7 ns
and plateaus ~50% above it; v6 was still climbing at 32 ns.

Built v7 (ef 1500) and v8 (ef 3000) on that reasoning. **Then, while comparing our mdps against a new
CHARMM-GUI protein build, found the reasoning was resting on a confound.**

### v2 is the ONLY variant minimized with the wrong electrostatics

From the actual run logs, not the mdp files:

| variant | EM coulombtype | ε_r |
|---|---|---|
| v1, v3, v4, v5, v6 | Reaction-Field | 15 ✅ |
| **v2** | **PME** | **1** ❌ |

`martini-dome-cg-flatbottom/em.mdp` was never updated when the rest were fixed July 23. `eq`/`md` mdps
are byte-identical across variants, so it is EM-only — but ε_r = 1 means electrostatics ~15× too strong
on a membrane full of anionic lipids.

**This invalidated three things stated earlier the same session:**
- "v2 is best" — rests on a run with a bad starting structure.
- "v6 = v2 with only `ef` changed" — true of the topology (verified with `cmp` on all 24 chains), false
  of the protocol. **Verifying topology is not enough; verify the mdps too.**
- Both one-variable comparisons behind "more restraint improves everything" (v1→v2, v6→v2) cross the EM
  change. The trend is not established.
- Also retracted: the inference that the reversed ΔRg_z points at the CG membrane (`TLCL1`→`TOCL`).
  ΔRg_z tracks restraint level monotonically, so protein restraints do influence it.

### Submitted v7 / v8 / v9

| job | variant | `ef` | purpose |
|---|---|---|---|
| 53083065 | v9 | 700 | v2 with corrected EM — measures the damage |
| 53082040 | v7 | 1500 | 1/√k extrapolation toward AA's RMSD |
| 53082042 | v8 | 3000 | brackets the expected turnover |

All derived from v2's topology by rewriting only the rubber-band force constant (the v4/v5 approach),
paired with v6's corrected mdps. 26,189 bonds rewritten each, verified byte-identical to source once the
force constant is normalized away. `700.0` occurs nowhere else in the `.itp`s, so exact-value matching is
safe — the other constants in that block (5000/7500/2500/1000000) are real bonded terms.

**On the `ef` numbers**: 1500/3000 were judgment calls, not derived — said so when asked. A post-hoc
two-point fit gives 947 (linear, unphysical), **1541 (1/√ef — the right scaling for a harmonic
restraint)**, 1182 (log), 3973 (1/ef). 1500 lands on the physical model by instinct; 3000 brackets. But
that fit used v2's off-curve point, so **redo it from v6/v9/v7/v8.**

### CHARMM-GUI protocol: protein changes almost nothing (confirmed on a second protein)

Built **2ZXE** (Na⁺/K⁺-ATPase, multi-chain) as `charmm-gui-8586651827`. Diffed all eight mdps against the
membrane-only build. **Exactly two differences:** the `-DPOSRES` ramp on step6.2–6.6, and `tc-grps`
gaining a `protein` group. Timesteps, step counts, electrostatics, cutoffs, barostat identical —
`gen_seed` differs only because it is the job ID.

This independently confirms the Aug 4 1AFO result on a far larger protein: **protein complexity does not
change the Martini protocol.** Our production `md.mdp` matches CHARMM-GUI on every physics parameter.
Still missing on our side: the `step6.0` soft-core minimization (`free-energy=yes`, `sc-alpha=4`,
`init-lambda=0.01`) and the staged ladder.

### Other work

- Downloaded v6's trajectory locally (`trajectories/martini_sweep/v6/`) — 0–32 ns window, full 50 ns, and
  the equilibration. Caught that `Protein_Membrane` is group **19** in the shared index but **1** in the
  Go index; reusing the v4/v5 extraction script verbatim would have centered on protein-only and produced
  a silently wrong PBC correction rather than an error.
- Wrote `trajectories/load_v1_v6.tcl` — loads all six variants, handles the two-topology split
  (177,845 vs 185,885 atoms), `WINDOW_NS` selects the 0–32 ns AA-matched window or the 0–50 ns
  all-six-shared window. Tested headless.
- **Lesson**: `COMPLETED` + correct topology + correct trajectory can still be an invalid comparison if
  the *protocol* differs. Diff the mdps between variants before treating them as a controlled series.

---

## August 3–5, 2026 — GPU-resident GaMD REJECTED, Martini sweep readout, CHARMM-GUI protein-protocol comparison

### Headline: do NOT migrate GaMD to Chen's resident build — the boost statistics are corrupted

The validation run (job 52975499, `dome-bact/gamd_resident_val/`, 200,000 steps branched from the
static segment-1 restart at step 5,410,000) **completed cleanly and still failed the test.** This is
exactly why it was run instead of trusting the earlier 5,000-step smoke test.

**Thermodynamics agree essentially perfectly:**

| quantity | resident | offload | %diff |
|---|---|---|---|
| potential | −4,836,496.27 | −4,836,863.72 | **−0.008** |
| total | −3,707,490.55 | −3,707,622.58 | **−0.004** |
| temperature | 302.35 | 302.41 | −0.021 |

**The GaMD boost statistics do not:**

| | resident | offload |
|---|---|---|
| DIHED Vmin | **0** | 223,257 |
| TOTAL Vmin | **−2.39e+07** | −5.07e+06 |
| TOTAL sigmaV | **5.18e+06** | 1,139.87 |

Traced to the exact step it happens. Both runs are **identical** on the first statistics line
(Vmax −5.05557e+06, Vmin −5.06679e+06, sigmaV 1144.04) — so both read the restart file correctly.
On the **second** statistics line, resident's `Vmin` collapses: DIHED to exactly `0`, TOTAL to
−2.39e+07. Since `Vmin` is a running minimum it never recovers; `Vavg` then drifts monotonically
(−5.06 → −5.76e+06 over 7 windows) and `sigmaV` grows without bound.

**The corrupted value is not a real sample.** The actual sampled potential energy over that run spans
only −4,839,454 … −4,834,182, and **zero frames** fall below −1e7. A DIHED `Vmin` of exactly `0` reads
like an uninitialized value entering the accumulator.

**Why the energies still matched, and why that's a trap:** `dome-bact` is still in the cMD phase
(E = k = 0), so no boost is applied yet. The dynamics are genuinely fine — the corruption is confined
to the accumulator that will *later* set the boost. Had we switched now, the first boosted step would
have used a `sigmaV` ~4,500× too large, producing a wrong boost and an invalid reweighted free energy
surface. **The earlier smoke test looked clean because it checked energies, not boost statistics.**

**Decision: all three GaMD runs stay on offload.** The ~4 weeks of wall-clock stays unrecovered; not
worth an invalid free energy surface. Resident speed was confirmed real (8.22 ns/day vs ~2.77 offload
at 2 GPU, ~3×) — the problem is correctness, not performance.

**To report to Dr. Chen** — this is a concrete reproduction of the accuracy question emailed Aug 3:
GPU-resident mode feeds a spurious value (0 for DIHED, ~−2.4e7 for TOTAL) into the GaMD statistics
accumulator on the first update after a restart, permanently poisoning `Vmin` and inflating `sigmaV`.
The `ENERGY:` output over the same window is correct, so the bug is in the statistics path, not the
force/integration path. Reproducer: `dome-bact/gamd_resident_val/` +
`compare_resident_offload.py`. **Not yet sent.**

### Martini v4/v5/v6 sweep — and a finding that invalidates the Go family's comparison

**v4 and v5 completed** (52966615, 52966616): 50 ns each, ~2,180 ns/day, 1.9 GB trajectories, verified
by output files rather than exit code. **v6 failed in 1 second** — literal `$SLURM_SUBMIT_DIR` from a
heredoc escaping fault (the same bug that killed the first resident-validation submission; both scripts
were written in the same batch and only one was fixed). Resubmitted as **53032654**.

**Deltas over the matched 0–32 ns window:**

| variant | design | ΔRg_xy | ΔRg_z | RMSD | err |
|---|---|---|---|---|---|
| **AA dome-model** | CHARMM36m, no bias (reference) | **−3.40** | **+1.72** | 8.74 | — |
| v1 elastic | ef 700, no inter-chain | −1.70 | −1.54 ✗ | 16.48 | 1.70 |
| v2 flat-bottom | elastic + 5,015 inter | −1.90 | −0.94 ✗ | 13.17 | **1.49** |
| v3 Go | 10,612 intra + 4,663 inter | −0.14 | +0.50 ✓ | 11.27 | 3.26 |
| **v4** Go intra-only | inter-chain deleted | −0.76 | +0.85 ✓ | **21.27** | 2.64 |
| **v5** Go weak | ε 9.414 → 5.0 | −1.09 | +1.22 ✓ | 14.93 | 2.31 |

Within the Go family, **v5 > v4 > v3** on every metric. v4's RMSD of 21.27 is the **worst of all six** —
deleting the inter-chain contacts reproduced v1's failure mode (chains stay folded but slide), so the
"inter-chain rigidity froze the ring" hypothesis gets only weak support. Contact *strength* mattered
more than contact *coverage*.

**But the absolute values invalidate that whole comparison:**

| variant | Rg_xy start | Rg_xy @32 ns | gap to AA end |
|---|---|---|---|
| AA (reference) | **79.65** | 76.25 | — |
| v1 elastic | 79.00 | 77.30 | +1.04 |
| v2 flat-bottom | 79.51 | 77.60 | +1.35 |
| v3 Go | **76.53** | 76.39 | +0.14 |
| v4 Go intra-only | **75.76** | 75.00 | **−1.26** |
| v5 Go weak | **76.14** | 75.05 | **−1.21** |

**Every Go variant begins production already collapsed** — at ~76 Å, essentially AA's *endpoint*
(76.25), ~3.5–4 Å tighter than AA's start (79.65). They never had the contraction available to
reproduce; equilibration under the Go contact map had already done it. Go builds attractive wells at
native contacts, and 15,275 of them over-pull the assembly tighter than native (a documented
Go-model over-compaction mode). v4 and v5 then finish **below** AA's endpoint.

v1/v2 start where AA starts (79.00, 79.51). **Comparing Go deltas against AA deltas is not a fair
comparison at all** — the Go family's problem is more fundamental than contact strength or coverage.

**Standing conclusion unchanged: v2 remains best on the opening observable**, with its two known
caveats intact (one-sided `low = 0.000` restraints that don't resist closing; reversed vertical
direction). **The AA systems remain the primary evidence.**

**Next test worth running**: lower ε further (v7, ε ≈ 2.5) — but the diagnostic quantity is now
whether it *reduces the pre-compaction at production start*, not the production-phase delta. v6
(soft elastic, ef 300) is elastic-based so it should start near 79 like v1/v2, making it the more
informative outstanding run.

### CHARMM-GUI protein-vs-membrane protocol comparison (build 8579367020, 1AFO)

Goal: does CHARMM-GUI's Martini protocol change when a protein is present? Built **1AFO** (glycophorin
A TM dimer) — chosen after **1A3N hemoglobin failed**, because hemoglobin is soluble with no TM region,
so `step2_orient` never produces a membrane-embedded system. (A separate 1A3N attempt also hit
"No lipid was selected... system is too small" from an XY guess of 10 Å producing an 18.67 Å box
smaller than the protein itself.)

**Answer: it differs in exactly one way — an added protein position-restraint ramp.** The timestep
ladder and step counts are **byte-identical** to the membrane-only build (8542787498):

```
step6.2  -DPOSRES -DPOSRES_FC=1000  -DBILAYER_LIPIDHEAD_FC=200   dt 0.002  500000
step6.3  -DPOSRES -DPOSRES_FC=500   -DBILAYER_LIPIDHEAD_FC=100   dt 0.005  200000
step6.4  -DPOSRES -DPOSRES_FC=250   -DBILAYER_LIPIDHEAD_FC=50    dt 0.010  100000
step6.5  -DPOSRES -DPOSRES_FC=100   -DBILAYER_LIPIDHEAD_FC=20    dt 0.015   50000
step6.6  -DPOSRES -DPOSRES_FC=50    -DBILAYER_LIPIDHEAD_FC=10    dt 0.020   50000
```
(membrane-only: same lines minus the `-DPOSRES` half). Total 4.75 ns.

**Our production `md.mdp` matches theirs** on every physics parameter — integrator, dt 0.02,
reaction-field, `epsilon_r 15`, rcoulomb/rvdw 1.1, potential-shift-verlet, v-rescale, `tau-t 1.0`,
`ref-t 303.15`, parrinello-rahman semiisotropic, `tau-p 12.0`, compressibility 3e-4, nstlist 20. Two
cosmetic differences only: they use 3 thermostat groups (protein/membrane/solvent) vs our 2, and they
auto-tune the pair buffer (`verlet-buffer-tolerance 0.005`) where we pin `rlist 1.35`. Neither is a
problem. (Note: our mdp uses hyphenated keys — `tau-t`, `ref-t` — so a grep for `tau_t` finds nothing.)

**Our equilibration does differ:**

| | ours (`eq.mdp`) | CHARMM-GUI |
|---|---|---|
| stages / total | 1 / 1 ns | 5 / 4.75 ns |
| dt | straight to 10 fs | 2 → 5 → 10 → 15 → 20 fs |
| protein POSRES | 1000 → 0 in one step | 1000 → 500 → 250 → 100 → 50 → 0 |
| lipid headgroup z | **none** | 200 → 100 → 50 → 20 → 10 |

`POSRES_FC` defaults to 1000 in our chain `.itp`s — the *strongest* rung — then production drops it to
zero while the timestep doubles. And our `M3-Lipid-Parameters` lipid `.itp`s contain **no
`[position_restraints]` block at all**, so `-DBILAYER_LIPIDHEAD_FC` is a **silent no-op** for us.

**Not the explanation for the dome contraction** — the AA systems contract too (−3.40 Å), so that's
real physics. At most this affects early strain and contraction rate. All six Martini variants share
the same 1 ns equilibration, so it is a controlled variable and cannot be what separates them.

### Staged equilibration prepared — `scripts/martini_staged_eq/` — NOT applied

Deliberately staged, not applied: changing equilibration mid-sweep would break comparability across
v1–v6. Apply after the sweep reads out.

- `step6.{2,3,4,5,6}_equilibration.mdp` — the ladder, physics inherited verbatim from our
  KALP-validated `eq.mdp`
- `add_lipid_headgroup_posres.py` — patches DPPE/POPG/DOPG (phosphate = bead 2) and TOCL (**both**
  phosphates, beads 2 and 13). Bead indices read off our actual `[atoms]` blocks, not assumed from
  CHARMM-GUI's ordering; hard-fails if an index exceeds the molecule's atom count. Idempotent, writes
  `.bak`. Tested on a scratch copy: correct placement at end of each moleculetype, guard verified.
- Restrains **z only** (`fcx = fcy = 0`) — lateral diffusion and lipid mixing untouched.
- **Fixed in passing**: `eq.mdp` had `compressibility = 4.5e-5` (all-atom water; Martini water is ~7×
  more compressible). Our `md.mdp` already used 3e-4 — `eq.mdp` was the outlier. This was the
  known-unfixed item from Aug 1. The `em.mdp` PME/`epsilon_r` bug is **still open**.

> **Go variants get no protein restraint from this.** v3/v4/v5 topologies contain zero
> `[position_restraints]` — `martinize2 -go` ran without `-p backbone`, so `-DPOSRES` is a no-op there
> (verified). The lipid half still works. v1/v2 are fine.

### Cluster operations

- **`control-prod` and `dome-model-prod` had both gone idle**, neither crashed. `dome-model-prod`
  finished at **44.05 ns** hitting the `MAX_CHUNKS=12` cap after 12 chunks (35h of its 48h);
  `control-prod` finished at **96.53 ns**. Resubmitted as **52976021** and **53032667**. Nothing
  auto-chains across jobs — this is the recurring failure mode.
- **`beagle3-0006` was missing from 5 sbatch scripts**, including `control`'s live production script.
  All 8 scripts now carry `--exclude=beagle3-0028,beagle3-0006`.
- **SSH sockets expired mid-session** (both Beagle3 and Midway3, `ControlPersist 1h`). Hosts were fine
  (port 22 open) — only monitoring went blind; server-side jobs unaffected.

### Tooling gotchas found this session

- **Beagle3's GROMACS binary is `gmx_mpi`, not `gmx`.** `module load gromacs/2025.3` then `gmx` gives
  `command not found`.
- **`-deffnm prod_v` names outputs, not the tpr.** `grompp -o md_v.tpr` means the tpr is `md_v.tpr`;
  `trjconv -s prod_v.tpr` fails. Check the directory rather than inferring from `-deffnm`.
- **macOS BSD `sed` has no `\b`** — a `s/\bgmx /gmx_mpi /g` silently did nothing and the unfixed file
  got submitted. Verify a sed actually changed the file before using it.
- **Write scripts locally and `scp` them** rather than heredoc-ing over ssh — the `\$` escaping fault
  cost three failed jobs across two scripts.
- **Go virtual sites are named `CA`** — 8,040 of them sitting exactly on the BB beads. Any protein
  selection on v3/v4/v5 needs `and not name CA` or every backbone bead renders twice.

### Local trajectories

`trajectories/martini_sweep/{v4,v5}/` — 50 ns each, PBC-corrected (`trjconv -pbc mol -center`),
decimated to 1 ns/frame (51 frames, 38 MB), plus topology, `martini_ff/`, and `cg_bonds.tcl`. They
share v3's 185,885-atom structure with the 8,040 Go virtual sites — **v1/v2's topology will not load
them**. `trajectories/` total is now 46 GB, gitignored.

---

## July 28 – August 3, 2026 — Martini restraint-scheme investigation, FtsH gap found, /project2 outage resolved

### Session opening: queue empty after 4 days — nothing had crashed

Found the Beagle3 queue empty. `sacct` showed **every job had completed cleanly (exit 0) and simply
self-stopped** at its wall-time budget or the 12-chunk cap, exactly per `run_prod_gpu.sh`'s design —
nothing auto-chains across jobs, and nobody had resubmitted for 1–4 days. Cumulative at that point:
control 72.53, dome-model 32.05, dome-bact 32.00, full-model 37.05, full-bact 20.05 ns; martini-prod-1
finished a 12h block at 2,318 ns/day.

**Real bug found**: all 4 GaMD equilibration jobs submitted July 24 had `FAILED` within 2–3 seconds.
NAMD's own log: `ERROR: Multiple definitions of 'margin'`. The shared template had `margin 5` at line 12
(restart setup) colliding with `margin 3` pasted in at line 156 inside the GaMD block. **All four had
never run a single step** despite appearing "submitted" in the status table for days.

Second, independent bug in two of them (`dome-bact`, `dome-model`): `accelMDGRestart on` with no
`accelMDGRestartFile`, pointing at stale `gamd-equil.restart.gamd` stubs (step ~700k–710k, ~1.4 ns into a
3 ns prep phase — nowhere near converged, likely leftover benchmark artifacts). User chose fresh start
over resuming the stubs.

**Lesson recorded**: a job vanishing from `squeue` within seconds is easy to mistake for "still running" —
verify GaMD submissions via `sacct` state, not just that `sbatch` accepted them.

### Directory reorg completed for the reachable systems

Applied the long-pending `{namd,gamd}/` split under `/scratch/beagle3/junseo/`:
- `control` was fully flat (465 items at top level) → split into `namd/` + `gamd/`
- `dome-bact`, `full-bact` had `namd/` with GaMD files commingled inside → carved out `gamd/`
- **Shared inputs symlinked, not duplicated** (`gamd/step5_input.psf -> ../namd/step5_input.psf`, same for
  `toppar/`) — avoids duplicating 100–300 MB PSFs while keeping every relative path working. Verified by
  reading `run_prod_gpu.sh` and the sbatch scripts in full first: all use relative paths + `$SLURM_SUBMIT_DIR`,
  no hardcoded absolutes.

**Gotcha found the hard way**: symlinking the *static* shared inputs is not enough. `gamd-equil.inp`'s
`set inputname step7_N.restart;` also reads that specific **branch-point restart trio**
(`.coor/.vel/.xsc`) by bare relative name, and those live in `namd/`. Missed initially for all three
systems; caught and fixed before any job actually launched. **Any future GaMD setup in this structure must
symlink its restart trio into `gamd/` too.**

### `beagle3-0006` is a bad node

Four jobs died instantly (1–2 s, zero output files, `sacct` Reason=None) — all on `beagle3-0006`, which
reported `STATE=MIXED`, i.e. healthy as far as SLURM knew. Resubmitting elsewhere worked immediately.
**Added `beagle3-0006` to `--exclude` in every production/GaMD sbatch.** Distinguishing feature vs a config
error: config failures still write a `.err`; this node produced *no output at all*.

### `-bonded gpu` benchmark — Dr. Haddadian's ChatGPT thread

Haddadian forwarded a ChatGPT conversation suggesting speedups for the Martini system. Checked each point
against what was already done: GROMACS version (2025.3, already newer than suggested), 1 MPI rank + OpenMP
(already), thread/GPU sweep (already done July 24), `-update gpu` (already known-blocked — Martini virtual
sites are unsupported by GPU-resident update), `-pme gpu` (**not applicable at all** — this system uses
`coulombtype = reaction-field`, not PME), bead count (already known: 168,577).

Only genuinely untried item was **`-bonded gpu`**. Benchmarked it properly (5,000 steps, `-resetstep 1000`,
32t/2GPU, on the current elastic-network topology):

| config | ns/day |
|---|---|
| baseline `-nb gpu` | **2,063.8** |
| `+ -bonded gpu` | 1,930.5 |

**~6.5% *slower*.** Nothing in the thread improved on the existing config.

### FtsH is only ~10% modeled — previously unnoticed

User spotted that 9CZ2's protease is incomplete. Traced it through every stage with sequence verification
(not chain-letter assumptions):

| stage | FtsH resolved |
|---|---|
| **deposited 9CZ2 CIF** | **residues 31–97 (67 of ~644)** — confirmed for label_asym `Y`, `AA`, `BA`, `JA` |
| Rajiv's `9cz2-full-minimized.pdb` | 1–120 (verified 120/120 sequence match to the FtsH FASTA) |
| AF3-updated `dome_m3_af3_ic_minimized_final.pdb` | 31–97 |
| current `full-model`/`full-bact` PSFs | 31–97, all 12 FtsH segments |

**The gap is inherent to the cryo-EM map** — at 4.4 Å the entire cytoplasmic AAA+ ATPase ring and M41
protease domain were unresolved. Only an N-terminal TM anchor made it in. All prior gap-filling work
(HflK M1–M3, HflC 161–190) was dome-only; **FtsH's incompleteness had never been addressed**.

FtsH segment naming in the current systems (determined empirically from residue ranges, since CHARMM-GUI's
`PRO*`/`PRA*` naming doesn't map to the older documented `Y,Z,0-9` scheme):
`PRAA`–`PRAJ` + `PROY` + `PROZ` = 12 segments, all resid 31–97, 1090 atoms each.
`PROY`/`PROZ` are easily mistaken for dome chains — they're FtsH, distinguished only by residue range.

**AF3 hexamer job built**: full 644-residue sequence × 6, with the resolved 31–97 fragment embedded as a
custom template. Two failures fixed along the way:
1. Job name rejected — commas not allowed (letters/numbers/spaces/dashes/underscores/colons only)
2. `Model inference failed` — my hand-built template mmCIF included **explicit hydrogens** (the source is
   an all-atom CHARMM36m NAMD structure; real deposited templates never have H). Rebuilt heavy-atom-only
   (1090 → 544 atoms) and it uploaded successfully.

**Correction recorded**: I initially told the user the AF3 Server can't accept custom templates. User
pushed back; checked the official `google-deepmind/alphafold` `server/example.json` and **they were right** —
the `alphafoldserver` dialect does support a `templates` field with raw `mmcif` + `queryIndices`/
`templateIndices`. (`maxTemplateDate` is capped at 2025-02-03; a later value is silently clamped.)

**Decision (Aug 2)**: the user is rebuilding both full systems in CHARMM-GUI with an AlphaFold-completed
protease. Existing `full-model`/`full-bact` are **dismissed**; their jobs were cancelled and only
`control` + dome systems run until the rebuild lands.

---

### The Martini investigation (the session's main thread)

#### v1 was scientifically invalid — no elastic network at all

User reported the dome dispersing in the ~1131 ns `martini-prod-1` trajectory. Checked the actual command
recorded in the `.itp` header: `martinize2 ... -p backbone -maxwarn 100` — **no `-elastic` flag**. Confirmed
by grep: the `[ bonds ]` section had only sequential backbone bonds, no rubber-band network, and no
separate `_en.itp` anywhere.

`-p backbone` restrains only *local secondary structure*. Nothing held tertiary fold or the 24-chain
quaternary arrangement — beyond backbone connectivity everything relied on Martini's deliberately soft
nonbonded potential. **The entire original production run is unusable for structural analysis.**

Fix: regenerated all 24 chains with `-elastic`. **Verified `-elastic` does not change output coordinates**
(diffed old vs new `chain_X_cg.pdb`, byte-identical), so only topology needed swapping — the packed
membrane system (`fudge 0.9`, corrected z-position) remained valid. `.itp` grew 3,983 → ~5,085 lines.

#### Then a PBC artifact masqueraded as continued collapse

After the fix the dome still *looked* shattered. Rg was stable, so checked for wrapping: **641 of 1,228
frames had atoms jumping >5 nm between consecutive frames, max 271.4 Å ≈ the full box width.** Classic
periodic-wrapping signature, which `cg_bonds.tcl` renders as bonds drawn straight across the box.

`trjconv -pbc mol -center` → **0 of 1,228 frames** with jumps, max displacement 29.5 Å (physically normal).
**All Martini production trajectories must be PBC-corrected before visualization.**

#### But the user's structural observation was real

User then observed "tertiary structure gets less organized" — Rg alone can't see this (it measures size,
not organization). Measured both:

| | whole-assembly RMSD (unfitted) | per-chain RMSD (fitted) |
|---|---|---|
| v1 @ 1228 ns | **26.7 Å** | ~12 Å, still climbing |

Whole-assembly deviation is >2× per-chain — chains stay folded but **slide relative to each other**. Root
cause: the deliberate design choice of *per-chain elastic only, no inter-chain restraint*, combined with
Martini nonbonded being too soft to hold a 24-chain assembly.

#### v2 and v3 built

- **v2 (flat-bottom)** — v1's elastic network **kept**, plus **5,015 inter-chain distance restraints**
  derived from backbone pairs within 8 Å in the native packed structure. Zero force to native+3 Å, harmonic
  to +8 Å, then linear. Verified active in GROMACS (`There are 5015 distance restraints`, live `Dis. Rest.`
  energy term). Production: **1,084.78 ns**, T = 303.152 K, P = 1.006 bar, mean violation ~0.0026 nm/restraint.
- **v3 (Go-Martini)** — `martinize2 -go` on the **whole complex**, which **replaces** the elastic network
  entirely (no `-elastic`; zero rubber-band entries in `molecule.itp`). **15,275 contacts: 10,612 intra +
  4,663 inter-chain.** Production: **1,703.5 ns**, T = 303.150 K, P = 0.9998 bar.

Cross-validation: my KD-tree 8 Å backbone search (5,015 inter-chain pairs) and Go-Martini's own OV+rCSU
algorithm (4,663) independently agreed that the dominant contacts are **adjacent ring neighbours**
(A-B, C-D, K-L…), matching real dome geometry.

#### Go-model build: three real obstacles

1. **OOM-killed twice locally.** Whole-complex contact map for 126,696 atoms exhausted the Mac (8.9 of
   10 GB swap consumed; Docker's 7.75 GB ceiling was not the real limit — the machine itself ran out).
   Moved to Beagle3 with `--mem=200G`; took 50 min.
2. **`UnicodeDecodeError` on import.** First cluster attempt reported `COMPLETED` exit 0:0 but crashed in
   10 seconds — the venv had been built on the system python 3.6 with an ASCII locale, which can't read
   vermouth's citation `.bib`. Rebuilt on `python/3.11.9` + forced UTF-8.
   **Another instance of `COMPLETED` not meaning success.**
3. **Atom-serial hex overflow.** `dome_m3_af3_ic_minimized_final_noftsh.pdb` has 126,696 atoms; past 99,999
   the writer switched to **hexadecimal** serials (`186a0`), which vermouth's parser rejects. Fixed with
   wrapped decimal renumbering.

**Membrane system built without re-running `insane`**: the Go structure's atoms 1–18264 are byte-identical
in order and coordinates to the original protein block, with the 8,040 `CA` virtual sites appended at the
end (18265–26304). So the 8,040 sites were **inserted into the already-validated packed system** rather
than repacking — repacking would have doubled bead density at every backbone position and invalidated the
tuned `-fudge 0.9` exclusion. Verified CA sites coincide exactly with their BB beads and are proper type-1
virtual sites (`18265 1 1`, `18266 1 4`, …).

#### Go-Martini's cost, and a T-coupling bug

- **`grompp` takes ~1 hour.** Go creates **one atomtype per residue (8,040)**, so GROMACS builds a
  ~66-million-entry nonbonded matrix. The resulting `.tpr` is **703 MB**. Both the eq and production
  `grompp` pay this — the first attempt died at a 2h wall limit mid-way.
- **`make_ndx` group numbers are NOT stable across systems.** I assumed they were; the Go system emitted
  separate `NA`, `CL` *and* combined `ION` groups (the original had only `ION`), shifting numbering so
  `name 19 Protein_Membrane` silently renamed the **CL** group. Result: chloride in both thermostat groups
  → `Fatal error: Atom 185087 in multiple T-Coupling groups`. Fixed by **generating the index directly from
  resnames in Python** with an assertion that the two groups partition the system with zero overlap
  (62,102 + 123,783 = 185,885 ✓). The error surfaced ~1h late because `grompp` validates groups only after
  building the matrix.
- `-DPOSRES` in the Go eq was a **no-op** — `martinize2 -go` was run without `-p backbone`, so the topology
  has no `[position_restraints]`. Removed; Go contacts serve that role.

---

### AA-vs-CG comparison — the key scientific result

User asked which restraint scheme is most biologically accurate. Built a like-for-like comparison:
**AA `CA` atoms vs CG `BB` beads, 8,040 each, mapping 1:1** — so the two representations are directly
comparable. AA is the reference: CHARMM36m, zero structural bias, and **verified zero restraints in
`step7_production.inp`**.

**The headline finding — the all-atom systems contract too:**

| system | Rg(ring plane) | change |
|---|---|---|
| **AA dome-model** (32 ns) | 79.65 → 76.19 Å | **−3.40** |
| **AA dome-bact** (44 ns) | 79.64 → 78.15 Å | **−1.88** |

Both **plateau** (dome-model by ~13 ns, dome-bact by ~26 ns), so the windows are long enough to trust.
**The dome closing seen in CG is real physics, not a restraint artifact.**

**Ranking over a matched 0–32 ns window:**

| variant | ΔRg_xy (ring) | ΔRg_z | RMSD |
|---|---|---|---|
| **AA dome-model (ref)** | **−3.40** | **+1.72** | **8.74** |
| v1 elastic | −1.70 | −1.54 ✗ | 16.48 |
| v2 flat-bottom | **−1.90** ✓ | −0.94 ✗ | 13.17 |
| v3 Go | −0.14 ✗ | +0.50 ✓ | 11.27 |

**No clean winner:**
- **Ring width** (the opening observable): v2 best; **v3 essentially fails** — moves −0.14 Å where AA moves −3.40
- **Vertical direction**: only v3 gets the sign right; v1 and v2 both compress where AA elongates
- **Total deviation**: v3 closest; v1 nearly 2× AA's motion

Two caveats recorded honestly:
- **v2's advantage is partly luck.** Its restraints use `low = 0.000`, so the zero-force zone extends to
  zero separation — they resist chains moving *apart* but exert **nothing** against closing. They're
  one-sided, and closing happens to be the direction AA moves.
- **v3 pre-compacted during equilibration.** It starts production at Rg_xy 76.53 — essentially AA's
  *endpoint* (76.25) — then holds. It lands on a plausible value by pinning rather than by dynamics.

**Conceptual point for the opening question**: any *inter-chain* bias is question-begging, since dome
opening is quaternary motion. Elastic is applied intra-chain only in this project (chains were martinized
separately, so the tool never saw two chains at once). Go's advantage is that contacts **break and re-form**,
so an intra-chain hinge can open — relevant because Paper 2 reports the opening originates in the
**coiled-coil domain**, i.e. potentially an intra-chain hinge that an unbreakable elastic spring would suppress.

### v4/v5/v6 sweep submitted

Realised the AA window is only 32 ns, so **50 ns CG runs suffice** (~35 min each at ~2,000 ns/day) instead
of the 1,000+ ns production lengths. A sweep is a few GPU-hours, not days.

| variant | change | isolates |
|---|---|---|
| **v4** (52966615) | Go intra-chain only — 4,663 inter-chain contacts deleted | is inter-chain rigidity what froze ring width? |
| **v5** (52966616) | Go with ε 9.414 → 5.0 on all 15,275 | is it contact *strength* rather than coverage? |
| **v6** (52967586) | v2 with elastic ef 700 → 300 | does softer stiffness fix the reversed vertical direction? |

v4 and v5 were derived from v3's existing topology by editing **only `go_nbparams.itp`** — no `martinize2`
rerun, and each isolates exactly one variable. v6 is drop-in compatible with the v1/v2 structure (verified
matching bead counts and moleculetype names), so it skips Go virtual sites entirely and its `grompp` is fast.

**User caught a design error in v6.** My first version was elastic-only at ef=300 with *no* inter-chain
layer — i.e. *less* restraint than v1, which already disorganized (RMSD 16.48). It would have disorganized
further, making `Rg_z` uninterpretable and unable to answer the question it was designed for. Cancelled
before it started and rebuilt as **v2 with softer springs**, changing only stiffness.

Also noted: **v1 is not uniformly a failure** — its ring contraction (−1.70) is closer to AA than v3's
(−0.14). It fails on *organization* (RMSD ~2× AA), which is why that number can't be trusted.

---

### `/project2` outage — resolved via Midway2

`/project2/haddadian` was unreachable from **both** Beagle3 and Midway3 for ~5 days (empty root-owned stub
dated 2023 — automount not attaching), blocking `dome-model`/`full-model` jobs and Rajiv's analysis scripts.
Data confirmed intact throughout.

**Resolution**: `/project2` is served by the **`midway2_cap`** filesystem — it *is* Midway2's storage
(confirmed via `mount | grep project2` on Midway3). So **Midway2 has native access and is the authoritative
host**, not a fallback. Added a `Host midway2` block to `~/.ssh/config` mirroring `midway3` (backup at
`~/.ssh/config.bak-20260802-011715`); user opened the socket and `/project2` was immediately readable.

**`dome-model` recovered and migrated off `/project2`:**
- Essentials first (~535 MB: PSF/PDB/`toppar`/restart trio/ledger/scripts) so jobs could resubmit
  immediately, then 13 GB of DCDs backfilled separately
- Now at `/scratch/beagle3/junseo/dome-model/{namd,gamd}/` — **permanently free of the `/project2` dependency**
- Production resumed from `step7_32` (job 52900855); GaMD branched from `step7_20` (job 52901280),
  matching `dome-bact`'s branch point so the composition comparison stays aligned

Rajiv's analysis directory also became readable — more variants than previously logged:
`com_lipids.py` **and** `new_com_lipids.py`, `lipid-prox-com.py`, `com-lipid-prox.tcl`, and per-protein
TCL variants `lipid-prox-{FtsH,HflK,HflC,opening}-{namd,gamd}.tcl`.

### GaMD 96h timeouts — proper continuation

`gamd-control-equil` and `gamd-dome-bact-equil` both hit their 96h wall at exactly 4d00h. A naive resubmit
would have **destroyed data**: `outputName` was unchanged and segment 1 had left a **9.35 GB
`gamd-equil.dcd`**. Built segment-2 configs that:
- write to `gamd-equil2.*` (preserves segment 1)
- set `accelMDGRestart on` **with** `accelMDGRestartFile` (the missing-pairing bug that killed these in July)
- set `firsttimestep` to the true absolute step so cMD/equilibration phase boundaries evaluate correctly
- `run` only the remaining steps

| | last step | boost state | remaining |
|---|---|---|---|
| control | 12,320,000 / 22.5M | **active** (E, k nonzero — past cMD) | ~80 h |
| dome-bact | 5,410,000 / 22.5M | **not computed** (E, k = 0, still in cMD) | **~302 h ≈ 12.5 days** |

dome-bact is 2.2× slower per step (0.064 vs 0.028 s/step) — it carries protein (1.74M atoms) vs control's
633k membrane-only. Note the `.gamd` file's `Vn` field is samples in the *current statistics window*, not
the absolute step (windows reset every 1.5M steps).

### CHARMM-GUI protocol comparison — two real mdp bugs found

User supplied a fresh CHARMM-GUI Martini build (`charmm-gui-8542787498`) with its official README/mdp
ladder. Comparing against our files found:

1. **`em.mdp` uses the wrong electrostatics.** Ours: `coulombtype = PME`, **no `epsilon_r`** (defaults to 1),
   `rcoulomb/rvdw 1.2`. Martini 3 is parameterized with **`epsilon_r = 15`** and reaction-field at 1.1 —
   which our own `eq.mdp`/`md.mdp` correctly use. So EM minimizes under electrostatics ~15× too strong,
   and the file's own comment ("matches martini_md_template.mdp for consistency") is wrong.
2. **`eq.mdp` uses all-atom water compressibility.** Ours: `4.5e-5` (CHARMM36 water). Martini water is a
   4-to-1 bead, ~7× more compressible — CHARMM-GUI and our own `md.mdp` both use **`3e-4`**.
3. **We skip the whole gradual ladder.** CHARMM-GUI does soft-core min (`free-energy`, `sc-alpha=4`) +
   regular min + **5 staged equilibrations** ramping dt 0.002→0.020 while releasing lipid-headgroup
   z-restraints (`BILAYER_LIPIDHEAD_FC` 200→100→50→20→10) over ~4.75 ns. We do 1 min + 1 ns at dt=0.01,
   then jump straight to dt=0.02 production.

**Our production `md.mdp` is correct** — matches CHARMM-GUI almost exactly. These are eq/EM issues, and
they are *not* the cause of the dome disorganization (that was definitively the missing elastic network),
though they could contribute to the early transient. **Not yet fixed** — user chose to keep the v2/v3 runs
moving rather than divert.

### RCC contact: CPU-only jobs on GPU nodes

Dossay Oryspayev flagged 1 CPU-only job >1800 s on the GPU partition. Identified as **52831054**
(`martinize-go-dome`, 50 min, 8 CPU, 200 GB, no GPU) — the Go contact map. Found the fix: Beagle3 has a
**`beagle3-bigmem`** partition, 4 nodes, **512 GB each, no GPUs, all idle** — strictly better for this work
than what was being done. All subsequent CPU-only jobs (`trjconv`, `grompp`-only) routed there.

### Helping Juliana Steier — GaMD in GPU-resident mode

Haddadian connected Juliana, who was hitting `atoms moving too fast` with GaMD + `CUDASOAintegrate on`
using our Chen build. Compared her config against our verified-working one; her **submit script is
essentially identical** to ours (same `+p16 +devices 0,1`, full path to Chen's binary, `cuda/11.5`), so the
entire delta is in the `.conf`:

1. **`fullElectFrequency 2`** vs our `1` — multiple timestepping conflicts with the resident integration loop (prime suspect)
2. **wrapping disabled** (`#wrapAll on` commented out; NAMD's default is *off*, so commenting it out genuinely disables it)
3. **`pairlistdist 14`** vs our `16` (2 Å vs 4 Å buffer over cutoff 12)

Also passed along that our own FtsH systems hit this exact error in resident mode and it was **not** fixable
by tuning or by a minimize/reinitvels warm-up — offload mode is the working fallback. Shared files staged at
`share_gamd_resident/` (working `.inp`, `.sbatch`, README).

### Local trajectory organization

Consolidated ~33 GB into `trajectories/` (gitignored), with `README.md` covering load commands, selection
strings, and the non-obvious gotchas:

```
trajectories/
├── namd/{dome-model,dome-bact,full-bact,full-model}/
└── martini/{v1_elastic,v2_flatbottom,v3_go}/
```

Verified all three Martini variants load with correct frame counts (1229/1085/1704) **before** deleting
sources; removed ~1.6 GB of genuinely redundant files. Each variant folder carries its own topology and
`cg_bonds.tcl`. Later found the `.top` files pull in **31 `#include`s** (`martini_ff/` ×7,
`martini_chains/` ×24, plus Go-specific files) which I had not copied — fixed and verified all resolve.

**Visualization gotchas recorded**: v3_go needs its **own** `.gro`/`.top` (185,885 atoms vs 177,845 — 8,040
Go virtual sites); `cg_bonds -top` requires a `./` prefix (the script splits the argument on `/` to find
includes); VMD's `protein` macro is unreliable on CG beads (they're `BB`/`SC1`, not `CA`/`N`/`C`) — use
`not resname DPPE POPG DOPG TOCL W NA CL`; cardiolipin is `TOCL` in Martini but `LOACL1`/`TLCL1` all-atom.

### Decision: move GaMD to GPU-resident mode (Chen's build) — validating first

All three GaMD runs were still **offload on stock NAMD**, because stock NAMD FATAL-errors on
`CUDASOAintegrate` + `accelMD`. Chen's `haochuan/gpu_accelmd_2` branch fixes that and was smoke-tested
back in July (5,000 steps, 8.57 vs ~0.87 ns/day ≈ 10×), but **no production GaMD had ever been migrated
to it.**

The case for switching is large:

| | step | remaining | offload ETA | resident ETA (~10×) |
|---|---|---|---|---|
| `control` | 12.85M / 22.5M | 9.7M | ~75 h | ~8 h |
| `dome-bact` | 5.64M / 22.5M | 16.9M | **~300 h (12.5 d)** | ~30 h |
| `dome-model` | 2.17M / 22.5M | 20.3M | **~360 h (15 d)** | ~36 h |

≈ **4 weeks of wall-clock** across the three.

**Timing observation that favours acting now**: `dome-bact` and `dome-model` both still show **E = k = 0**
— still in the cMD phase, boost parameters not yet computed. That's the cleanest moment to change engines,
since there are no accumulated boost statistics to perturb. `control` has active boost
(E = 150011, k = 1.57e-4), so switching it mid-stream is a more meaningful change.

**Tension noted and surfaced**: the email drafted to Dr. Chen this same session says *"we'd like to
understand this before committing production runs."* Switching immediately would contradict that, and the
build has only ever been smoke-tested here. **User chose to validate first.**

**Validation design** (job 52973301, `dome-bact/gamd_resident_val/`):
- Branches from `dome-bact`'s **segment-1** restart (step 5,410,000) — a *static* file. Deliberately not
  `gamd-equil2.restart.*`, which the live job is actively writing.
- 200,000 steps (0.4 ns) in resident mode on Chen's binary, all other physics/GaMD parameters identical.
- **The offload reference is free**: the running job (52955068) already logged the identical step range, so
  its energies serve as the control — no need to burn GPU re-running offload.

**What is actually being compared** (script `compare_resident_offload.py`, uploaded and format-verified
against `ETITLE:` field positions):
- Langevin dynamics is stochastic, so the two trajectories **will** diverge — step-by-step agreement is
  neither expected nor the test. **Ensemble averages** are.
- Potential/kinetic/total energy, temperature, pressure (with stdevs)
- **Vmax, Vmin, Vavg, sigmaV for both DIHED and TOTAL boosts** — the decisive numbers, since these set the
  boost and therefore the reweighted free energy surface
- Real-workload ns/day, replacing the 5,000-step smoke-test figure (short enough that startup overhead
  could distort it)

**Reading criterion**: energies within ~0.1% and sigmaV within a few percent ⇒ engines equivalent, switch
all three. A large sigmaV divergence would mean the boost itself differs — exactly the concern raised to
Chen, and a reason not to switch.

**Email to Chen** (drafted, thanking him for the branch link) asks specifically whether any accuracy
tradeoff is known for GaMD in resident mode — noting that resident/offload equivalence is understood for
conventional MD, but the boost depends on running statistics accumulated on the fly, and it is unclear
whether the resident reorganization changes how or when those are collected.

### Status at session close

**Running**: `control-prod`, `dome-bact-prod`, `dome-model-prod`, `gamd-control-equil2`,
`gamd-dome-bact-equil2`, `gamd-dome-model-equil`.
**Queued**: v4/v5/v6 Martini sweep (52966615 / 52966616 / 52967586); resident-mode GaMD validation (52973301).
**Cancelled/superseded**: `full-bact-prod`, `gamd-full-bact-equil` (FtsH protease rebuild pending).

Cumulative NAMD: control 84.53 → 85.53+, dome-bact 68.00, dome-model 32.05 (just resumed), full-bact 40.05
(frozen, superseded), full-model 37.05 (frozen, superseded).

GaMD progress: control step 12.85M/22.5M (**boost active**), dome-bact 5.64M (cMD), dome-model 2.17M (cMD).

**Open items for next session, in priority order:**

> **Items 1–2 were completed Aug 4 — see the Aug 3–5 entry at the top of this log.** Item 1 came back
> **negative** (resident GaMD rejected, boost statistics corrupted); item 2 came back with v4/v5 done and
> the Go family's AA comparison invalidated by pre-compaction. Item 3 is now partly self-answered. The
> list below is kept for its reasoning; the live list is the one that follows it.

1. ~~Read out the resident-mode validation (52973301)~~ — **DONE, REJECTED.** See above.
2. ~~Read out the v4/v5/v6 sweep~~ — **v4/v5 DONE**; v6 failed on a script bug, rerunning as 53032654.
3. **Watch for Chen's reply** on GaMD resident-mode accuracy tradeoffs — **and send him the reproducer**,
   since the answer turned out to be a concrete bug rather than a tradeoff.
4. **Full-system rebuild** — when the user's CHARMM-GUI build with the AlphaFold-completed protease lands,
   build `full-model`/`full-bact` fresh. NAMD download alone is sufficient (GROMACS not needed even for a
   future Martini version — verified).
5. **Two unfixed mdp bugs** — `eq.mdp` compressibility is now **fixed in the staged ladder**
   (`scripts/martini_staged_eq/`, not yet applied); **`em.mdp`'s PME/`epsilon_r` bug is still open.**
6. `full-model`'s 25 GB is still only on `/project2`, reachable via `ssh midway2`. Superseded, so migration
   may not be worth it.

**Live open items (as of Aug 5):**
1. **Send Dr. Chen the resident-GaMD bug report** — reproducer at `dome-bact/gamd_resident_val/`.
   Fault is in the statistics path, not the force path (`ENERGY:` correct to 0.008% over the same window).
2. **Read out v6 (53032654)** — elastic-based, so it should start near Rg_xy 79 like v1/v2, unlike the
   whole Go family. The more informative remaining run.
3. **Consider v7 at ε ≈ 2.5** — but judge it on whether it **reduces pre-compaction at production start**,
   not on the production-phase delta.
4. **Apply `scripts/martini_staged_eq/`** once the sweep is done — includes the mandatory lipid-topology
   patch (`-DBILAYER_LIPIDHEAD_FC` is currently a silent no-op). Go variants need a separate protein
   restraint block; `-DPOSRES` is a no-op for them.
5. **Keep resubmitting production** — `control` and `dome-model` both went idle this session purely from
   not being resubmitted. Nothing auto-chains across jobs.

---

## July 22, 2026 — Day 40

**GaMD resident-mode incompatibility confirmed; 2-GPU offload benchmark done**
- Tested GaMD (accelMD) with GPU-resident mode enabled (`CUDASOAintegrate on`, job 52473685): **NAMD FATAL-errors at startup** with "GPUresident is incompatible with... accelMD and related options." Definitive — resident mode is structurally off the table for GaMD, settling a day-long discussion. The fast ~8 ns/day resident production baseline does not apply to GaMD; it structurally requires offload mode.
- **2-GPU offload GaMD benchmark** (job 52473718, `dome-model`): **0.0844 s/step = ~2.0 ns/day** (1.28× speedup over 1-GPU offload at 1.6 ns/day). Scaling is moderate (GaMD boost overhead doesn't parallelize as cleanly as plain dynamics), but real. Recommendation: launch both `dome-model` and `dome-bact` GaMD runs on 2-GPU/16PE offload (saves ~1 week per system vs 1 GPU).
- **GaMD equilibration timeline** (52 ns target per dome system): ~26 days wall-clock, running both dome GaMD in parallel on separate 2-GPU allocations. Updated CLAUDE.md with findings and recommendation.

**Martini 3 CG dome comparison system — ready to run July 23**
- Completed full ready-to-execute workflow setup for optional Martini 3 coarse-graining comparison (speed sanity-check: does dome open at all in CG?). Not replacement for AA—primary path (loses lipid specificity), but useful for ruling out "dome doesn't open in any environment."
- **Workflow files created**:
  1. `MARTINI_WORKFLOW.md` — comprehensive 4-step guide (CHARMM-GUI → martinize2 → GROMACS)
  2. `scripts/convert_charmm_to_martini.sh` — automated AA→CG conversion (tries martinize2, fallback to Martini online server)
  3. `scripts/martini_md_template.mdp` — GROMACS config (Martini 3, NPT, 10 fs CG timestep)
  4. `scripts/run_martini_gromacs_template.sbatch` — Beagle3 job template (2 GPU A100)
- Workflow (when CHARMM-GUI 8458753726 finishes tomorrow): download AA outputs → 1-min conversion → queue GROMACS (runs ~1 hr on 2 GPU vs 26 days for AA GaMD).
- Attempted martinize2 install via conda on Beagle3 during this session; it did not complete successfully (package availability/versioning issue). Fallback: user can run conversion locally on Mac or use Martini's online server (both documented in workflow).

**Session complete — all systems running, GaMD + Martini paths documented**
- All 5 production/equilibration systems running normally on Beagle3. FtsH systems confirmed stable in offload mode. Dome systems looping toward 20 ns conventional MD cap, then GaMD handoff.
- CLAUDE.md updated with all July 22 findings (GaMD, Martini, system status).
- Code committed and pushed (d2b1107, Day 40 summary).

---

## July 22, 2026 (continued) — 5 stalled benchmark jobs root-caused, real Martini 3 CG dome system built end-to-end

**Context**: dome-model/dome-bact hit their 20 ns conventional-MD cap today, so GaMD equilibration was
launched (4-GPU offload, jobs 52527113/52527114 — the config fix expected to recover ~6.4 ns/day per
Rajiv's validated template). Noticed the Beagle3 queue had shrunk from 11 jobs to 6 over ~30 min —
investigated and found 5 jobs (3× NAMD GaMD speed-sweep benchmarks, 1× OpenMM plain-MD benchmark, 1×
OpenMM "GaMD" benchmark) had all silently `FAILED` shortly after submission.

**All 5 failures root-caused via `sacct`/`.err` files, not guessed at:**
- **3× `gamd-bench-{1,2,3}gpu`** (NAMD): `FATAL ERROR: couldn't read file "step5_input.str"`. Their
  working directory (`domeonly_equil/namd/gamd_benchmark/`) was missing `step5_input.str`,
  `step5_input.psf/.pdb`, `toppar/`, and the `step7_20.restart.*` files it restarts from — all present
  one directory up in `namd/`, just never copied/symlinked in when the benchmark dir was set up. Fixed
  by symlinking all of them in from the parent directory; resubmitted as 52534069/70/71.
- **`openmm-bench-2fs`**: `FileNotFoundError` for `step6.6_equilibration.pdb` (and its fallback
  `step5_input.pdb`) — neither ever existed in that OpenMM working directory, which only had NAMD's
  binary `.psf`/`.crd`/`.coor` files, no PDB. Generated the missing PDB properly via MDAnalysis
  (`mda.Universe(psf, restart.coor, format='NAMDBIN')` → `.write(pdb)`), reading real box dimensions from
  the NAMD `.xsc` restart file first (MDAnalysis otherwise writes a placeholder unitary `CRYST1`, which
  would silently break PME). Also found and fixed a second, unraised bug while doing this: the benchmark
  script never passed a `CharmmParameterSet` to `psf.createSystem()` at all — it would have crashed on
  that call too, just further down, since PSF-format topology has no force-field parameters embedded.
  Rewrote the script with the full CHARMM `toppar/` file list and the real box vectors.
- **`gamd-openmm-bench`**: crashed calling `mm.GaussianAccelerationGroupForce()`. Verified directly —
  `hasattr(openmm, 'GaussianAccelerationGroupForce')` → `False` on Beagle3's actual OpenMM install — this
  class does not exist anywhere in stock OpenMM; the original benchmark script (written earlier this
  session, before checking) assumed a one-line library call that was never real. **User correctly pushed
  back** on the initial conclusion "GaMD is impossible in OpenMM" — checked further and found the Miao
  Lab (same lab behind NAMD's GaMD) publishes a real, separate, pip-installable package,
  `github.com/MiaoLab20/gamd-openmm`, implementing dual/dihedral/total boost via `CustomCVForce` and a
  CLI tool (`gamdRunner`) driven by an XML config — not a bare Force class. Installed it on Beagle3
  (`pip install --user`, after fixing an `mdtraj`/`versioneer` build conflict by installing dependencies
  via prebuilt wheels first), wrote a matching XML config (`lower-dual` boost, sigma0 6.0/6.0 kcal/mol —
  same as Rajiv's NAMD config — staged as 1000+1000+1000+1000 prep/eq steps + 50,000-step GaMD-production
  for the actual speed measurement), resubmitted as 52534068.
- **Lesson for future benchmark setups**: always stage a benchmark subdirectory with symlinks to its full
  dependency set (topology, restart, parameter files) *and* smoke-test the script's imports/API calls
  before submitting to the queue — none of these 5 failures were physics problems, all were "the job
  never actually had what it needed to start."

**Real Martini 3 CG dome system built, fully from scratch, end-to-end — first successful attempt this
summer.** Prior sessions' attempts (CHARMM-GUI Martini Bilayer Maker, direct `martinize2` on the full
solvated system) both failed; this time the failure modes were root-caused precisely enough to build a
real working alternative:
- **CHARMM-GUI's Martini Bilayer Maker cannot handle this system, confirmed as a hard limit, not a
  bug**: its input is explicitly labeled "Upload All-atom PDB File" — no path exists to hand it an
  already-CG structure. It always does its own internal AA→CG conversion, and for a >99,999-atom system
  that conversion's internal PDB write hits the 5-digit atom-serial format limit and writes literal
  `*****`, crashing `martinize2` with `ValueError: invalid literal for int() with base 10: '*****'`.
  Confirmed this happens identically for both PDB and mmCIF uploads (CHARMM-GUI's backend still funnels
  through its own PDB writer either way).
- **Direct `martinize2` on the full 1.7M-atom solvated `.gro` file does NOT hit that atom-count wall**
  (GRO format doesn't have PDB's hard serial-number cutoff) — it processed the *entire* system cleanly
  through graph-building, coordinate-averaging, and topology-writing — but crashed at the very last step,
  `ValueError: No molecule in the system. Nothing to write.` Root cause: `martinize2` is a protein-only
  converter; every one of the ~370,000 TIP3 water molecules (and presumably every lipid) got silently
  rejected with `Cannot recognize residue 'TIP3'... Deleting the molecule`, leaving nothing to write once
  all non-protein content was stripped.
- **Working solution**: convert the protein only, per chain (CHARMM-GUI's GROMACS FF-Converter output
  had already split it into 24 single-chain PDBs, ~5,300 atoms each — comfortably small), then build the
  CG membrane separately around the resulting CG protein using `insane` (Marrink lab's own
  membrane-builder tool, a real pip-installable package from `github.com/Tsjerk/Insane`, not the loose
  single-file script an older tutorial might suggest).
- Used a local Docker container (`continuumio/miniconda3` + `pip install polyply vermouth` +
  `pip install git+https://github.com/Tsjerk/Insane.git`) to avoid the local-pip/cluster-conda version
  conflicts and auth issues that blocked every earlier direct-install attempt this session.
- All 24 chains converted successfully (18,264 total CG beads, down from ~127,500 AA atoms). Verified
  `martinize2` preserves the original absolute coordinate frame (checked chain A's first residue CA vs
  its CG BB bead — matched), so all 24 chains could be concatenated directly with no re-superposition.
- Found the official Martini 3 lipid parameter library is a *separate* GitHub org/repo,
  `Martini-Force-Field-Initiative/M3-Lipid-Parameters` — not the generic `martini-forcefields` repo
  (which only has 3 unrelated lipid types). Downloaded the 6 needed files (core FF, the easy-to-forget
  `ffbonded` bond/angle-macro file, PE/PG phospholipids, solvents, ions).
- Two lipid gaps found and handled: **`DPPE`** has no Martini-3 shape template in `insane`'s bundled
  `lipids.dat` (only unsaturated PE variants exist) — built a custom entry by copying `DPPG`'s identical
  saturated-tail layout and swapping just the headgroup bead/charge to match DPPE's real parameters, fed
  via `insane`'s `-dat` flag. **Cardiolipin has no Martini-3 template in `insane` at all** (only
  Martini-2-era entries, explicitly marked incompatible with the real M3 `.itp` bead names) — rather than
  hand-build an unvalidated custom 19-bead template under time pressure, redistributed its 5% (LOACL1 +
  TLCL1) into POPG/DOPG, giving this CG system DPPE 70%/POPG 15%/DOPG 15% instead of the real 5-lipid mix.
  **Documented as a known simplification, not silently absorbed.**
- Built the full system with `insane` (135,760 CG beads: 18,264 protein / ~1,654 lipids / 95,580 water /
  2,104 ions, correctly neutralized — 1,335 Na⁺ / 769 Cl⁻ against a −566 net charge). Had to manually
  rewrite the topology's protein section afterward: `insane` only understands the protein as one opaque
  input blob and writes a placeholder `Protein  1` molecule line — replaced with the real 24 separate
  `chain_X_0` moleculetypes, in the same order the chains were concatenated (cross-checked against the
  `.gro` file's per-chain residue-numbering reset at each chain boundary).
- **Validated with `gmx grompp`** on Beagle3 before trusting any of it — first pass surfaced the missing
  `ffbonded` file (every lipid bond errored "No default Bond types"); second pass, after adding it, came
  back completely clean (only a PME-mesh-load performance note, zero errors). `em.tpr` generated.
- First `gmx mdrun` attempt was run directly on the Beagle3 login node (habit from thinking of it as "just
  testing") and segfaulted immediately — login nodes have no GPU and RCC doesn't support compute there.
  Wrote a proper `run_em.sbatch`, resubmitted correctly as job 52534609.
- **Full reproducible pipeline (all 10 steps, every gotcha) written into CLAUDE.md** under "Martini 3 CG
  Dome System" specifically so this doesn't need to be re-derived from scratch if CG is later run on the
  other 4 systems.

---

## July 22–23, 2026 (continued) — overnight: 3 new job bugs found/fixed, Martini EM segfault root-caused, all-clear before bed

**Checked whether energy-minimization-after-coarse-graining is real standard practice, not assumed.**
User asked directly, so did actual research rather than answering from memory: fetched the official
Martini Force Field Initiative tutorial (cgmartini.nl). Confirmed — the documented standard workflow is
minimization → NVT/NPT equilibration → production, specifically because placing lipids/water/ions
programmatically (exactly what `insane` does) creates steric clashes that must be relaxed first. Not an
extra precaution specific to our pipeline; this is the field's actual standard.

**Checked on the 5 "fixed" jobs from earlier today — 3 of them had failed again, for entirely different
reasons than before.** User noticed the queue had dropped to 3 pending + 2 running and asked what
happened; investigated via `sacct`/`.err` rather than assuming the earlier fixes hadn't held:
- `full-model-prod` (52465073) had actually **completed normally** overnight (12.05→14.05 ns, used its
  full wall-time allocation, nothing auto-chains) — not a failure, just needed a routine resubmit
  (52546374). While checking this, noticed something worth flagging: the running config currently has
  `CUDASOAintegrate on` (**resident mode**), which directly contradicts the July 17–20 finding that
  resident mode crashes FtsH systems ("atoms moving too fast"). It's been running fine for 10+ ns in
  resident mode on 2 GPU (~8 ns/day, matching resident-tier speed) — timestamps show the switch happened
  between `step7_3` (Jul 21, offload-era slow rate) and `step7_4` (Jul 21, suddenly fast). Don't know if
  this was an intentional revert after building confidence, or accidental. **Left as an open question**,
  not resolved — flagged prominently in CLAUDE.md for a fresh look.
- **`gamd-bench-1/2/3gpu`** (NAMD) failed with a *different* error than this morning's missing-files bug:
  `ERROR: 'accelMDGRestartFile' is a required configuration option when 'accelMDGRestart' is set`. The
  `.inp` had `accelMDGRestart on` (copied from a real production config that legitimately restarts from
  a prior GaMD segment) but this from-scratch benchmark never had a restart file to point it at. Fixed
  by setting `accelMDGRestart off` — correct for a first-time speed test. Resubmitted (52546353/54/55);
  1-GPU and 2-GPU are now running and healthy, real GaMD statistics being computed, both landing at
  ~0.88 ns/day — **suspiciously identical between 1 and 2 GPU**, contradicting the earlier-documented
  1.28× 2-GPU speedup (job 52473718). Not yet explained; worth comparing configs once 3/4-GPU data is in.
- **`openmm-bench-2fs`** failed on `FileNotFoundError: toppar/top_all36_prot.rtf` — my earlier rewrite of
  this script assumed `toppar/` was a subdirectory of the working `openmm/` directory; it's actually a
  sibling directory one level up. Fixed all 50 path references to `../toppar/`. Resubmitted (52546364),
  **completed cleanly**: 6.79 ns/day, a real trustworthy number now.
- **`gamd-openmm-bench`** had "completed" in 2 seconds with zero output — false success. The sbatch tried
  `source .../envs/openmm/bin/activate`, which doesn't exist for that conda environment, so `python` was
  never found and the whole script silently no-op'd (no `set -e` to catch it). Fixed by switching to
  `module load openmm/8.1.0` (verified directly that this puts a working `python3` with both `openmm`
  and `gamd` importable on PATH, before trusting a resubmit). Resubmitted (52546365) — running and
  healthy, actively writing a real trajectory (`output.dcd`, growing past 1 GB) — first real GaMD-via-
  OpenMM run of the summer.
- **Recurring lesson, worth internalizing**: none of tonight's 3 new failures were repeats of this
  morning's bugs (missing files) — they were new problems that only surface once a job gets *past* the
  missing-file stage. A job showing `COMPLETED`/exit 0 is not proof it did anything real (the
  `gamd-openmm-bench` false-success case) — always check for actual output (growing trajectory, nonzero
  log, real numbers), not just the exit code.

**Martini EM segfault root-caused: a GROMACS build bug, not a topology problem.** The first real
`sbatch` attempt (52534609, correctly run on a GPU compute node this time, not the login node) segfaulted
inside GROMACS's threaded virtual-site construction (`gmx::constr_vsiten`, address `0x180`). This was
concerning since it's inside our own protein topology's `[virtual_sitesn]` sections (Martini's standard
ring-stabilizing construct, present in all 24 chains) — but `grompp` had validated with zero errors, so a
real topology bug seemed unlikely. Ruled out an OpenMP threading race first (the most likely category of
bug for a crash inside threaded vsite construction): reran single-threaded, CPU-only — **still segfaulted,
same exact spot, in 7 seconds**. That ruled out threading. The actual cause: the loaded module was
`gromacs/2022.4-plumed_2.8.1`, a PLUMED-patched build (PLUMED patches are known to sometimes touch
force/vsite code paths). Switched to `gromacs/2025.3` (also PLUMED-patched, but far newer — plumed
2.10.0), regenerated `em.tpr` fresh with matching `grompp`, reran: **completed 3,969 of 5,000 steps
cleanly**, potential energy smoothly decreasing (−4.24×10⁶ → −4.54×10⁶ kJ/mol), no crash — only stopped
because the diagnostic run's 15-minute wall-time limit hit, not because of any error. Confirms the fix.
**Always use `gromacs/2025.3` for this system going forward, never the cluster's default `2022.4`.**
EM itself was never given a real time budget to actually finish — that's tomorrow's first step.

**Session close, all-clear**: two production systems running normally (`control`, `full-bact`), three
benchmark jobs confirmed healthy and producing real data overnight (`gamd-bench-1gpu`, `gamd-bench-2gpu`,
`gamd-openmm-bench`), two more resubmitted and pending on resources (`gamd-bench-3/4gpu`), the two real
GaMD equilibration jobs still queued (`gamd-dome-model-equil`, `gamd-dome-bact-equil`), `full-model-prod`
resubmitted, and the Martini EM ready to resubmit with a proper wall-time on the correct GROMACS version.
Full morning checklist and per-job detail written into CLAUDE.md's "Beagle3 job queue snapshot" section.

---

## July 17–20, 2026 — Days 36–39

**FtsH resident-mode crash fully diagnosed → FtsH systems run OFFLOAD**
- Continued the `full-model` production-crash investigation. The offload+minimize warm-up completed clean and produced `step7_0`, but the *first resident-mode production block from it* (job 52347461) **still crashed** `SequencerCUDA: Atoms moving too fast` — this time at **timestep 13,758 (~27 ps)** instead of 361. So the warm-up bought ~27 ps but didn't fix it; not a simple local clash a minimization removes.
- Per the "if it fails again, stop and diagnose" rule, ran an **offload diagnostic** (job 52351830): `full-model` production in offload mode (1 GPU, same forces, continuing velocities from `step7_0`). It **ran the full 1 ns cleanly** (500,000 steps, End of program, zero instability). Since offload uses identical forces, a broken structure would have crashed it too → the structure is fine; it's a **resident-mode numerical fragility** specific to this large FtsH system.
- Root-cause framing (why now, never before): `full-model` is the first system combining FtsH + the new AF3 build + resident-mode production. Every "similar" system that worked drops one of those — `dome-model` (same AF3 build, resident, but no FtsH) crosses fine; the old Midway3 full-dome resident benchmark that ran clean was a *different pre-AF3 build*, only 100 ps.
- **Resolution**: `full-model` and `full-bact` run production in **offload** (`CUDASOAintegrate off`, 1 GPU / 8 PE, ~2 ns/day — ~4× slower than resident's ~8). Dome-only/membrane systems keep faster resident mode. Submitted a 2-GPU-offload benchmark (job 52407197) to see if the FtsH speed is recoverable. Open question: recover resident speed via `margin`/timestep/NAMD-build — not yet investigated.

**Production script rewritten to LOOP chunks within a job**
- User corrected a misunderstanding: Rajiv's script doesn't exit after 1 ns — it *iterates many ns, processed in 1 ns chunks, within one job*. Rewrote `run_prod_gpu.sh` accordingly: runs sequential 1 ns chunks until the wall-time allocation is nearly used (measured-chunk-duration check) or a `MAX_CHUNKS=12` per-job cap, then stops cleanly. Removes the per-ns manual-resubmit babysitting.
- Made it one script for all five via env vars in each sbatch: `DEVICES` (GPU list) and `TARGET_NS` (stop at a total). Kept the July-15 self-heal + overwrite-guard.
- `dome-bact` validated the loop empirically: its first production job (52350287) ran **0 → 12 ns** in one go (hit the 12-chunk cap), Jul 17→19.

**Coarse-graining explored and set aside in favor of GaMD**
- Extended discussion (prompted by Dr. Haddadian's interest) on Martini CG with *implicit water / CG lipids but atomistic protein*. Worked through the science and **researched the literature** (Wassenaar "Mixing MARTINI" virtual-site coupling; dual-resolution membrane paper PMID 32314586; CHARMM/PRIMO hybrid; Two-Decades-of-Martini review).
- Key findings that steered away from the hybrid: (1) it's **not standard** — one of several specialized schemes, and the AA-protein-in-CG-*membrane* case specifically isn't an established/validated workflow (published membrane hybrids are lipid-only vesicles); (2) the protein↔environment interaction is necessarily at **CG resolution** (confirmed verbatim in the dual-resolution paper) — so it coarse-grains the very lipid–protein specificity our question depends on (cardiolipin binding, composition effects); (3) literature documents that concurrent AA/CG Martini coupling **over-stabilizes protein conformational dynamics** (or unfolds the protein without the fix) — fatal for studying the dome opening; (4) even the throughput win is smaller than fully-CG (~3–10× vs ~100×) because the AA protein caps the timestep, and it *doesn't accelerate the opening barrier at all* (protein stays atomistic, normal rates).
- **Decision**: use **GaMD** (already in the plan, "planned next") — all-atom, native in NAMD (no engine switch), flattens the conformational barrier directly (~10–1000× effective on the transition), preserves the lipid-specificity and existing analyses. Hybrid CG is a possible later throughput add-on via the *serial* route (CG-sample → AA-backmap), not concurrent mixing.

**Day-39 relaunch — all 5 systems running again**
- Returned to find everything idle (nothing running): `control` had a transient no-output failure (52347462, exit 1:0; data intact at 39.53), `dome-model`/`dome-bact` had completed their jobs and nothing auto-chains across jobs, FtsH systems were parked awaiting the offload answer.
- Relaunched all five with the looping script (jobs 52407134–52407180): `control` (39.53 ns, 4 GPU resident, no cap), `dome-model` (10.05 ns) and `dome-bact` (12.0 ns) both **capped at 20 ns** (`TARGET_NS=20`) for the GaMD handoff, `full-model` (1.05 ns — reused the offload-diagnostic ns as `step7_1`) and `full-bact` (0.05 ns, first real block) both **1 GPU offload**. Plus the 2-GPU-offload benchmark.

---

## July 16–17, 2026 — Days 35–36

**Session-start status check — all 5 systems**
- `control` and `dome-model` each completed one more 1 ns production block (jobs 52297534, 52297484; both `COMPLETED` exit 0:0), reaching **39.53 ns** (step7_39) and **9.05 ns** (step7_9) respectively, then went idle (nothing auto-chains — each production sbatch runs one block and exits). Need resubmit to continue
- `dome-bact` / `full-bact` still equilibrating, on step6.5 (~58–64% through) heading into step6.6 — these DO auto-chain 6.1→6.6 within one job, so they'll finish equilibration without intervention
- `full-model` equilibration was complete but production had never been launched — did so this session (below)

**`full-model` production launch — failed, root-caused, warm-up fix deployed**
- Set up production from scratch for `full-model` (directory previously had only equilibration scripts): copied `dome-model`'s `run_prod_gpu.sh` + a `job-submit-beagle3-prod.sbatch` (2 GPU / 16 PE / A100, resident), patched `step7_production.inp`'s `CUDASOAintegrate off`→`on` (stale CHARMM-GUI default), seeded `cumulative_ns.txt` with `step6.6_equilibration 0`. Submitted job 52301891
- Job **FAILED** after ~6 min: `SequencerCUDA: Atoms moving too fast` at timestep 361 (ran 361 steps stably first, then diverged — a slow build-up, not a static step-1 clash)
- Root-caused: **not** a generic config problem. `dome-model`'s first production block used the *identical* resident-mode/non-HMR/2fs config from its own step6.6 restart and crossed the transition cleanly. The only structural difference is `full-model` contains **FtsH**. Equilibration ended clean (step6.6 final temp 302.8 K, energies normal, no gross clash in global VDW) → a *localized* strained contact (almost certainly FtsH region or an M3-graft junction) that only releases when step6.x restraints drop, and that a single hot contact averages out over 1.7M atoms
- **Fix**: run just the first block as an offload warm-up — mirror the exact offload config that carried this system through step6.1–6.6 (1 GPU, 8 PE, A100, `CUDASOAintegrate off`) plus a `minimize 5000` + `reinitvels 303.15` + 50 ps run, producing `step7_0` (0.05 ns). Built `step7_0_warmup.inp` by transforming `step7_production.inp` on-cluster (guarantees the 50+ toppar lines match exactly), submitted as job 52338639 (left PENDING at session close, behind the two equilibrations). Once it produces `step7_0.restart.*`, seed the ledger `step7_0 0.05` and resume normal resident 1 ns blocks. **If the warm-up also fails "atoms moving too fast" → stop and inspect FtsH/M3 geometry, do not blind-resubmit** (agreed with user). Full gotcha written into CLAUDE.md
- (Session note: Beagle3 ControlMaster socket expired near end of session — warm-up final status not yet confirmed)

**HMR revisited in depth (Balusek et al. 2019, JCTC — "Accelerating membrane simulations with HMR")**
- User surfaced the paper's line "HMR should not be applied to water" and asked whether that rules HMR out for our system. Clarified it does **not**: "not applied to water" is a per-molecule bookkeeping instruction (skip water when repartitioning), not a statement that water-containing systems can't use HMR — every system in the paper is solvated and every 4-fs run *is* an HMR run. Water is already held rigid by **SETTLE** (analytic, mass-independent), so HMR buys it nothing and, per Hopkins et al., actively raises its viscosity/slows protein-conformational transitions if applied → excluding water is free, not a compromise. Our existing `step5_input_hmr.psf` (CHARMM-GUI's HMR generator) already does this exclusion automatically
- Explained SETTLE (analytic rigid-water solver, whole-molecule geometry, mass-independent) vs SHAKE (general iterative bond-length constraint on protein/lipid X–H, what `rigidBonds all` invokes) — SHAKE-constrained X–H are the actual timestep bottleneck HMR targets; water via SETTLE was never limiting
- **Decision reaffirmed: not adopting HMR** — but with more specific evidence than before. Point that decided it (user's call): the paper's *conformational-transition* fidelity is the concern for our science. Honest reading of the paper: the properly-built 4-12 (HMR, 12 Å cutoff) protocol actually reproduced L8 peptide TM↔surface transitions and glycophorin-A dimerization PMFs reasonably (most of the damage in the paper came from the 9 Å cutoff, which we'd never use). BUT the two places the paper touched *large-scale/rare-event collective* behavior both trended away from the non-HMR reference under 4-12: (1) **bending modulus kc** 30.9→28.6 kBT (a property only measurable in large membranes with long-wavelength undulations — the paper explicitly notes its small systems can't exhibit these), and (2) a **cholesterol flip-flop** rare event appeared under 4-12 but not in the 2-μs non-HMR reference. The paper only claims statistical significance for the extreme 4-9, not 4-12 — so it neither proves nor validates HMR for our regime (1.7M-atom system, membrane-coupled dome-opening = large collective + rare-event motion). Defensible basis for holding off; the clean way to actually settle it is a paired short HMR/non-HMR run on `dome-model` comparing a *conformational/membrane-mechanics* observable, not just lipid diffusion

**Voronoi APL script walked through and documented**
- Read the actual `control_apl_voronoi_35ns.py` off Midway3 and documented how it works in CLAUDE.md (`control` analysis section) so it's reusable/explainable: one point per lipid at whole-molecule COM (not headgroup); `name P or name P1` used only for leaflet assignment; cardiolipin deliberately counted as one lipid = one cell (grabs only `P1`, hence its ~72 Å² ≈ 2× the ~55 of single-phosphate lipids); each leaflet tessellated separately with 3×3 periodic tiling + shoelace areas; 350-frame/35 ns verified-intact window. Noted the code lives **only** on Midway3 — repo currently tracks just the `.npy`/`.png` outputs

## July 15–16, 2026 — Days 34–35

**Beagle3 scratch reorganization started**
- Began consolidating the 5 systems under `/scratch/beagle3/junseo/` (previously scattered under `/project2/haddadian/junseo/beagle3-jobs/` with inconsistent directory names). Moved `control` (server-side rsync from `/project2`, ~10s at 200+ MB/s — much faster than routing through local machine); staged `dome-bact`/`full-bact` there directly from the start since they were never staged anywhere else. `dome-model`/`full-model` deferred until no live job uses their current path (can't rename a directory a running SLURM job has as its WorkDir)

**dome-bact / full-bact staged and equilibration started**
- Two new CHARMM-GUI downloads (`charmm-gui-no-ftsh`, `charmm-gui-ftsh`) verified against composition #2 (74% PG / 20% CL / 6% PE) — counted lipid residues directly from `step5_input.pdb`: 138 DPPE / 851 POPG / 851 DOPG / 230 LOAC / 230 TLCL = exactly 6.0/74.0/20.0% match. Same AF3 ic-minimized protein structure as `dome-model`/`full-model`, so the lipid-composition comparison isn't confounded by a different protein build
- Patched missing `CUDASOAintegrate off` into all step6.x + step7_production.inp (same gap as before, CHARMM-GUI doesn't include it by default)
- Equilibration submitted (jobs 52188526, 52188527), mirroring `full-model`'s proven-robust recipe (NAMD 3.0.1, 1 GPU, offload mode, A100-pinned). Both healthy, no errors, working through step6.1–6.6 as of session close (currently on step6.5)

**Chunk size changed to 1 ns for all systems**
- User flagged that Rajiv's own convention (`/project2/haddadian/rajiv/namd/step7_1...step7_9`) used 1 ns blocks, not the 8 ns blocks adopted earlier this week. Checked: Rajiv actually used 1 ns blocks *early* and scaled up to 10 ns+ blocks later (`step7_run20.inp`, 5,000,000 steps) once established — so 1 ns was his starting point, not his steady-state
- Confirmed chunk size doesn't meaningfully affect throughput (NAMD's per-step cost is independent of block length; startup/toppar-parsing overhead is <1% even at 1 ns block length) — the only real cost is more frequent manual resubmission, since nothing auto-chains yet
- `BLOCK_STEPS` changed 4,000,000 → 500,000 in both `control_prod/run_prod_gpu.sh` and `domeonly_equil/run_prod_gpu.sh`, deployed live

**`control` production data-loss incident — root-caused and fixed**
- `run_prod_gpu.sh`'s self-heal step (finds "the latest completed block" via `ls -t step7_*.restart.coor`) matched a leftover GPU-count benchmark restart file still sitting in `control`'s live directory (never archived, unlike `dome-model`'s). Self-heal renamed it onto the existing `step7_45.*` filenames with a plain `mv` — silently overwriting and destroying the real 8 ns block that was there (37.53→45.53 ns)
- Discovered the corruption cascaded into the cumulative-ns ledger too: the benchmark's real duration (0.05 ns) got added *on top of* the already-correct 45.53 value instead of the true physical branch point (36.4 ns by direct frame count), inflating the ledger to a fabricated 45.58 ns. A job had already started running against that bad baseline before the fix landed — killed it (`scancel`), deleted its incomplete partial output, and corrected the ledger
- **User's call**: rather than patch around the gap, fully discard everything after the last verified-good checkpoint (`step7_37`, 37.53 ns) and restart production from there. Deleted all `step7_45.*` files, removed the ledger's trailing bad line, resubmitted — `control`'s real, continuous, gap-free trajectory is now anchored at **37.53 ns**, not 45.53
- Fix applied to both `control_prod/run_prod_gpu.sh` and `domeonly_equil/run_prod_gpu.sh`: (1) self-heal glob tightened to `grep -E '^step7_[0-9]+\.restart\.coor$'`, excluding any filename with extra suffix text; (2) hard check added — refuses to rename onto a target that already exists instead of silently overwriting
- Lesson for future systems: archive benchmark files out of a system's live production directory (sibling `benchmarks_archive/` folder) *before* production ever starts there, not "later"

**A second, unrelated bug from editing a live script**
- Overwrote `dome-model`'s `run_prod_gpu.sh` on disk (as part of the fix above) while that system's *own* 24-hour production job was still mid-execution, paused waiting on NAMD. When NAMD finished and the bash wrapper resumed reading the script file to append its final ledger line, it read a corrupted mix of old/new file content (the file had been substantially restructured, not just appended to) and crashed with a "No such file or directory" error — job 52134348 shows `FAILED`, exit 127
- The underlying NAMD run itself completed perfectly cleanly (step 4,000,000/4,000,000, "End of program", valid restart files) — only the bash wrapper's bookkeeping crashed after. No data lost; manually appended the missing `step7_8 8.0500` ledger line and resubmitted
- **Lesson**: don't overwrite a script file while a long-running invocation of it may still be mid-execution and about to resume reading from disk

**`full-model` equilibration complete**
- Job 52124727 `COMPLETED`, exit 0:0, ~1 day 3.7h total. step6.6 reached its full target (step 1,135,000) cleanly. Ready for production setup (not yet started as of session close)

**`control` system analysis pipeline built (thickness, curvature, area-per-lipid, order parameter)**
- Reran thickness + curvature over the corrected, gap-free **35 ns** window (Midway3 `step7_1`-`step7_21` + Beagle3 `step7_37`, 364 frames total, using first 350). Thickness: mean 43.93 Å (37.55–50.00 Å range). Curvature: found the original 15×15 grid gave physically implausible magnitudes (±0.8 (1/Å), implying a ~1-3 Å radius of curvature — smaller than a bond length); reran at 8×8 grid with a data-driven percentile-based color scale instead of the old fixed ±0.01, giving a much more reasonable ±0.37-0.49 (1/Å) range — root cause was too few headgroup atoms per bin for a stable curvature fit at 15×15
- Order parameter (S_CD per acyl-chain carbon): Rajiv's local `lipidorderkit` checkout was broken (git-tracked but the actual `lipidorder/lipid_order.py` source was missing on disk); traced its `git remote` to the real upstream (`github.com/ricard1997/lipidorderkit`) and cloned a fresh copy into the user's own scratch space (explicit user go-ahead required — fetching/running third-party code). Found and fixed two real bugs in the original `order_sn1`/`order_sn2` functions: an off-by-one in the carbon-counting loop, and missing alkene-carbon hydrogen-name overrides for POPG/DOPG (the original only special-cased POPE/POPS, despite POPG's sn2 tail and DOPG's both tails having the same oleoyl double-bond chemistry) — verified the correct hydrogen names directly against `step5_input.psf` bond topology rather than guessing. Cardiolipin (LOACL1/TLCL1) excluded entirely — 4 acyl chains with completely different `CA/CB/CC/CD` atom naming, not the sn1/sn2 two-tail model this method assumes
- Area per lipid: built fresh (no existing script anywhere, including Rajiv's directory). First version used the simple box-area/leaflet-count method; user asked for 2D periodic Voronoi tessellation on whole-lipid centers of mass instead, for a method that (a) can resolve per-lipid-type APL and (b) stays accurate under local heterogeneity (relevant once protein-containing systems are analyzed). Rebuilt using `scipy.spatial.Voronoi` with 3×3 periodic tiling. Confirmed mathematically (and numerically) that the overall/combined mean is identical between both methods (54.35 Å² both times) — Voronoi's real value is the per-type breakdown, which the simple method can't produce at all: cardiolipin (~71-73 Å²) is noticeably larger than the single-headgroup lipids (~53-56 Å²), consistent with its bulkier 4-tail structure
- All of the above reran from scratch on request, after the `control` data-loss incident, to keep every deliverable computed on a single consistent, gap-free window

**Local `analysis/` folder reorganized**
- Restructured into `<system>/<Nns>/<script-type>/` subfolders (e.g. `analysis/control/35ns/thickness/`) per user request, for consistency as `dome-model`/`full-model`/`dome-bact`/`full-bact` accumulate their own analysis runs. General reference docs (literature review, benchmark plan) and the retired `no-dome` system's old lipid-proximity output left/organized separately, not tied to the new 5-system naming

**Five systems formally named**
- `control`, `dome-model`, `dome-bact`, `full-model`, `full-bact` — see CLAUDE.md for the full naming table and lipid-composition rationale (composition #1 = generic PE-dominant model membrane; composition #2 = the true cardiolipin-microdomain bacterial signature, per Dr. Haddadian's own usage and consistent with published cardiolipin-microdomain/HflC-localization literature)

**Dr. Haddadian forwarded an Argonne (ALCF) email thread on GaMD**
- Unrelated group (Prof. Stephen Meredith's lab) discussing GaMD setup on Aurora/Polaris with Argonne's Arvind Ramanathan/Moeen Meigooni. Key takeaway for later: NAMD's new GPU-resident GaMD code is NVIDIA/AMD-only (doesn't run on Aurora's Intel GPUs — irrelevant to us, Beagle3 is NVIDIA); separately, Argonne's own past experience found NAMD underperforms OpenMM specifically for enhanced-sampling/alchemical methods (CPU-fallback bottleneck), though Meigooni notes this gap may close once NAMD's new GPU-resident GaMD is actually used. Relevant to this project's own "planned next" GaMD phase — when that starts, treat NAMD-vs-OpenMM performance for GaMD as its own open empirical question, not an assumption carried over from this summer's conventional-MD benchmarking (where NAMD won decisively)

---

## July 9–14, 2026 — Days 28–33

**NAMD vs OpenMM systematic speed sweep (dome-only system)**
- Debugged and completed dome-only system's NAMD equilibration (root cause: missing `CUDASOAintegrate off` — GPU-resident mode can't survive the harsh minimize→velocity-reassignment transition at step6.1; fixed by running that step in offload mode). Verified and ran equilibration for the parallel OpenMM-format CHARMM-GUI download too
- Ran a large, systematic benchmark sweep on Beagle3 across both engines: PE count, GPU-resident vs. offload mode, precision, integrator choice, vdW treatment, hydrogen mass repartitioning (HMR) + extended timestep (2fs→3/4/5fs), PME/reporting-frequency settings, and NAMD/OpenMM version. ~35 distinct configurations tested, several replicated 2-3× after early results looked inconsistent
- **Major confound found and fixed**: Beagle3 mixes A100 (nodes 0001-0022) and A40 (nodes 0023-0044) GPUs; early "inconsistent" results (especially OpenMM's) turned out to be pure hardware artifacts from jobs randomly landing on the slower A40s. Retroactively audited every prior job's `NodeList` via `sacct`; fixed going forward with `--constraint=a100` on all jobs
- **Major finding**: multi-GPU scaling is non-monotonic for this system size — 2 GPU gives ~1.5-2x speedup over 1 GPU, but 3-4 GPU regress *below* 1-GPU performance (root cause not fully confirmed; leading hypothesis is single-GPU PME serialization bottlenecking beyond 2 devices; `+pmePEs` unsupported on this NAMD build, so couldn't test directly). This contradicted Dr. Trung's prior data on a smaller system — confirmed it's a real system-size-dependent effect, not an assumption
- **Winning config**: NAMD 3.0.1, GPU-resident mode, HMR + 4fs timestep (with piston period/decay doubled for stability), 2 GPU / 16 PE, A100 → **16.71 ns/day**, beating best OpenMM (8.2.0, plain HMR+4fs, force-switch preserved, replicated) at 10.91 ns/day by ~53%
- Root-caused four distinct NAMD instability bugs along the way: missing `CUDASOAintegrate off`, insufficient `margin` for larger timestep, stale equilibration velocities inconsistent with HMR-repartitioned masses (fixed via `temperature $temp` instead of reusing `.vel`), and Langevin piston timescale mismatch at 4fs (fixed by doubling period/decay)
- Full results published as a Claude Artifact (interactive chart + per-setting-detail tables), and a copy-paste-ready markdown table for the lab's Google Doc

**Control system production restored**
- Found broken: wrong SLURM account (`pi-haddadian`, not in the beagle3 partition's `AllowAccounts` whitelist) and an outdated ad-hoc NAMD build. Fixed both (`beagle3-exusers` account, `namd/3.0.1-multicore-cuda` module); production resumed

**HMR decision for actual production — deliberated, not adopted**
- Confirmed HMR preserves structural/thermodynamic properties well (area-per-lipid, electron density, order parameters — per literature) but genuinely compromises kinetic/dynamical properties (diffusion coefficients, anything time-resolved), since it works by redistributing atomic mass, which directly changes the real-time dynamics via F=ma
- Since this project's core question involves membrane/lipid dynamics (and the literature review's own method list includes lateral diffusion coefficient via MSD), chose **not** to adopt HMR for production despite its ~2x speedup — `control` and `dome-model` both run non-HMR (2fs, standard piston), keeping every future kinetic analysis clean. Isolated HMR's exact contribution empirically: same 2GPU/16PE/A100/resident config, HMR on = 16.71 ns/day vs. HMR off = 8.23 ns/day, almost entirely attributable to the doubled timestep (per-step cost nearly identical either way)

**Full system (`full-model`) staged and equilibration started**
- Confirmed via direct verification that `dome-model` and `full-model` both use the same AF3 ic-minimized protein structure (not different structure-building approaches) — so any future lipid-composition comparison isn't confounded by a different protein build
- Equilibration submitted (job 52124727) with the same proven-robust recipe as everything else: NAMD 3.0.1, 1 GPU, offload mode, A100-pinned

**Benchmark file cleanup**
- Archived ~250 leftover benchmark files (9.3 GB of 19 GB total) out of `dome-model`'s live production directory into a sibling `benchmarks_archive/` folder, after confirming every useful number from the whole sweep was already captured in the results table/artifact

---

## July 7–8, 2026 — Days 26–27

**AF2 dome-24 (job 50972223) — confirmed FAILED, total loss**
- `sacct` confirms `State=TIMEOUT`, Start 2026-06-21T19:02:58 → End 2026-07-05T19:03:14, Elapsed exactly 14-00:00:16
- Zero PDB models ever produced (only `features.pkl` + `msas/`); AF2 does not checkpoint mid-model, so the full 14-day bigmem allocation is a total loss
- Officially abandoned — AF3 `opt1_extended` path (below) is now primary

**AF3 `opt1_extended` — completed, merged, minimized, and compared**
- Server job completed July 6: HflK 200–419 × 12 + HflC 200–334 × 12, template left unconstrained
- Checked the actual template CIFs used: AF3 did **not** use 9CZ2 — it templated on **7VHQ/7VHP** (2021 closed/symmetric cryo-EM structure of the same complex) and **8Z5G**, confirmed via `_entry.id` fields in the downloaded template mmCIFs
- Built two chain-mapping variants merging the predicted 356–419 region onto the existing dome (9CZ2 + HflC 161–190 loop + X/V/W completed chains):
  - `ic` (interchangeable) — predicted chains reassigned by best geometric fit to each dome position
  - `op` (order-preserving) — predicted chains kept in AF3's raw output order
- Solvated and minimized both on Midway3 (jobs 51481766 / 51481765, 10,000 steps each, ~1.456M atoms) — both converged cleanly, zero M3-vs-dome clashes <2.0 Å in either
- Compared M3 tail CA-displacement during minimization as a proxy for initial fit quality: `ic` overall RMSD 2.19 Å vs `op` 2.28 Å, lower in 10/12 chains → **chose `ic`** as the structure to move forward with
- Final NAMD potential energy was nearly identical between variants (diluted by the ~1.45M-atom water box — not a useful discriminator)
- Saved locally: `dome_m3_af3_ic_minimized_final.pdb` (full complex, 36 chains) and `dome_m3_af3_ic_minimized_final_noftsh.pdb` (dome-only, 24 chains, A–X)
- Deleted other local PDBs to free space (all recoverable from Midway3 or git history): `dome_m3_af3_ic_solv.pdb`, `dome_m3_af3_op_minimized_final.pdb`, `dome_m3_af3_op_solv.pdb`, `dome_m3_rotated.pdb`, `dome_with_m3_grafted.pdb`
- Sent `dome_m3_af3_ic_minimized_final.pdb` to Dr. Ghanbarpour with full methodology, referencing the June 13 Zoom meeting

**ThinLinc / VMD segfault — root-caused, not yet fully resolved**
- VMD segfaults on ThinLinc because the default web URL load-balances onto a GPU-less login node (login5), falling back to crashing `llvmpipe` software rendering
- Tried `sviz` (Midway2-only, doesn't exist on Midway3), then `sinteractive -p gpu -G 1 --account=pi-haddadian` (works, but queue wait)
- Emailed Dr. Trung and RCC's Dossay Oryspayev; Dossay suggested login3/login4 directly — discovered the **web ThinLinc client can't end an existing session** (only the native client can, via an Options checkbox), so it kept reconnecting to the login5 session regardless of URL
- Installed VMD natively on this Mac instead (`/Applications/VMD 2.0.0a7-pre2.app`) as the reliable fallback — used it to visually/numerically compare the `ic` vs `op` structures

**New machine note**
- This session (from `Kenneths-MacBook-Pro.local`) required re-establishing the SSH ControlMaster socket multiple times (1h `ControlPersist` expiring); confirmed the socket only forms when connecting via the `midway3` alias (`ssh midway3`), not the full hostname

**Beagle3 access granted — first direct login**
- Added a `beagle3` entry to `~/.ssh/config` (same ControlMaster pattern as `midway3`); confirmed working after user ran `ssh beagle3` + DUO once
- Also discovered `/scratch/midway3` and `/project2/haddadian` are both directly readable from Beagle3 login nodes (not just the shared `project2` staging area) — no need to bounce through Midway3 for cross-cluster file checks

**Control system production naming bug found and fixed**
- Investigating `control_prod/step7_22` (Kaylie's Beagle3 run) revealed `run_prod_gpu.sh` used `STEPS_PER_RUN=25000000` (50 ns/submission) — far more than the ~10 ns that fits in the 36h `beagle3-prio` wall time at observed throughput (~0.026 s/step). Job 50868924 was killed by `TIME LIMIT` at 5,015,000/25,000,000 steps (~10.03 ns actual, not the intended 50 ns)
- Root cause of the confusion: our script names outputs by **sequential run index** (`NEXT = last + 1`), not content. Traced Rajiv's older convention (`/project2/haddadian/rajiv/namd/step7_run20/50/80.inp`) and confirmed his `step7_N` means **N = cumulative ns since step6.6** (a 10 ns block from `step7_10` → `step7_20`; a 30 ns block `step7_20` → `step7_50`, etc.) — the filename is deliberately sized to equal the running total
- Recomputed true cumulative for the control system as of the Beagle3 restart point: step7_1–19 (19 ns) + step7_20 partial (0.5 ns, from its own `.out` log, not the ~0.42 ns previously estimated) + step7_21 8 ns block (Midway3) = 27.5 ns, + step7_22 actual 10.03 ns (Beagle3) = **37.53 ns true cumulative**
- Renamed `step7_22.*` → `step7_37.*` on Beagle3 (`control_prod/`) to match; **rewrote `run_prod_gpu.sh`** to (a) name outputs by cumulative ns going forward, (b) use 8 ns/block (4,000,000 steps — matches Rajiv's own historical block size for this system, ~29h at observed throughput, safe margin under the 36h cap), (c) track true cumulative in a `cumulative_ns.txt` ledger that self-heals (renames + corrects the ledger) if a future run gets truncated by wall time again
- Attempted to submit the next block (`step7_45`, 37.53 + 8 ns) as the first real test of direct Beagle3 access — **blocked**: `sbatch` rejects both `beagle3-exusers` (not a member) and `pi-haddadian`/`bios10603`/`bios10602` (valid accounts, but `scontrol show partition beagle3` shows `AllowAccounts` is a specific PI whitelist that does not include `pi-haddadian`; only `beagle3-exusers`, `rcc-staff`, and a handful of unrelated PI groups are allowed). Newly-granted Beagle3 access appears to be login/filesystem-only (`ssh beagle3` works, `/project2` and `/scratch/midway3` are both readable) — **not** a compute allocation. Job submission needs `pi-haddadian` added to the partition's `AllowAccounts`, or the user added under `beagle3-exusers` like Kaylie. Follow up with RCC or Dr. Haddadian. Script/naming fixes (`run_prod_gpu.sh`, `step7_22`→`step7_37` rename, `cumulative_ns.txt` ledger) are in place and ready to run once submission rights are granted.

---

## July 2, 2026 — Days 23–25

**AF2 dome-24 (job 50972223) — still running, past self-imposed cancel date**
- At session start: **10d 16h elapsed**, still RUNNING on midway3-0318; only `features.pkl` + `msas/` in output — no PDB models
- Past the self-imposed July 1 (day 10) cancel point; hard kill ~July 5 19:03 CDT (~3 days remaining)
- Decision: let it ride to wall time (no cost; remote work week anyway)

**AF3 server — first result: tails entangled with dome**
- First server job (hflk_m3_dome_server: HflK 319–419 × 12 + HflC 270–334 × 12, 1,992 tokens) completed
- Result: M3 tails predicted inside/entangled with dome interior — not physically meaningful
- Root cause: query too short → only 37-residue helical anchor per chain; model had no directional context to send M3 downward; dome interior appeared as open space
- Resubmitted with seed 2 → "Model inference failed" (transient server error)

**AF3 server — two new jobs with extended queries**
- Both use "Use PDB templates up to 01/01/2026" (9CZ2 found automatically); submitted July 2

| Job | Query | Tokens | Rationale |
|-----|-------|--------|-----------|
| server_opt1_extended | HflK 200–419 × 12 + HflC 200–334 × 12 | 4,260 | Longer helical stalk gives directional context for M3 |
| server_opt2_halfdome | HflK 79–419 × 6 + HflC 1–334 × 6 | 4,050 | Half dome, full sequences; richer per-chain context |

- JSONs: `server_opt1_extended.json`, `server_opt2_halfdome.json`
- HflK starts at 79 (not 1) in opt2 to avoid confusing AF3 with TM region lacking membrane context

**AF3 Midway3 (job 51362125) — failed; fixed and resubmitted**
- Crash at data pipeline stage: `ValueError: Protein chain A has unpaired MSA, paired MSA, or templates set only partially`
- Root cause: `hflk_m3_dome.json` had `templates` field set (custom mmCIF for HflK 319–355 and HflC 291–329) but no `unpairedMsa`/`pairedMsa` fields — AF3 requires all-or-nothing
- Fix: removed `templates` from both protein entities; pipeline now searches MSA + templates automatically (finds 9CZ2 via date cutoff)
- Resubmitted as **job 51372128** (gpu partition, 2× A100, 24h); input: HflK 319–419 × 12 + HflC full × 12 = 5,220 tokens

**AF3 template note**
- Custom mmCIF template upload on AF3 server required a mapping file (JSON referencing CIF filenames); format figured out but abandoned in favor of auto PDB template search — 9CZ2 is in PDB and AF3 finds it automatically
- AF3 local requires MSA+templates all-or-nothing (unlike AF2 which always runs its own pipeline); server abstracts this away entirely

**Midway3 outage (July 1)**
- Brief: `ssh midway3` → "Connection refused"; resolved same day; job 50972223 unaffected

**Main system equilibration — confirmed complete**
- step6.1–6.6 DCDs all present on Midway3; step6.6 restart files (`.coor`, `.vel`, `.xsc`) intact
- Ready to start production (step7) on Midway3

**Working from home (July 2)**
- MacBook non-functional; working via PC; UPS delivery day

---

## June 25–29, 2026 — Days 18–22

**AF2 dome-24 (job 50972223) — wall time extended to 14 days; still no model**
- RCC (Dossay Oryspayev) extended the job's TimeLimit in place: 4 days → **14 days** on June 25 request (hard kill now ~July 5 19:03 CDT)
- As of June 28: **~152h elapsed**, process healthy (PID 2108493, 806% CPU = ~8 cores, 748 GB RSS, no restart), monitor `0/1`, only `features.pkl` written — **no PDB model yet**
- Runtime now exceeds the optimistic estimate (~125h) and is approaching the mid estimates (~160–200h); pessimistic O(N³)×full-recycle estimate is ~380h
- Self-imposed decision point: cancel rather than ride to July 5 if no output by ~July 1 (day 10)

**Runtime prediction exercise**
- Built a research prompt (system size, partition, per-job sacct timing for all past AF2 runs) to estimate single-model CPU inference time; fed to three LLMs → estimates 125h / 160h / 380h total
- Key finding from live process check: AF2-on-CPU uses only ~8 of 48 allocated cores (806% CPU) — memory-bandwidth/XLA bound; more cores won't help much (RCC guidance: >8 cores wasted for AF2)
- Consensus: won't finish before the original 4-day wall; extension was the only way to save the sunk compute. Asked RCC for 14 days (granted)

**Midway3 outage (June 29)**
- Login node unreachable cluster-wide: `ssh midway3` → "Connection refused", minutes later "Connection timed out" (port 22 refused/closed from routed path too)
- No maintenance notice on RCC homepage; refused→timed-out shift is consistent with a node taken fully offline (possible scheduled maintenance)
- **Resolved (June 29 later)**: cluster came back; job 50972223 confirmed RUNNING at ~193h elapsed — survived the outage; still no PDB output

**GPU benchmarks (full 9cz2, 1.7M atoms) — 2-GPU complete**
- 2 GPU + 16 PE (job 51044708) completed June 25: **7.40 ns/day** (0.0233 s/step) — only **1.32×** over 1 GPU + 16 PE (5.59) → strong diminishing returns from the 2nd GPU (consistent with Dr. Trung)
- 4 GPU + 32 PE (51044709) still queued (est. start ~June 26, now affected by the outage)
- Benchmark doc tables (namd_performance.md / CLAUDE.md) to be finalized once the 4-GPU job completes — holding per decision to record both together

**Structure asymmetry email (June 29)**
- Rajiv noted chains A/M/S M3 tails are intertwined in the structure
- Cause: per-chain independent rotation search assigned different angles to each M3 tail → asymmetric orientations globally
- Not a concern: M3 (pLDDT ~44) is intrinsically disordered; initial placement doesn't matter for MD

**Lipid proximity plot**
- Generated `analysis/lipid_proximity_FtsH_nodome.png` from `lipid_count_FtsH_nodome_namd.dat` (98 frames, ~10 ns, no-dome FtsH) via `analysis/plot_lipid_proximity.py`
- All five species flat over the window; counts track bulk membrane composition (DPPE ~110, POPG/DOPG ~20–26, LOACL1/TLCL1 ~4–5) — no obvious enrichment/depletion in this short run

---

## June 24, 2026 — Day 17

**Clash analysis on dome_m3_minimized_v3.dcd (final frame)**
- 12 flagged contacts < 1.5 Å — all are ASP356 N ↔ LEU355 C on each of the 12 HflK chains
- These are peptide bond geometry at the 355|356 grafting junction (~1.3–1.4 Å = correct bond length)
- Not real steric clashes — M3 is clean against all dome residues
- Structure is ready for CHARMM-GUI

**PDB extraction from minimized DCD**
- Extracted protein-only PDB from final frame via VMD: `dome_m3_minimized_v3_protein.pdb`
- Discovered `dome_m3_rotated.pdb` input included FtsH (full complex, not dome-only); segnames 0P2–9P2, YP1, ZP1 present
- Created dome-only version by filtering FtsH segnames: `dome_m3_minimized_v3_dome.pdb` (126,696 atoms, HflK + HflC only)
- Note: VMD hex atom numbering (>99,999 atoms) present in both PDBs — may need renumbering before CHARMM-GUI

**GPU benchmark jobs submitted (Midway3 gpu partition, A100)**
- Background: Dr. Trung (RCC) reported 1 GPU + 8 PE = 13 ns/day for 1M atom system on Beagle3 A100; multi-GPU gives no benefit at this scale
- Submitted 4 benchmark jobs on Midway3 A100 node (midway3-0294) using NAMD 3.0.1-multicore-cuda
- Config: 50,000 steps (0.1 ns) from step6.6 equilibration restart of main 9cz2 system (1,733,042 atoms)
- `CUDASOAintegrate on` (GPU-resident mode); if RATTLE errors occur, will disable

| Job ID | Config | GPUs | PEs |
|--------|--------|------|-----|
| 51044706 | bench_1gpu_8pe | 1 | 8 |
| 51044707 | bench_1gpu_16pe | 1 | 16 |
| 51044708 | bench_2gpu_16pe | 2 | 16 |
| 51044709 | bench_4gpu_32pe | 4 | 32 |

- 1-GPU jobs completed; 2- and 4-GPU still PENDING at session end

| Job ID | Config | ns/day | Wall time |
|--------|--------|--------|-----------|
| 51044706 | 1 GPU + 8 PE | ~3.8 | 44 min |
| 51044707 | 1 GPU + 16 PE | ~5.6 | 33 min |
| 51044708 | 2 GPU + 16 PE | — | pending |
| 51044709 | 4 GPU + 32 PE | — | pending |

- Notable: unlike Dr. Trung's 1M atom system (optimal at 8 PE), 1.7M system benefits from 16 PE (+47%)

**AF2 dome-24 (job 50972223)**
- ~66h elapsed; still RUNNING; 0 models complete; ~30h remaining on 4-day wall time
- Dr. Haddadian email: suggested extending wall time via RCC + resubmitting a partial system
- Note: current job is already dome-only (no FtsH); partial resubmission would mean fewer chains (e.g. opening region only)
- Action: draft RCC extension request + prepare partial FASTA — pending

---

## June 23, 2026 — Day 16

**NAMD minimization config fixes**
- Added missing output controls: `dcdfreq 100`, `restartfreq 500`, `XSTFreq 100`, `outputEnergies 40`
- Fixed parameters: `stepspercycle 20→8`, `nonbondedFreq 1→2`, added `fullElectFrequency 4`
- Previous run (v1, job 51015689) had no DCD; outputs renamed to `dome_m3_minimized_v1.*`

**Minimization v2 — B=500 restraints (wrong)**
- Submitted 2-node (51030625, later cancelled) and 1-node (51031241, completed 45 min / 2708s)
- Clash check on final frame: 11 clashes < 1.5 Å, min distance 1.205 Å — M3 stuck against frozen dome
- Root cause: B=500 is far too stiff (essentially freezes dome solid); Dr. Haddadian's recommendation is B=10

**Minimization v3 — B=10 restraints (correct)**
- Updated `04_make_restraints.py`: B=500 → B=10; regenerated `restraints.pdb` on Midway3
- Output renamed to `dome_m3_minimized_v3`
- 2-node (51034782): completed 25 min / 1507s — `dome_m3_minimized_v3.dcd` downloaded locally
- 1-node (51034788): RUNNING at session end (~38 min elapsed, expected ~45 min)
- v3 clash count not yet checked — pending

**Minimization scaling benchmark (water-only solvated system, 1,452,343 atoms)**

| Nodes | CPUs | WallClock | Restraint |
|-------|------|-----------|-----------|
| 4 (v1) | 192 | 919s (15 min) | B=500 |
| 2 (v3) | 96 | 1507s (25 min) | B=10 |
| 1 (v2) | 48 | 2708s (45 min) | B=500 |

**Lipid proximity analysis — no-dome FtsH**
- Ran `lipid-prox-FtsH-namd.tcl` (adapted) on `namd_caslake/` no-dome system: step7_production + step7_2–11 (98 frames, ~10 ns)
- FtsH TM selection: segnames PROV/W/X/Y/Z + PRAA-PRAG, resid 1–22 and 97–120; cutoff 6 Å
- Job 51033869 completed; node failure caused one requeue (output wiped and rerun)
- Added `--no-requeue` to v2 job (51035563, still running); both write to distinct output files
- Output downloaded locally: `analysis/lipid_count_FtsH_nodome_namd.dat`

**AF2 dome-24 (job 50972223)**
- ~47h elapsed at session end; 0 models complete; 748 GB RAM stable, ~755% CPU
- stderr silent since 19:12 CDT June 21 (normal — AF2 logs nothing during neural network inference)
- 4-day wall time was a rough guess; completion time genuinely unknown; failure risk is real
- Cannot rely on this job — M3 grafting + minimization approach must work independently

**GPU scaling email**
- Dr. Zand response: single A100 node estimated 60–80 ns/day for 1.7M atom system; referred to Dr. Trung (ndtrung@uchicago.edu) for deeper expertise
- Drafted follow-up email to Dr. Trung citing Zand referral

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
