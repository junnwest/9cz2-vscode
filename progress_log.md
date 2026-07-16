# Research Progress Log — 9cz2 FtsH•HflK/C Project

**PI**: Dr. Haddadian  
**Researcher**: Jun-Seo Yang  
**Start date**: June 8, 2026  
**Cluster**: Midway3 (`/scratch/midway3/junseo/26summer-research/`)

---

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
