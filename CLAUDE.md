# 9cz2 Research — Session Context

> **This file is kept deliberately lean — it is loaded in full on every turn.** Dated narrative,
> diagnostic play-by-plays, and superseded content live in `progress_log.md` instead (not
> auto-loaded; read it only when you need the history behind a decision). If you're about to add a
> multi-paragraph dated writeup here, it probably belongs in `progress_log.md` with a one-line
> pointer left here.

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
| SSH config | `~/.ssh/config` — has a `Host midway3` entry (`HostName midway3.rcc.uchicago.edu`, `User junseo`, `ControlMaster auto`, `ControlPath ~/.ssh/cm-%r@%h:%p`, `ControlPersist 1h`); same pattern for `Host beagle3` and `Host midway2` |
| GitHub SSH | already working (`~/.ssh/id_ed25519`, `Host github.com` entry); no deploy key needed on this machine |
| git binary | system git at `/usr/bin/git` (no CLT/Xcode license issue here) |
| VSCode Remote-SSH | extension not yet installed — install `ms-vscode-remote.remote-ssh` from the Extensions panel (⇧⌘X); the `code` CLI is not on PATH here |
| Local VMD | `/Applications/VMD 2.0.0a7-pre2.app` — real binary at `Contents/vmd2/lib/vmd_MACOSXARM64`, launch with `VMDDIR=".../Contents/vmd2/lib"` set (the bundled `vmd` wrapper script has a hardcoded build-machine path and fails standalone) |

Session connection flow is the same as the lab Mac: user runs `ssh beagle3` (primary cluster) or
`ssh midway3` in a terminal to open the ControlMaster socket (password + DUO), then Claude's Bash
tool reuses that socket via plain `ssh beagle3 "<command>"`. Socket expires after 1h idle.

---

### Step 1 — Open the SSH ControlMaster socket (user action required)

**Beagle3 is the primary cluster for all current production/equilibration/analysis work** — see
"Current Systems" below. Midway3 is used only for AlphaFold jobs and legacy files.

**Tell the user:**

> Open a local terminal and run:
> ```
> ssh beagle3
> ```
> Complete the DUO two-factor authentication prompt. Leave that terminal open or close it — the
> socket persists for 1 hour. Let me know when done. (For Midway3-specific work, same thing with
> `ssh midway3`.)

### Step 2 — Verify the connection

```bash
ssh beagle3 "echo OK"
```

If it prints `OK` immediately (no DUO prompt), the connection is ready. If it fails or prompts for
DUO again, ask the user to re-run `ssh beagle3` in their local terminal.

### Step 3 — Run the startup status check

```bash
ssh beagle3 "squeue -u junseo --format='%.10i %.22j %.9T %.11l %.20S %R'"
```

Compare against the "Current Systems" table below — flag anything unexpectedly idle, anything
about to be killed by a scheduled maintenance reservation (`scontrol show res` if queue entries
show `ReqNodeNotAvail`), and any GaMD job that has stopped (needs `make_gamd_restart.py`, see
Cluster Operations below).

### What does NOT need per-session setup

- **SSH keys** — already installed on Beagle3/Midway3; no password after the ControlMaster socket is open
- **pi-haddadian group / beagle3-exusers account** — already set up
- **NAMD/GROMACS modules** — loaded inside SLURM job scripts; no manual loading needed
- **Git** — configured locally; cluster files are never committed
- **VSCode Remote SSH** — optional, for file browsing; reuses the ControlMaster socket once open

## Local Machine Setup (BSCD401-5, lab Mac)

Shared lab computer; project files live in an encrypted vault.
- **Vault**: `~/kenneth.sparsebundle` (AES-256, 5 GB) — mount: `hdiutil attach ~/kenneth.sparsebundle` → `/Volumes/kenneth`; unmount: `hdiutil detach /Volumes/kenneth`; resize: `hdiutil resize -size 10g ~/kenneth.sparsebundle`
- **VSCode working folder**: `/Volumes/kenneth/9cz2-vscode`
- **Deploy key**: `/Volumes/kenneth/.ssh/9cz2_deploy`
- **git binary**: `/Library/Developer/CommandLineTools/usr/bin/git` (system git blocked by Xcode license)

---

## Project Overview

Summer 2026 research investigating the opening mechanism of the dome structure in the FtsH•HflK/C complex (PDB: 9cz2) in *E. coli*.

**PI**: Dr. Haddadian
**Predecessor**: Rajiv (Kenneth Yang) — built the complete structure and ran early test systems prior to this summer
**Start date**: June 8, 2026
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

## Structure Preparation (done by Rajiv + this summer, before MD)

Full narrative (AlphaFold runs, HflK M3 rotation search, monomer-approach dead end, Rajiv's
pre-production minimization) is archived in `progress_log.md` (June 2026 entries + the Aug 6
archive block). Current-state facts still needed for selections/provenance:

- **Two classes of gaps were filled before MD**: HflC residues 161–190 (AlphaFold-generated) and
  chains X/V/W bottom halves (copied from resolved chains A/B/T, RMSD-superimposed on TM helix
  region resid 269–348).
- **Current structure files** (repo root, untracked — large files never committed):
  `dome_m3_af3_ic_minimized_final.pdb` (full complex, 36 chains, 11 MB) and
  `dome_m3_af3_ic_minimized_final_noftsh.pdb` (dome-only, 24 chains A–X, 10 MB). These derive from
  the AF3 `opt1_extended` prediction (HflK/HflC stalk region extended for directional context so
  M3 wouldn't fold into the dome interior), NAMD-minimized, with the "interchangeable" (`ic`) chain
  mapping chosen over "order-preserving" (`op`) — lower M3 CA-displacement in 10 of 12 chains.
  AF3 templated on **7VHQ/7VHP** (the group's 2021 closed structure) and **8Z5G**, not on 9CZ2 itself.
- **AF2 dome-24** (a full 24-chain AlphaFold2 multimer run attempting to fill all three gaps at
  once) **FAILED** — TIMEOUT after the full 14-day bigmem allocation, zero model output ever
  produced. Dead end, not retried; AF3 `opt1_extended` → `ic` is the path that succeeded.
- **`reference_structures/ghanbarpour_closed1_complete.pdb`**: a gap-filled, correctly-oriented
  version of Dr. Ghanbarpour's closed1 reference structure, built for a *new* CHARMM-GUI submission
  (not for RMSD/analysis — see [[ghanbarpour_structure_completion]] in memory). Global orientation
  bug found+fixed Sep 2026 (was tilted, not centered — build script only did local per-chain grafting
  fits, never touched the global frame); FtsH's off-center position within the ring is inherited
  from Ghanbarpour's own raw structure, confirmed not a bug, left as-is per user decision.

### Chain ID / Segname mapping (`9cz2minimized_ftsh_fixed.pdb`-era naming)
- **HflK chains**: A, C, E, G, I, K, M, O, Q, S, U, X → segnames AP1, CP1, EP1, GP1, IP1, KP1, MP1, OP1, QP1, SP1, UP1, XP1
- **HflC chains**: B, D, F, H, J, L, N, P, R, T, V, W → segnames BP1, DP1, FP1, HP1, JP1, LP1, NP1, PP1, RP1, TP1, VP1, WP1
- **FtsH chains**: Y, Z (soluble, segnames YP1, ZP1) + 0–9 (TM, segnames 0P2–9P2)
- Always use segname for selection — chain IDs are less reliable
- **Note**: current CHARMM-GUI PSFs (full-model/full-bact rebuilds) use different, empirically-determined
  `PRO*`/`PRA*` segnames — see the FtsH section below, not this table, for those.

---

## Simulation Stack

| Component | Tool |
|-----------|------|
| MD engine | NAMD 3.0.1 (GPU, current) |
| System builder | CHARMM-GUI Membrane Bilayer Builder |
| Enhanced sampling | GaMD (Gaussian Accelerated MD) |
| Coarse-graining | Martini 3 (`martinize2` + `insane`), GROMACS |
| Visualization / scripting | VMD |
| Cluster | Beagle3 (primary), Midway3 (AlphaFold + legacy) |

### Membrane Compositions
**Composition #1** ("generic model"): DPPE 70% / POPG 12.5% / DOPG 12.5% / LOACL1 2.5% / TLCL1 2.5%.
Matches the textbook whole-cell/bulk *E. coli* inner-membrane average.

**Composition #2** ("bacterial"/cardiolipin-microdomain): 74% PG (37% POPG + 37% DOPG), 20%
cardiolipin (10% LOACL1 + 10% TLCL1), 6% DPPE. Does not match any bulk average — the inverse of
composition #1. Cardiolipin-enriched microdomains are a distinctively bacterial signature and
cardiolipin specifically controls HflK/C membrane localization (PMC10434171); composition #2
represents the actual local lipid environment HflK/C likely lives in.

### NAMD Production Parameters (all-atom systems)
- Force field: CHARMM36m (`par_all36m_prot.prm`, `par_all36_lipid.prm`, etc.)
- Timestep: 2 fs (`rigidBonds all`), 303.15 K Langevin thermostat (damping 1 ps⁻¹), 1.01325 bar Langevin piston NPT (period 50 fs, decay 25 fs)
- cutoff 12 Å, switchdist 10 Å, pairlistdist 16 Å, PME, PMEGridSpacing 1.0 Å
- `wrapAll on`, `useFlexibleCell yes`, `useConstantRatio yes`
- DCD every 50,000 steps (100 ps); 1 ns per production block (500,000 steps)
- Equilibration: CHARMM-GUI standard 6-step protocol (step6.1–step6.6)
- **Production config** (decided after a ~35-config NAMD-vs-OpenMM benchmark sweep — NAMD 3.0.1
  GPU-resident won at 16.71 ns/day vs OpenMM's 10.91 ns/day; full methodology in
  `analysis/namd_vs_openmm_benchmark_plan.md`):
  - **All 5 systems**: GPU-**resident** (`CUDASOAintegrate on`), 2 GPU / 16 PE. ~8 ns/day for
    dome-only/membrane-only, ~7 ns/day for FtsH systems (bigger, ~2.8× the atom count of `control`).
    Non-HMR (HMR gives ~2× speed but measurably compromises kinetic/dynamical properties — not
    adopted). **FtsH systems were offload-only until Aug 22** (resident used to crash them with
    `SequencerCUDA: Atoms moving too fast` — fixed via a `margin` setting, diagnostic chain archived
    in `progress_log.md`); both switched to resident that day and have run clean since.
    **`control` ran offload on 4 GPU (missing `CUDASOAintegrate` entirely) until Sep 7** — found via
    a project-wide config audit prompted by an unexplained speed discrepancy between `control`'s
    plain-NAMD and GaMD runs. No benchmark ever justified 4 GPU specifically; this project's own
    sweep found 3-4 GPU regresses *below* 1-GPU resident performance. Fixed to match the other 4
    systems (resident, 2 GPU).
  - **Equilibration, all 5 systems**: offload mode regardless of system — resident mode can't
    survive the minimize→velocity-reassignment transition at step6.1.
  - Always pin `--constraint=a100` — Beagle3 mixes A100 (nodes 0001-0022) and A40 (0023-0044).
  - **CHARMM-GUI gotcha, every fresh download**: `CUDASOAintegrate` is missing entirely by default
    from step6.x/step7_production.inp — must be patched in manually (insert before `rigidBonds
    all`) or GPU mode silently falls back to something else.
- **Production loops 1 ns chunks within a job** (`run_prod_gpu.sh`) until wall-time is nearly used
  or a per-job `MAX_CHUNKS=12` cap, then stops cleanly. Nothing auto-chains ACROSS jobs — check
  `squeue` each session and resubmit idle production; this is the single most common failure mode
  (jobs finish clean at exit 0 and just sit there).
- **Unified `TARGET_NS=250` hard cap, all 5 systems** (Sep 20, 2026, limited compute allocation) —
  set via `export TARGET_NS="250"` in each system's `job-submit-beagle3*.sbatch`, read by
  `run_prod_gpu.sh`'s pre-existing safety-stop. Supersedes an earlier tiered version (`control`
  250 ns, `dome-model`/`dome-bact` 300 ns, `full-model`/`full-bact` uncapped) — now all five match.
  **Caveat**: the cap is only checked at the START of each 1 ns chunk, so a system can overshoot by
  up to ~1 ns before stopping (`control` stopped at 250.38, not exactly 250 — expected, not a bug).
  **Also**: changing this value in the `.sbatch` file does NOT affect an already-running job — the
  env var is fixed at that job's own submission time. Any system already mid-run under an old cap
  needs to be cancelled and resubmitted for a new cap to actually take effect (done for `dome-bact`
  on Sep 20, since its live job still had the stale 300 ns cap baked in).

---

## Current Systems

**Always verify against the live cluster at session start (Step 3 above) — this table is a snapshot.**

**Beagle3 is the primary cluster for all production/equilibration systems**, `/scratch/beagle3/junseo/`.
**`/project2/haddadian` is unreliable** — it is actually served by Midway2 (`midway2_cap` filesystem,
confirmed via `mount | grep project2`), not a Beagle3/Midway3-native mount, and has gone
unreachable from both for days at a time. `ssh midway2` is the authoritative host for it if you
must use it; prefer moving anything off `/project2` onto Beagle3 scratch instead.

### The 5 systems (5 systems × 3 methods = 15-run target), plus a new 6th (`control-bact`)

| Name | Protein content | Lipid composition |
|---|---|---|
| `control` | none (membrane-only baseline) | Composition #1 |
| `dome-model` | dome only (24 HflK/HflC chains, no FtsH) | Composition #1 |
| `dome-bact` | dome only | Composition #2 |
| `full-model` | full dome + FtsH (resid 1–120, see FtsH section) | Composition #1 |
| `full-bact` | full dome + FtsH (resid 1–120) | Composition #2 |
| `control-bact` | none (membrane-only baseline) — **new, Sep 22-23** | Composition #2 (see caveat below) |

**`control-bact`** (CHARMM-GUI job `8966184860`, local `~/Downloads/charmm-gui-8966184860/`): fills
the missing protein-free baseline for composition #2 (`control` itself is composition #1 only). Box
304.6 x 304.6 x 75 Å. As-built: POPG 37.0% / DOPG 37.0% / DPPE 6.0% / LOAC 10.0% / TYCL1 10.0% —
**the second cardiolipin species is `TYCL1` (tetra-hexadecenoyl, C16:1), not `TLCL1`** (tetralinoleoyl,
C18:2) used in `dome-bact`/`full-bact` — flagged, not changed, unconfirmed whether intentional.
Setup on `/scratch/beagle3/junseo/control-bact/` (note: `step5_assembly.str` must stay a sibling of
`namd/`, not inside it — `step6.1` does `exec tr ... < ../step5_assembly.str` at runtime). Two upload
bugs hit and fixed during setup (missing `step5_assembly.str`, missing 483 MB `restraints/` dir +
`step5_input.colvar.str`) — full writeup in `progress_log.md`, Sep 22-23 entry. **Equilibration
status UNCONFIRMED as of Sep 23** — job 59421265 resubmitted after fixing the restraints/ upload,
but the Midway3 SSH socket dropped before the outcome could be checked. Verify `sacct -j 59421265`
first thing next session before assuming it's healthy. Production scripts (`run_prod_gpu.sh` /
`job-submit-beagle3-prod.sbatch`) and GaMD are not set up yet — pending equilibration confirmation.

`full-model`/`full-bact` are built from the identical protein structure (12 HflK 79–419, 12 HflC
1–329, 12 FtsH 1–120) and differ only in lipids — the composition comparison is not confounded by
a different protein build. Same holds for `dome-model`/`dome-bact` (both from
`dome_m3_af3_ic_minimized_final_noftsh.pdb`).

**Beagle3 paths**: `control`, `dome-bact`, `full-bact`, `full-model` all under
`/scratch/beagle3/junseo/{system}/{namd,gamd}/` (system-first, since NAMD+GaMD share large
PSF/PDB/toppar inputs). `dome-model` may still be at its `/project2` staging path — verify with
`squeue`/`ls` before assuming; don't rename a directory a running SLURM job has as its WorkDir.
Martini variants live at `/scratch/beagle3/junseo/martini-sweep-{v14,v15,v16}/` (method-first, since
Martini shares nothing with the AA systems). **v1-v13 were removed from the cluster Sep 7** during a
disk-quota cleanup — all fully analyzed (see the restraint-scheme sweep table below, conclusions
unchanged) with confirmed-complete local copies first (`trajectories/martini/` and
`trajectories/martini_sweep/`), so cluster deletion cost nothing. v14/v15/v16 (the active timestep-
sensitivity comparison) remain on cluster and are the only Martini jobs still runnable/resubmittable.

### Status snapshot — Sep 22, 2026 (last live check; verify fresh at session start)

| | NAMD production | GaMD (total = equil + prod, equil is always 45 ns) |
|---|---|---|
| `control` | 250.38 ns — hit the 250 ns `TARGET_NS` cap, stopped as designed | 245.04 ns (45 + 200.04 prod), `gamd-prod12` running (job 59417164) after finding `prod11` idle ~1.5 days |
| `dome-model` | 202.05 ns, running (job 59367403) | 120.27 ns (45 + 75.27 prod), `prod5` running |
| `dome-bact` | 250.50 ns — hit the cap, stopped as designed | 101.75 ns (45 + 56.75 prod), `prod4` running |
| `full-model` | 109.5 ns, was idle → resubmitted (job 59417172), PENDING | 62.24 ns (45 + 17.24 prod), `prod1` running — equilibration now complete |
| `full-bact` | 119.0 ns, was idle → resubmitted (job 59417174), PENDING | 61.99 ns (45 + 16.99 prod), `prod1` running — equilibration now complete |

Beagle3's own login node SSH was unreachable Sep 22 (`Connection refused`) — confirmed this is
login-node-only, not a cluster outage: compute/GPU nodes and the scheduler are fine, jobs actively
`RUNNING` on `beagle3-00XX` nodes, confirmed via `squeue` run from Midway3 (same shared scheduler).
All Midway3-session work since has routed cluster access through `ssh midway3` accordingly — keep
doing this until Beagle3 login access is confirmed restored.

**All 5 systems now have GaMD running or queued** — a change from earlier in the project when
`full-model`/`full-bact` sat unstarted; see the GPU-resident section below for the migration.
Plain-NAMD production and GaMD for a given system are separate jobs/queue entries; check both.
**`dome-model` plain production was deliberately restarted from ns 183 on Sep 18**, discarding the
~40 ns that had accumulated since (ns 184-223, itself already missing its `.dcd` files from an
earlier archival gap — the simulation was never broken, just its *files*, but user chose a clean
gap-free branch going forward over keeping the extra already-completed ns). Old range archived
(not deleted) at `dome-model/namd/superseded_ns184-223_gap_restart/`. `dome-model`'s GaMD track is
untouched — separate checkpoint chain, branched off much earlier, unaffected.

**Only `control`/`dome-model`/`dome-bact` have completed GaMD equilibration** (production data
exists) — `full-model`/`full-bact` are still mid-equilibration, no GaMD production data for them
yet; relevant if asked to run any production-only analysis (e.g. convergence checks) across "all 5
systems."

**Beagle3 and Midway3 share ONE SLURM queue/scheduler — not separate resource pools.** Confirmed
Sep 17: `squeue -u junseo` run from either host shows identical job IDs/states/partition names.
Submitting a job "from Midway3" does not grant separate GPU allocation. The binding constraint is
the `gpu` QOS's **16 GPU/user cap** — as of Sep 17, 8 running jobs (2 GPU each) = 16/16, hence the
above PENDING jobs. (This is in addition to, not instead of, the already-known fact that
`/scratch/beagle3` is GPFS-mounted on Midway3 — filesystem AND scheduler are both shared.)

**Sep 7 disk-quota crisis, resolved**: Beagle3 scratch quota (400G soft limit) had been silently
exceeded for days with an expired grace period, blocking every write cluster-wide — the empty-queue
symptom this surfaced as. Freed ~155G (disposable backups, fully-analyzed/already-locally-copied old
Martini variants v1-v13, a stale duplicate directory, already-synced derived trajectory files, and
the big one: 41.6G of stale non-latest NAMD restart checkpoints — only the single latest per system
is ever needed to resume). One mistake happened and was caught/fixed during this: the
restart-checkpoint cleanup briefly broke `control`'s and `full-model`/`full-bact`'s resume chains by
deleting a checkpoint that turned out to still be needed; recovered using NAMD's separate *regular*
(non-restart) final-output files, which carry the same binary format and were still intact. See
`progress_log.md` for the full incident writeup.

**Sep 16-17 continuation**: cleanup redirected to `/cds2/haddadian/kenneth` (Midway3-mounted, GPFS-
visible from Beagle3, no laptop round-trip needed) for `dome-bact`/`dome-model` bulk trajectory
archival. A `rm -rf` on `dome-bact/namd` deleted essential operational files (restart checkpoint,
`cumulative_ns.txt`, toppar, sbatch scripts) alongside the intended bulk `.dcd` archival target;
recovered via full `rsync` restore from the cds2 backup. **Standing rule since**: only ever delete
`*.dcd` via targeted `find ... -delete`, never `rm -rf` a whole `namd/`/`gamd/` directory, even
right after a verified backup. Full incident in `progress_log.md`.

**Five side experiments running/queued on `control`** (all four GaMD-side tests branch from the
same `step7_210.restart` plain-production checkpoint — NOT `step7_21.restart` as earlier written
here, corrected Sep 18 — isolated from live production). **Priority scheme (Sep 18)**: core
production always wins — all 4 GaMD experiments run at `Nice=100000` (`scontrol update
JobId=X Nice=100000`) so the scheduler always prefers a waiting core job over a waiting experiment
for any freed GPU slot; experiments only advance opportunistically. Both existing/new sigma0P
variants (2.0, 4.0) run in parallel rather than picking one, for a 3-point comparison against the
6.0 baseline once all finish. All run equilibration in GPU-resident mode despite `control`'s own
real equilibration having stayed in offload mode throughout (Sep 18 finding, unresolved — the
resident-mode fix's validation scope for the *equilibration* phase specifically, vs. production
restarts, couldn't be confirmed since the original test's files are gone; decided to proceed and
diagnose reactively via two known failure signatures if something breaks: `Vmin`-collapse/
`sigmaV`-inflation, or `SequencerCUDA: Atoms moving too fast`):
- **Asymmetric sigma0 equilibration test** (`gamd-sigma-asym`: `accelMDGsigma0P=2.0`, total-
  potential boost target lowered; `accelMDGsigma0D=6.0`, dihedral boost left at baseline — more
  surgical than lowering both, since the total-potential boost dominates the combined ΔV. Started
  fresh from step 0 of its own dedicated equilibration schedule with these settings throughout, no
  parameter changed mid-run — verified via the restart file's own step counter). Continuation
  submitted job 59247853, queued (GPU cap) as of Sep 17.
  **Retracted claim (Sep 18)**: this used to say it "extends the earlier sigma0=4-vs-6 test, which
  found nearly identical boost statistics" — checked `sacct` directly, that test (job 57683980,
  `control/gamd-sigma4/`) actually **FAILED** after 1d3h, right at the edge of the Sep 7 disk-quota
  crisis (likely an innocent casualty, unconfirmed — its logs no longer exist). No such comparison
  was ever actually completed. The sigma0-tuning question is open, not settled — see the
  PI-requested sigma0P=4.0/D=6.0 full-length experiment (equilibration→production) being planned.
- **`fullElectFrequency=2`-without-GaMD test** (`gamd-fullelec2-noGaMD`, new Sep 17): same
  checkpoint/settings as an earlier `fullElectFrequency=2` GaMD attempt (job 57990267) that was
  previously assumed to have found a real instability — **also checked directly (Sep 18): that job
  failed in 3 seconds**, inconsistent with a genuine physics crash and much more likely a
  config/launch error whose actual cause was never retrieved (logs gone). So this isolation test's
  premise ("isolate whether GaMD is required to trigger the earlier-found instability") rests on an
  unconfirmed instability — still worth running, just not on the footing originally described.
  `accelMD off` — GaMD fully disabled for this test. Job 59247926, queued (GPU cap) as of Sep 17.
  User wants `fullElectFrequency=2` support as an actively-pursued, ongoing goal, not a one-off test.
- **sigma0P=4.0/D=6.0** (`gamd-sigma4-6`, PI-requested, new Sep 18): fresh full equilibration
  (45 ns) → ~20-30 ns production once equilibration completes. Verified via `diff` against the
  `gamd-sigma-asym` template that only `accelMDGsigma0P` (2.0→4.0) differs. Job 59271939.
- **`PMEInterpOrder=4`** (`gamd-pmeinterp4`, PI-requested, new Sep 18): down from this project's
  baseline of 6 (confirmed via actual config, not NAMD's usual default of 4) — same full
  equilibration→production scope. `accelMDGsigma0P` reverted to baseline 6.0 (the template it was
  built from had 2.0) so only `PMEInterpOrder` varies — verified via `diff`. Job 59271940.
- Also testing removing `margin`/`stepspercycle` entirely on `full-model` (Dr. Chen's suggestion,
  isolated test — `margin 5` was specifically added to fix a real resident-mode crash on the FtsH
  systems, so this is being verified before adopting broadly, not applied directly to live jobs).

### FtsH is only ~19% modeled (found Aug 2, rebuilt Aug 5, 2026)

**The deposited 9CZ2 structure resolves only residues 31–97 of FtsH's ~644** (entire cytoplasmic
AAA+ ATPase ring and M41 protease domain unresolved at 4.4 Å). `full-model`/`full-bact` were
rebuilt Aug 5 in CHARMM-GUI extending this to **resid 1–120** (still not the full 644 — the AF3
hexamer prediction `ftsh_hexamer_af3server.json` was not used in these builds).

**This does NOT clear the proteolysis objection** — no ATPase ring, no protease domain, so any
question about proteolysis/substrate engagement/ATPase-driven dynamics is still a non-starter.
User's call (Aug 5): "1-120 is enough" for the dome-opening question, which is not directly
compromised by the FtsH gap. Fine to proceed on that basis.

| system | CHARMM-GUI job | atoms |
|---|---|---|
| `full-model` | `8553087068` | 1,916,043 |
| `full-bact` | `8553086741` | 1,809,634 |

Lipids as-built: `full-model` DPPE 72.2/POPG 12.9/DOPG 12.9/LOAC 1.0/TLCL 1.0; `full-bact` POPG
37.0/DOPG 37.0/DPPE 6.0/LOAC 10.0/TLCL 10.0.

⚠️ **Both carry a stray 37th protein segment `PROI`** — one free-floating capped LEU 9 (22 atoms,
build artifact). Harmless energetically but breaks any "36 segments" assumption and appears in
`protein` selections.

**FtsH segment naming in these PSFs — corrected Sep 22, 2026, previous version below was wrong.**
Verified directly against both PSFs (`full-model`/`full-bact` are byte-identical in segid↔resid
scheme, confirmed by diffing every segment): CHARMM-GUI's `PRO*`/`PRA*` naming does **not** map to
the older `Y,Z,0-9` scheme, and — the actual error — does **not** put all 12 FtsH segments under
`PRAA`–`PRAJ`/`PROY`/`PROZ` either. The real mapping (resid 1–120 = FtsH in this rebuild):
- **FtsH (12 segs, resid 1–120)**: `PROA, PROB, PROD, PROE, PROG, PROH, PROK, PROM, PRON, PROP, PROQ, PROR`
- **Dome HflK (12 segs, resid 79–419)**: `PRAB, PRAD, PRAF, PRAH, PRAK, PROC, PROJ, PROO, PROT, PROV, PROX, PROZ`
- **Dome HflC (12 segs, resid 1–329)**: `PRAA, PRAC, PRAE, PRAG, PRAI, PRAJ, PROF, PROL, PROS, PROU, PROW, PROY`
- **Stray**: `PROI` (the 1-residue LEU artifact, see above)

**Critical gotcha**: `PROA`–`PROX` in `full-model`/`full-bact` is a totally different letter→chain
mapping than the same-looking `PROA`–`PROX` in `dome-model`/`dome-bact` (where `PROA`-`PROX` is a
clean 24-segment alternating-HflK/HflC scheme with no FtsH involved at all — see the segname table
near the top of this file). **The two families are not interchangeable** — `PROA` is an HflK dome
subunit in `dome-model`/`dome-bact` but an FtsH fragment in `full-model`/`full-bact`. Any
cross-system script (e.g. ring-adjacency/opening-distance analysis) must select dome chains **by
resid range** (79–419 or 1–329, excluding `PROI`/`IONS`/`MEMB`/`TIP3`/FtsH's 1–120 range), never by
a hardcoded segid list, if it's meant to run uniformly across both families. `dome-bact` confirmed
identical to `dome-model`'s scheme; `full-bact` confirmed identical to `full-model`'s — only two
distinct schemes exist across all 4 protein-bearing systems, not four.

Previous `full-bact` build (40 ns production + GaMD, FtsH 31-97) is **archived, not deleted**, at
`full-bact/superseded_ftsh31-97/{namd,gamd}/`.

**Two real equilibration bugs found and fixed Aug 8-9, both worth knowing if these are ever rebuilt
again:**
1. **Missing/stale `step5_assembly.str`.** `full-model` never got this file uploaded at all (only
   `namd/` was copied from the CHARMM-GUI download, not the parent dir) — instant `FATAL ERROR`.
   `full-bact` had one, but it was a **Jul 15 leftover from the superseded 31-97 build**, not the
   Aug 5 rebuild — box dimensions differ by several Å (A: 308.3→306.2, C: 201.2→205.8). Fixed by
   copying the correct file from each system's own `~/Downloads/charmm-gui-*/step5_assembly.str`.
2. **Investigated whether the box was actually too small to contain the protein** (it looked that
   way from percentiles alone: protein top reaches +144 Å above the membrane, water box only
   extends to +104 Å) — **but the quantitative check (periodic-wrap the overflow atoms, measure
   distance to the nearest real protein/lipid atom) found zero clashes within 8 Å even at the worst
   point.** The dome's overflow wraps into open bulk water on the far side, not into itself. **No
   rebuild was needed** — don't assume "exceeds the declared box" means broken without checking
   what's actually on the other side of the wrap first.

---

## Martini 3 coarse-grained comparison — `dome-model` restraint-scheme sweep

**Purpose**: speed sanity-check on CG dynamics (does dome opening happen at all in Martini?),
complementary to the primary AA path, not a replacement. Lipid specificity is lost at CG
resolution, so this can rule out "doesn't open in any lipid environment" but can't answer the
mechanistic which-lipids-drive-opening question. **AA remains the primary evidence.**

**CHARMM-GUI's Martini Bilayer Maker cannot build this system** — its internal AA→CG conversion
writes a PDB that overflows the 5-digit atom-serial field above 99,999 atoms (this system's AA
input is ~1.7M atoms). The pipeline below was hand-built instead (`martinize2` + `insane`) and
is the reusable recipe for any future system needing Martini CG conversion.

### Reusable build recipe

1. Get per-chain protein PDBs — CHARMM-GUI's GROMACS FF-Converter (a different, working tool)
   writes one PDB per segment automatically, ~5,300 atoms each, safely under the format limit.
2. Docker environment (avoids cluster/local pip conflicts):
   `FROM continuumio/miniconda3` + `pip install polyply vermouth` + `pip install "git+https://github.com/Tsjerk/Insane.git"`
3. Convert each chain separately: `martinize2 -f chain.pdb -o chain.top -x chain_cg.pdb -name chain_X -ff martini3001 -p backbone [-elastic -ef N] [-ss <string>] -maxwarn 100`.
   **Must set `-w` (container workdir) to the output folder** — `martinize2` writes `.itp` relative
   to CWD, not to `-o`/`-x`'s path.
4. Concatenate the CG chain PDBs directly — `martinize2` preserves the original coordinate frame,
   no re-superposition needed.
5. Lipid parameters from `Martini-Force-Field-Initiative/M3-Lipid-Parameters` on GitHub (`ITPs/`),
   NOT the generic `marrink-lab/martini-forcefields` repo (only 3 lipid types). Need core +
   `ffbonded_v2` (easy to forget — defines bonded macros lipids reference) + per-headgroup files +
   solvents + ions.
6. Missing lipid types: check `insane`'s `lipids.dat` for `M3.<NAME>` before assuming support.
   `DPPE` and cardiolipin (`TOCL`) both needed custom shape-template entries in `custom_lipids.dat`
   (real Martini 3 bead names/charges, not Martini-2-era stand-ins) — done, see repo's
   `custom_lipids.dat`. Verified `LOACL1` = tetraoleoyl cardiolipin (exact `TOCL` match); `TLCL1` =
   tetralinoleoyl (18:2, no Martini 3 template exists, `TOCL` is the closest approximation, used
   for both per project decision).
7. Build: `insane -f protein.gro -o system.gro -p system.top -dat custom_lipids.dat -pbc rectangular -x/-y/-z <nm> -l DPPE:70 -l POPG:12.5 -l DOPG:12.5 -l TOCL:5 -sol W -salt 0.15 -ff M3 -fudge 0.9`.
   Box dims from the AA system's equilibrated `.xsc` (Å→nm). **`-fudge 0.9` is this system's tuned
   value** (default 0.1 leaves a 147 nm² void under the dome from this system's sparse/wobbly M3
   stalk footprint) — treat as system-specific, not universal.
8. Manually replace `insane`'s placeholder `Protein 1` topology line with `#include`s for all 24
   chain `.itp`s + `chain_X_0 1` molecule entries, in concatenation order.
9. `gmx grompp` before trusting anything — zero ERRORs means the topology is internally consistent.
10. Run on a compute node via `sbatch`, never the login node (`mdrun` segfaults there).

Files at `/scratch/beagle3/junseo/martini-dome-cg/` (local mirror `~/Downloads/charmm-gui-8458758786/`).
`em.mdp`/`eq.mdp`/`md.mdp` verified against the official Martini 3 tutorial (cgmartini.nl, KALP
peptide), not written from general knowledge: reaction-field electrostatics (`epsilon_r=15`,
`epsilon_rf=0`), 1.1 nm cutoffs, semi-isotropic `c-rescale`→`parrinello-rahman` barostat, separate
`Protein_Membrane`/`W_ION` thermostat groups, 20 fs production timestep. Confirmed
**2,116 ns/day at 32 threads/2 GPU** (final best config; internally and externally corroborated,
not a fluke — see `progress_log.md` archive for the verification).

### Selection gotchas (Martini CG, all variants)
- `martinize2` renumbers every chain from 1 (discards AA numbering). Offset per chain = real AA
  start resid − 1 (e.g. HflK chains: AA 79–419 → CG 1–341, offset 78).
- `insane` writes ions under **resname `ION`**, species distinguished only by atom name (`name NA`/`name CL`).
- Lipid headgroup phosphate-only: `name PO4 PO41 PO42`. Full headgroup needs per-lipid-class splits.
- VMD's `protein`/STRIDE macros don't work on CG beads (no atom named `CA`/`N`/`C` in non-Go
  builds — `BB`/`SC1` instead). Use `not resname DPPE POPG DOPG TOCL W NA CL`. For New Cartoon,
  transfer secondary structure from AA per-chain PDBs via STRIDE + residue-offset mapping
  (`~/Downloads/charmm-gui-8458758786/transfer_secondary_structure.tcl`).
- Go-variant virtual sites are named `CA` (8,040 of them, sit exactly on `BB` beads) — any protein
  selection on Go variants needs `and not name CA` or every backbone bead renders twice.
- `-DPOSRES` is a no-op with `martinize2 -go` unless `-p backbone` was also passed.
- `grompp` on Go variants takes ~1h (66M-entry nonbonded matrix, one atomtype per residue) — budget
  wall time. Contact-map generation needs ~200 GB, run on `beagle3-bigmem`.

### Restraint-scheme sweep — where the comparison against CHARMM-GUI landed

**Compared our mdp/martinize2 parameters directly against CHARMM-GUI's official Martini output**
(charmm-gui-8542787498 membrane-only, -8579367020 1AFO, -8586651827 2ZXE — confirmed the protocol
is not protein-specific, only adds a POSRES ramp + thermostat group). Result: **all non-bonded
parameters and production-phase physics already matched exactly.** The one consequential
difference: **we never ran `-dssp`/STRIDE to assign secondary structure**, so `martinize2` labeled
every one of our 24 chains all-coil, and Martini 3 never emitted the helix/sheet-dependent bonded
terms real secondary structure would produce. We compensated with an elastic network (springs
between nearby beads) instead — which holds the fold together but has no idea what's a helix vs a
loop. Minor differences: CHARMM-GUI's 5-stage equilibration ladder (dt 0.002→0.020 ps over 4.75 ns,
restraints ramped down) vs our single 1 ns stage; and our `eq.mdp` used all-atom water
compressibility (4.5e-5) instead of Martini's 3e-4.

**Variants built, basis for comparison: AA `CA` atoms vs CG `BB` beads, 8,040 each, 0–32 ns window
(the AA reference's span)** — AA dome-model contracts 79.65→76.19 Å (ΔRg_xy −3.40) too, so CG
contraction is real physics, not a restraint artifact:

| variant | design | ΔRg_xy | ΔRg_z | RMSD | note |
|---|---|---|---|---|---|
| **AA dome-model** (ref) | CHARMM36m, no bias | **−3.40** | **+1.72** | 8.74 | ground truth |
| v1 elastic | ef 700, no inter-chain | −1.70 | −1.54 ✗ | 16.48 | invalid — chains slide, do not use |
| v2 flat-bottom | elastic + 5,015 inter-chain | −1.90 | −0.94 ✗ | 13.17 | best ring width, but EM ran with wrong electrostatics (below) |
| v3 Go | 10,612 intra + 4,663 inter contacts | −0.14 | +0.50 ✓ | 11.27 | pre-collapsed at production start, comparison invalid |
| v4 Go intra-only | v3, inter-chain deleted | −0.76 | +0.85 ✓ | 21.27 | worst RMSD of all — pre-collapsed too |
| v5 Go weak | v3, ε 9.414→5.0 | −1.09 | +1.22 ✓ | 14.93 | pre-collapsed too |
| v6 elastic ef300 | v2, ef 700→300 | −1.33 | −1.60 ✗ | 20.34 | softening made every metric worse |
| v7 elastic ef1500 | v2 topology, ef 700→1500, corrected EM | pending analysis | | | |
| v8 elastic ef3000 | v2 topology, ef 700→3000, corrected EM | pending analysis | | | |
| v9 elastic ef700 | v2 topology, corrected EM only | pending analysis | | measures how much the EM bug mattered |
| v10 no elastic, real SS | CHARMM-GUI method exactly (STRIDE, no springs, staged ladder) | **+1.93** ✗✗ | −1.25 ✗ | **16.51** | ring EXPANDS (wrong sign, not just wrong magnitude) — worst shape-error of any variant |
| v11 elastic + real SS | v10 + elastic ef 700 | +0.29 | **+1.19** ✓ | **22.45** | worst RMSD of all 11 variants; only variant to get Rg_z sign right |
| v12 elastic ef1000, real SS | v11, ef 700→1000 | not computed via this table's metric | | | **best variant so far** — longest clean run of the whole sweep (2382 ns), closest ΔRg_z sign/magnitude match to AA among elastic variants. Missing from this table until Sep 2026 (real data existed in `trajectories/martini_sweep/v12/`, just never written down here) |
| v13 elastic ef1500, real SS | v12, ef 1000→1500 | — | | | **crashed** via LINCS constraint failure at ~2107 ns. Also missing from this table until Sep 2026 |

**v2's EM bug**: confirmed from run logs that v2 alone minimized with `coulombtype=PME`,
`epsilon_r=1` (should be reaction-field, ε_r=15 like every other variant — a file that was never
updated when the others were fixed). Electrostatics ~15× too strong on an anionic-lipid membrane.
This means every "v2 is best" conclusion above rests on a bad starting structure, and neither the
v1→v2 nor v6→v2 "more restraint helps" comparisons are clean (both cross the EM change). v9 retests
v2's exact topology with corrected EM to measure the damage.

**v10/v11 ANSWERED (read out Aug 10) — real secondary structure does NOT fix the pre-collapse
problem.** Both start their production window already contracted (Rg_xy0 76.94/77.07 vs AA's
79.65) — the exact same pre-equilibration-collapse failure mode that invalidated the Go family
(v3/v4/v5). This was the actual thing being tested; the answer is that supplying real secondary
structure alone does not prevent it. Some other factor in the CG system (most likely the CG
membrane/lipid parameters, per the earlier `TLCL1`→`TOCL` substitution note) is driving the
contraction regardless of how the protein is restrained.

Within that caveat, v10 (no elastic) vs v11 (elastic ef700) is a genuine mixed result, not a clean
winner: v10 has the lower RMSD (16.51 vs 22.45 — drifts less from its own start) but its ring
**expands** in the wrong direction entirely (ΔRg_xy +1.93 vs AA's −3.40); v11 barely moves in the
ring plane (+0.29, close to flat) and is the only variant of all 11 to get the *vertical* direction
right (ΔRg_z +1.19, same sign as AA's +1.72), at the cost of the highest RMSD of any variant tested.
v10's RMSD plateaus after ~8 ns; v11's keeps climbing through the full 32 ns window, unconverged.
**Neither variant's AA-comparison should be treated as clean** given the shared pre-collapse issue —
same caveat as the Go family.

**v12/v13 (elastic-stiffness follow-up) and v14-16 (timestep-sensitivity, separate axis) — table gap
found and corrected Sep 2026.** v12 (`ef1000`) is the best variant of the whole sweep so far by this
project's own metrics; v13 (`ef1500`) crashed. The subsequent pivot to v14/v15/v16 tests timestep
sensitivity, a different question than v12/v13's stiffness-tuning — **not** a sign v12 was rejected
or that v14-16 are "trying to beat" it. `trajectories/load_v2_v10_v11_v12_full.tcl` gives a 4-way
full-trajectory visual comparison (v2/v10/v11/v12).

**Third comparison arm added Aug 6 — a pure-lipid (no protein) CHARMM-GUI Martini build**
(`charmm-gui-8542787498`, `~/Downloads/`, confirmed via `system.top`: DPPE/POPG/DOPG + water/ions,
zero protein `#include`). This triangulates the earlier finding: the pure-lipid build matches the
protein-containing 2ZXE build on **every** physics parameter at every stage — the only differences
being the things a protein mechanically requires (`POSRES` ramp, one thermostat group). Confirms
the gap to our pipeline isn't "CHARMM-GUI treats proteins specially," it's specifically that we
skip the secondary-structure step and the staged ladder, independent of protein content. Full
three-way parameter table (protein+lipid / ours / pure-lipid) built as an artifact this session —
regenerate on request rather than relying on a URL here, since artifact links aren't guaranteed to
survive across sessions (this one didn't: the first published copy became unwritable mid-session).

**Restraint-mechanism deep dive (Aug 6)** — the two restraint types are not just different force
constants, they're different mechanisms, and they come from different places:
- **Protein `POSRES`**: isotropic 3D lock (`fcx=fcy=fcz=POSRES_FC`), **backbone (`BB`) beads only** —
  verified directly: 992 of 2,245 atoms in 2ZXE chain A are restrained, all `BB`, zero side chains.
  Comes from `martinize2 -p backbone` **itself** — confirmed empirically, since our own v10 topology
  (plain `martinize2 -p backbone`, no CHARMM-GUI involved) produces the byte-identical block. This
  is a Martini-tooling convention (vermouth), not a CHARMM-GUI addition.
- **Lipid `BILAYER_LIPIDHEAD_FC`**: z-only (`fcx=0, fcy=0, fcz=BILAYER_LIPIDHEAD_FC`), one bead per
  molecule (the headgroup phosphate) — deliberately leaves lateral diffusion untouched, since that's
  the membrane's defining physical behavior. **This one IS a CHARMM-GUI addition, not a community
  Martini file feature** — diffed CHARMM-GUI's bundled `martini_v3.0.0_phospholipids_v1.itp` against
  an independent GitHub copy of the identical file: CHARMM-GUI's version has ~50 extra lines
  (`BILAYER_LIPIDHEAD_FC`, `MICELLE_LIPIDHEAD_FC`, `VESICLE_LIPIDTAIL_R` restraint blocks) that
  simply do not exist upstream.
- **Practical gotcha, confirmed in both CHARMM-GUI reference builds**: the restraint block only
  survives in that legacy `_v1` file and the sterols file — the current `_PE_v2.itp`/`_PG_v2.itp`
  files CHARMM-GUI actually `#include`s for PE/PG lipids carry **no** `[position_restraints]` block
  at all. So `-DBILAYER_LIPIDHEAD_FC` is a **no-op in CHARMM-GUI's own output too**, for the exact
  lipid classes our systems use — not just a gap unique to our pipeline as earlier phrasing implied.

Local trajectory copies (gitignored, cluster remains authoritative) now include **all 11 variants**,
each with its own correct per-variant topology (not shared/borrowed — see the load-script note
below) at `trajectories/martini/{v1_elastic,v2_flatbottom,v3_go}/` and
`trajectories/martini_sweep/{v4..v11}/`. Three tracked load scripts (`trajectories/*.tcl`, exempted
from `.gitignore`'s blanket `trajectories/*` rule):
- `load_v1_v6.tcl` — v1-v6, `WINDOW_NS` selects 0-32/0-50/full, handles the two-topology split
- `load_v2_v10_v11.tcl` — the v2/v10/v11 three-way comparison
- `load_all_martini.tcl` — all 11 at once, 0-32 ns matched window, hidden except v2/v10/v11 by default

**Bug found and fixed while building these (Aug 10)**: an earlier version had v11's elastic bonds
drawn from **v6's** topology file via `cg_bonds`. Wrong — v6 (all-coil/ef300) and v11 (real-SS/ef700)
have completely different bonded chemistry; that would have rendered the wrong bond network, not
just failed. Every variant now draws `cg_bonds` from its own `.top`, verified headless before commit.
Separately, v7/v8/v9's local `.xtc` files were found truncated (leftovers from an earlier failed
parallel-scp attempt) and re-downloaded/verified byte-identical to the cluster copies.

**Gotcha: VMD's RMSD Visualizer Tool (GUI) doesn't work on Martini systems.** It ANDs whatever
selection you type with a hardcoded all-atom backbone filter (`name C CA N O`), which matches zero
Martini beads (`BB`/`SC1`/...) — every selection fails identically, including `protein` and `all`.
Either find and disable its "Backbone" toggle, or skip the GUI and use `measure rmsd` directly in
the Tk Console (no fit/superposition by default — matches how the RMSD numbers above were computed).

---

## GaMD — status and operational rules

**Reality check**: GaMD's 22.5M-step (45 ns) schedule is *equilibration* (7.5M cMD + 15M
boost-equilibration) — production GaMD sampling only begins after that completes. Check `E`/`k` in
the `.gamd` file: `E=k=0` means still in the cMD phase, i.e. plain conventional MD, not GaMD data
yet, however long the DCD is.

**All 5 systems now have GaMD running** — see the Current Systems status snapshot above for live
progress. `full-model`/`full-bact` started later than the other three: production crossed the 20 ns
conventional-MD threshold well before GaMD itself got set up (job 57826600/57826601, Sep 4), branched
from each system's own `step7_21.restart` (~21 ns), same protocol as the other three. All 5 now run
uniformly on 2 GPU/16 PE resident mode -- `control` briefly ran its plain (non-GaMD) production on an
unjustified 4 GPU/offload config, found and fixed Sep 7 (see the Production config section above);
that was never true of GaMD specifically, which was 2 GPU from the start.

**GPU-resident GaMD: the Aug 3-5 corruption bug is FIXED as of Sep 3-4 — no longer rejected,
migration decision pending.** Original finding (job 52975499, Dr. Chen's older
`haochuan/gpu_accelmd_2` branch): resident mode **corrupted the GaMD boost statistics** on restart
— DIHED `Vmin` collapsed to exactly 0, `sigmaV` inflated ~4,500×, on the very first statistics
update after a restart, while `ENERGY:` output matched offload to 0.008% (so a smoke test checking
only energies wouldn't catch it). Reported to Dr. Chen; he pointed to commit `cc69db49` ("force
computeEnergies to 1 when aMD/GaMD is enabled") on NAMD's `main` branch as the fix.

**Rebuilt and re-validated (Sep 3-4)**: pulled `main` via a new SSH deploy key (the old HTTPS clone
had no cached credentials — GitLab's private-repo access needs a **fine-grained** PAT with
`Code: Download` permission, not a classic token, for this repo). Built into
`/scratch/beagle3/junseo/namd-main-build/Linux-x86_64-g++/namd3` (git worktree off the same clone,
Charm++/tcl/fftw symlinked from the original build — reused, not rebuilt). Reran the identical
validation (`dome-bact/gamd_resident_val_mainbranch/`, same restart point/step range as the
original). Fixed: TOTAL `Vmin` −5.06679e6 matches offload exactly; DIHED `Vmin` 223,257 vs.
offload's 223,155; `sigmaV` within ~0.5-7% of offload (was ~4,500-6,200× inflated on the old
branch). Performance: **7.21 ns/day** vs. offload's ~2.77 ns/day (2 GPU) — still ~2.6×, down from
the old (buggy) build's 8.22× since the fix computes energies every step.

**Not yet migrated** — control/dome-model/dome-bact's live GaMD runs are all still on offload. Chen
confirmed his older `haochuan/gpu_accelmd_2` branch still has a separate pending bug in stochastic
velocity rescaling (irrelevant here — this project's configs use `langevin on`, not stochastic
velocity rescaling). Old build (`namd-chen-gpuresident/`, branch `haochuan/gpu_accelmd_2`) stays
useful for **conventional** (non-GaMD) resident-mode MD only — `share_gamd_resident/` (repo root)
has a verified-working reference config for that use case (`fullElectFrequency 1`, `wrapWater
on`/`wrapAll on`, `pairlistdist 16.0`). For GaMD specifically, use the new
`namd-main-build/Linux-x86_64-g++/namd3` if/when migrating — always invoke by full path, never bare
`namd3`.

**Real data loss found Aug 8 — Slurm silently requeues preempted jobs under the same ID, and the
raw single-shot GaMD `.inp` scripts have no resume logic.** The Aug 6 maintenance window preempted
`control`'s and `dome-bact`'s GaMD segment-2 jobs; Slurm's default `Requeue=1` restarted them under
the *same job ID*, and since `gamd-equilN.inp` has a fixed `firsttimestep` pointing at the segment's
original start (not a self-updating checkpoint), NAMD re-ran the entire segment from scratch,
**overwriting** the DCD in place. Confirmed via the DCD header, not just logs (`NSET`/`ISTART` fields
showed only the post-restart frames existed on disk): **`control` lost ~12.76 ns, `dome-bact` lost
~5.54 ns** of already-completed segment-2 progress. Not corrupted physics — a valid restart from a
valid checkpoint — just wasted wall-clock.

**Fix applied to all NAMD/GaMD submit scripts (`--no-requeue` in every sbatch, plus
`scontrol update JobId=X Requeue=0` on anything already running)** — a future preemption now kills
the job cleanly instead of silently overwriting progress, surfacing it as an obviously-dead job for
the normal `make_gamd_restart.py` workflow instead. `run_prod_gpu.sh`-driven NAMD production was
*not* affected — it self-heals by finding the latest completed 1 ns block on restart (confirmed:
`control-prod`'s `step7_105`→`106` sequence was continuous straight through the same maintenance
window) — but the fix was applied there too for a cleaner failure mode regardless.

### Dr. Haddadian's 3-part convergence check (completed Sep 16-17 for control/dome-model/dome-bact)

Check: (1) ΔV vs. time stable/no drift, (2) ΔV distribution ~Gaussian, (3) σΔV ≤ 10kT (=6.0242
kcal/mol at 303.15K) for reliable cumulant-expansion reweighting. **Method**: concatenate only the
*final/frozen* equilibration regime (E is recomputed periodically during equilibration — pooling
all regimes gives a meaningless bimodal distribution) with all production.

**Results**: all 3 systems PASS checks 1-2 (stable, close-to-Gaussian, low anharmonicity γ =
0.008-0.019) but **FAIL check 3** — σΔV is 4.4-11× over the 10kT threshold (control 66.63,
dome-model 26.39, dome-bact 27.40 kcal/mol). **Simulations are fine; this is a reweighting-
reliability caveat**, not a simulation defect — standard 2nd-order cumulant-expansion reweighting
is not automatically trustworthy on these trajectories as-is. Not yet resolved: an empirical
reweighting test (real coordinate, `PyReweighting`, check 2nd-order vs. exact-exponential-average
agreement) has not been run — the 10kT check only shows the safety margin is gone, not that
reweighting is confirmed to fail. `σ₀` in the field's own formula is literally this project's
`accelMDGsigma0P/D` (=6.0, chosen to approximate 10kT already) — the 4-11× overshoot beyond that
own calibration target, worse for `control` (165 ns combined) than the dome systems (35-49 ns),
suggests boost may grow beyond what a short calibration window anticipates over a long run; not yet
confirmed as causal. **The sigma0-tuning question is open** — an earlier claim here that sigma0=4
vs 6 gave "nearly identical" stats was retracted Sep 18 (that test actually failed, never produced
a real comparison). See the PI-requested sigma0P=4.0/D=6.0 full-length experiment and the
`sigma0P=2.0/D=6.0` asymmetric test above for the real tests of this, once complete. Full writeup
in `progress_log.md` (Sep 16-17 entry + Sep 18 correction). Script:
`scripts/analysis/gamd_convergence_full.R`; outputs in `analysis/gamd_convergence/`.

**General gotcha found via this analysis, applies to any future log-concatenation-across-restarts
work**: NAMD job restarts (both equilibration-regime transitions and production-segment restarts)
can produce a duplicate or anomalous log line for the exact boundary step — the boost hasn't
re-engaged yet when that line is written. Symptom: the same absolute step logged twice with
substantially disagreeing values (confirmed real case: same step, 3733 vs. 2540 kcal/mol — the two
values can't both be the same trajectory frame). Fix: after concatenating, deduplicate by step,
keeping whichever duplicate is consistent with its immediate neighbors.

### `make_gamd_restart.py` — run after any GaMD job stops

`/scratch/beagle3/junseo/make_gamd_restart.py control dome-bact dome-model`

Generates the next segment (`gamd-equil`→`-equil2`→`-equil3`...) and enforces the three restart
rules that have each been gotten wrong here before:
- **new `outputName`** every segment (refuses if the target `.dcd` already exists — these are
  4.8–11.5 GB, overwriting one is a real loss)
- **`accelMDGRestart on` together with `accelMDGRestartFile`** — never one without the other
- **`firsttimestep`** = true absolute step, read from `.restart.xsc` column 1 (**not** the `.gamd`
  file's `Vn` field — that's samples in the *current* 1.5M-step statistics window, not absolute)
- asserts `firsttimestep + run == 22,500,000`, writes nothing if that fails
- **refuses to run while the job is still live** (`.restart.xsc` is being rewritten continuously)
- Beagle3 login nodes run **python 3.6** — no `subprocess.run(capture_output=/text=)` kwargs

---

## Cluster operations — standing gotchas

- **`beagle3-0006` is a bad node.** Kills jobs in 1–2 s, zero output files, `Reason=None`, reports
  `STATE=MIXED`. Must be in `--exclude` on every sbatch/GaMD `.sh` script —
  **check both**: `grep -L 'beagle3-0006' */namd/*.sbatch */gamd/*.sh` (an earlier audit that
  globbed only `*.sbatch` missed the GaMD `*.sh` scripts entirely and let this drift back in).
- **CPU-only jobs must not go to the GPU partition** — use `--partition=beagle3-bigmem` (4 nodes,
  512 GB, no GPUs, usually idle) for `martinize2`/`trjconv`/`grompp`-only jobs.
- **Always pin `--constraint=a100`** — one script missing it is enough to land on an A40 silently.
- **`COMPLETED`/exit 0 is not proof of success.** Seen repeatedly: crashed-on-import jobs, a dead
  SSH socket read as "no jobs running," a genuinely-completed job whose result was still garbage.
  Check for real output files and (for anything with a walltime budget) the job's **elapsed time**
  vs its limit — a job that used 30.6 of 36 h "succeeded" but had almost no margin; the next-larger
  system on the same script needed more wall time, not the same amount.
- **Editing an sbatch file does NOT disturb a running job** — Slurm spools its own copy at
  submission. (Different from editing a *helper script* a live bash process is still reading —
  that can corrupt the in-flight process; see `progress_log.md` for the incident.)
- **Write sbatch scripts locally and `scp` them — never heredoc over ssh.** A `\$` escaping fault
  killed 3 jobs this way (`$SLURM_SUBMIT_DIR` written literally).
- **Beagle3's GROMACS binary is `gmx_mpi`, not `gmx`** (`module load gromacs/2025.3` first) —
  applies to `trjconv`/`grompp`/`check`, not just `mdrun`. Always use `gromacs/2025.3`, not the
  default `2022.4` (a PLUMED-patched build that segfaults on Martini virtual-site construction).
- **`-deffnm` names outputs, not the tpr** — `grompp -o md_v.tpr` then `mdrun -deffnm prod_v` gives
  trajectory `prod_v.xtc` but tpr `md_v.tpr`. List the directory, don't infer from `-deffnm`.
- **macOS BSD tools differ from GNU**: `rsync` has no `--info=progress2` (use `--progress`; exit 23
  with `fchmodat Operation not permitted` is a harmless permission warning, not a failed
  transfer); `sed` has no `\b` word-boundary (verify a `sed` actually changed the file before
  trusting it — one silently no-op'd and the unfixed file got submitted anyway).
- **Concurrent transfers to one host share the multiplexed SSH connection** and throttle each
  other — transfer sequentially. **A parallel attempt that gets killed/timed out leaves silently
  truncated files, not missing ones** — v7/v8/v9's local `.xtc` copies sat truncated (1-13 MB
  instead of ~24 MB) for days after a failed parallel download, undetected until a later `mol
  addfile` returned the wrong frame count. Always verify byte size against the remote after any
  transfer that got interrupted, not just check the file exists.
- **Foreground `scp`/`ssh` can be much slower than expected for no obvious reason** (seen repeatedly
  this project: same file, same connection, 10x+ speed variance session to session). Don't assume a
  slow transfer is broken — measure the live rate (`stat` the local file twice a few seconds apart)
  before concluding something's wrong, and prefer background/`run_in_background` for anything that
  might exceed the foreground tool timeout rather than let it die mid-transfer.
- **Production jobs going idle (not crashing) is the recurring failure mode.** Jobs exit 0 cleanly
  at their chunk/wall-time cap and nothing auto-resubmits. Check `squeue` every session against
  the Current Systems table.
- **Beagle3 and Midway3 are two login-node names into ONE shared SLURM queue, not separate
  clusters** (confirmed Sep 17: `squeue` from either host shows identical job IDs/states). Jobs
  stuck `PENDING` on a per-user QOS cap (currently 16 GPU/user on the `gpu` QOS) cannot be routed
  around by submitting from the other host — same queue, same limit. (Filesystem is also shared:
  `/scratch/beagle3` is GPFS-mounted on Midway3.)
- **A "safety-net" recovery `rsync` that excludes `.coor`/`.vel` (to avoid re-pulling large files)
  can leave a restart checkpoint silently incomplete** — found Sep 18: `dome-bact-prod` failed
  instantly (`Unable to open extended system file`) because its latest restart had `.xsc` but no
  `.coor`/`.vel`, from exactly this kind of exclusion during the Sep 16-17 `rm -rf` recovery.
  `run_prod_gpu.sh`'s self-heal correctly ignores incomplete/malformed checkpoints but has nothing
  to fall back to if the truly-latest one is incomplete. After any recovery that excludes large
  files by pattern, explicitly verify the actual latest restart set has all of `.coor`/`.vel`/`.xsc`
  (and `.gamd` for GaMD) present, don't assume the exclusion was safe.
- **Never `rm -rf` a whole `namd/`/`gamd/` directory**, even right after archiving/backing it up —
  a file-count-only verification can still miss that operational files (restart checkpoint,
  `cumulative_ns.txt`, toppar, sbatch scripts) got swept up with the intended bulk `.dcd` archival
  target. Only ever delete `.dcd` files via targeted `find ... -delete`.

---

## Local trajectory copies — `trajectories/`

Gitignored working copies for VMD/analysis. Cluster (`/scratch/beagle3/junseo/`) remains
authoritative. **Verify against the cluster before assuming these are current** — this list is a
snapshot, not live-synced.

```
trajectories/
├── README.md                  ← VMD load commands, selection strings, gotchas — READ FIRST
├── load_v1_v6.tcl             ← v1-v6, WINDOW_NS selects 0-32/0-50/full
├── load_v2_v10_v11.tcl        ← v2/v10/v11 three-way comparison, correct per-variant cg_bonds
├── load_all_martini.tcl       ← all 11 variants, 0-32 ns matched, hidden except v2/v10/v11 by default
├── namd/                      all-atom (CHARMM36m)
│   ├── dome-bact/   step7_1-93 (93 ns, caught up Aug 10) + step6.1-6.6 equilibration
│   ├── full-bact/   eq + 20 ns   (cluster ahead — check squeue)
│   └── full-model/  37 ns, production only (superseded build — full-model was rebuilt Aug 5,
│                    this local copy predates the rebuild)
├── martini/                   v1_elastic, v2_flatbottom, v3_go (full-length trajectories)
├── martini_sweep/             v4-v11, all complete with own topology (0-32 ns for v6-v11)
├── namd/stride_by_segment.tcl ← run this before New Cartoon on any all-atom system: VMD's
│                                 built-in STRIDE fails silently above 99,999 protein atoms
│                                 (writes malformed temp PDB), leaving everything coil. All-atom
│                                 systems here (126,696+ protein atoms) all hit this.
└── namd/sscache_by_segment.tcl ← per-frame SS caching for scrubbing a trajectory (SS may
                                  genuinely change over time, e.g. the coiled-coil near the
                                  opening). Source stride_by_segment.tcl FIRST, then this, then
                                  `start_sscache`. First pass ~0.8 s/frame (computes + caches),
                                  revisits are ~30 ms (cache hit). Patched from the standard
                                  VMD sscache.tcl, which otherwise calls the same whole-molecule
                                  STRIDE path that fails on this system.
```

**All-atom selections**: `protein`; lipids `resname DPPE POPG DOPG LOACL1 TLCL1` (cardiolipin is
`LOACL1`/`TLCL1` here, NOT `TOCL` — that's the Martini CG name); FtsH-only needs the current
build's actual segnames (see FtsH section above, verify don't assume).

**Loading NAMD DCDs**: use a `for` loop over `step7_$i.dcd`, never a glob — lexical sort gives
`step7_1, step7_10, step7_11, …, step7_2`, scrambling time order. Add `step 5` (or similar) to
`mol addfile` if loading the full trajectory would exceed available RAM (~17 GB for 800 frames on
a 1.77M-atom system) — check `sysctl -n hw.memsize` vs frame count × atom count × 12 bytes first.

## Analysis Scripts
Rajiv's full analysis scripts: `/project2/haddadian/rajiv/analysis` (requires `pi-haddadian` group,
already set up; access it via `ssh beagle3` directly first — it sometimes works despite the
`/project2` unreliability warning above, fall back to `ssh midway2` only if it doesn't). Known issue:
wrapping artifacts break center-of-mass calcs — unwrap the trajectory first. ~480 files in there,
mostly one-off/dated outputs — grep by purpose rather than browse. Local copy of the one pulled so
far: `scripts/analysis/rajiv_lipid_density.py` (2D XY histogram of one lipid species' phosphate
positions, `plt.imshow` heatmap, colorbar = "average lipid count per bin" — hardcoded to one system,
edit the `psf_file`/`dcd_file`/`lipid_sel` constants at the top before reuse). Not the same as
`thickness-map.py` (same directory) — that one maps bilayer thickness, not lipid count.

GaMD convergence-check analysis (Dr. Haddadian's 3-part check, see GaMD section above):
`scripts/analysis/gamd_convergence_full.R` (also `gamd_convergence_extract.sh`,
`gamd_convergence_anharmonicity.R`, and the `_ORIGINAL_juliana` unmodified copies they were adapted
from), outputs in `analysis/gamd_convergence/`.

`control` system analysis (thickness/curvature/order-parameter/area-per-lipid) lives in
`analysis/control/<Nns>/<script>/`. The Voronoi APL script (code on Midway3 only, repo tracks just
`.npy`/`.png` outputs) should be **reused unchanged for the other 4 systems**, not reimplemented
per-system, for a fair comparison. `control` 35 ns result: combined 54.35 Ų (DPPE 52.93, POPG
54.60, DOPG 56.34, LOACL1 71.49, TLCL1 73.27).

**Dome-opening-distance** (Dr. Haddadian's request — COM distance between adjacent membrane-embedded
helices, generalized to track all 24 ring-adjacent chain pairs since the opening can move):
`scripts/analysis/opening_distance.py`, runs on `dome-model`/`dome-bact`/`full-model`/`full-bact`
(not `control`/`control-bact`, no protein). Selects dome chains **by resid range** (not segid — see
the segid-scheme caveat above, this makes the script naming-family-agnostic) and derives true ring
adjacency via median-COM-distance nearest-neighbor-cycle detection (validated as a clean single
24-cycle on both segid families) rather than trusting segid letter order. Outputs in
`analysis/2026-09-22/opening_distance/` (`plots/` subdir for PNGs). Known limitation: the per-frame
"opening" is a strict argmax across 24 ring edges, which produces sawtooth switching when two edges'
values are close — a rolling-window smoothing fix was proposed but not yet applied.

## Workflow
- All large files (PDB, DCD, PSF, restart) live on the cluster — do NOT commit them here
- This repo tracks: scripts, configs, analysis notebooks, and progress notes
- `progress_log.md` — full dated narrative history, NOT auto-loaded; read it when you need the
  reasoning behind a past decision, a diagnostic play-by-play, or anything marked "archived" above
