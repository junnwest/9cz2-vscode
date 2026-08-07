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
  - **Dome-only + membrane-only** (`control`, `dome-model`, `dome-bact`): GPU-**resident**
    (`CUDASOAintegrate on`), 2 GPU / 16 PE (`control`: 4 GPU / 32 PE). ~8 ns/day. Non-HMR (HMR
    gives ~2× speed but measurably compromises kinetic/dynamical properties — not adopted).
  - **FtsH systems** (`full-model`, `full-bact`): GPU-**offload** (`CUDASOAintegrate off`), 1 GPU /
    8 PE, ~2 ns/day. **Resident mode crashes these** with `SequencerCUDA: Atoms moving too fast`,
    not fixable with a warm-up (full diagnostic chain archived in `progress_log.md`).
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

---

## Current Systems

**Always verify against the live cluster at session start (Step 3 above) — this table is a snapshot.**

**Beagle3 is the primary cluster for all production/equilibration systems**, `/scratch/beagle3/junseo/`.
**`/project2/haddadian` is unreliable** — it is actually served by Midway2 (`midway2_cap` filesystem,
confirmed via `mount | grep project2`), not a Beagle3/Midway3-native mount, and has gone
unreachable from both for days at a time. `ssh midway2` is the authoritative host for it if you
must use it; prefer moving anything off `/project2` onto Beagle3 scratch instead.

### The 5 systems (5 systems × 3 methods = 15-run target)

| Name | Protein content | Lipid composition |
|---|---|---|
| `control` | none (membrane-only baseline) | Composition #1 |
| `dome-model` | dome only (24 HflK/HflC chains, no FtsH) | Composition #1 |
| `dome-bact` | dome only | Composition #2 |
| `full-model` | full dome + FtsH (resid 1–120, see FtsH section) | Composition #1 |
| `full-bact` | full dome + FtsH (resid 1–120) | Composition #2 |

`full-model`/`full-bact` are built from the identical protein structure (12 HflK 79–419, 12 HflC
1–329, 12 FtsH 1–120) and differ only in lipids — the composition comparison is not confounded by
a different protein build. Same holds for `dome-model`/`dome-bact` (both from
`dome_m3_af3_ic_minimized_final_noftsh.pdb`).

**Beagle3 paths**: `control`, `dome-bact`, `full-bact`, `full-model` all under
`/scratch/beagle3/junseo/{system}/{namd,gamd}/` (system-first, since NAMD+GaMD share large
PSF/PDB/toppar inputs). `dome-model` may still be at its `/project2` staging path — verify with
`squeue`/`ls` before assuming; don't rename a directory a running SLURM job has as its WorkDir.
Martini variants live at `/scratch/beagle3/junseo/martini-sweep-{v1..v11}/` (method-first, since
Martini shares nothing with the AA systems).

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

**FtsH segment naming in these PSFs** (empirical, from residue ranges — CHARMM-GUI's `PRO*`/`PRA*`
naming does not map to the older `Y,Z,0-9` scheme): FtsH = `PRAA`–`PRAJ` + `PROY` + `PROZ`, 12
segments, all resid 31–97 in the *old* superseded builds — check actual ranges in the current
rebuild before relying on this, since the rebuild extended the range. `PROY`/`PROZ` are easy to
mistake for dome chains; distinguish by residue range, not name.

Previous `full-bact` build (40 ns production + GaMD, FtsH 31-97) is **archived, not deleted**, at
`full-bact/superseded_ftsh31-97/{namd,gamd}/`.

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
| v10 no elastic, real SS | CHARMM-GUI method exactly (STRIDE, no springs, staged ladder) | pending | | | |
| v11 elastic + real SS | v10 + elastic ef 700 | pending | | | |

**v2's EM bug**: confirmed from run logs that v2 alone minimized with `coulombtype=PME`,
`epsilon_r=1` (should be reaction-field, ε_r=15 like every other variant — a file that was never
updated when the others were fixed). Electrostatics ~15× too strong on an anionic-lipid membrane.
This means every "v2 is best" conclusion above rests on a bad starting structure, and neither the
v1→v2 nor v6→v2 "more restraint helps" comparisons are clean (both cross the EM change). v9 retests
v2's exact topology with corrected EM to measure the damage.

**Open question (v10/v11, submitted Aug 5, not yet read out)**: now that secondary structure is
supplied properly, does the elastic network still do necessary work, or was it only compensating
for the missing force-field terms? Neither v10 nor v11 has inter-chain restraints — if the
assembly loosens in both, that points to needing something between chains regardless of per-chain
structure quality.

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

Local trajectory copies (gitignored, ~cluster remains authoritative) at
`trajectories/martini/{v1_elastic,v2_flatbottom,v3_go}/` and `trajectories/martini_sweep/{v4..v9}/`.
Load with `trajectories/load_v1_v6.tcl` (`WINDOW_NS` selects 0-32/0-50/full; handles the two-topology
split — v1/v2/v6/v9 use `dome_martini_system.gro` 177,845 atoms, v3/v4/v5 use
`dome_go_membrane_system.gro` 185,885 atoms with 8,040 extra Go virtual sites).

---

## GaMD — status and operational rules

**Reality check**: GaMD's 22.5M-step (45 ns) schedule is *equilibration* (7.5M cMD + 15M
boost-equilibration) — production GaMD sampling only begins after that completes. Check `E`/`k` in
the `.gamd` file: `E=k=0` means still in the cMD phase, i.e. plain conventional MD, not GaMD data
yet, however long the DCD is.

**`control`/`dome-model`/`dome-bact` all have GaMD equilibration running or queued.**
`full-model`/`full-bact` need 20 ns of conventional production first (the two full systems were
just rebuilt Aug 5, so they're not there yet).

**GPU-resident GaMD is REJECTED — stays offload.** Dr. Chen's GPU-resident NAMD build
(`/scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3`, branch
`haochuan/gpu_accelmd_2`) runs ~3× faster but **corrupts the GaMD boost statistics** on restart —
validated empirically (job 52975499): DIHED `Vmin` collapses to exactly 0, `sigmaV` inflates
~4,500×, on the very first statistics update after a restart. The `ENERGY:` output itself matches
offload to 0.008% — the fault is in the boost-statistics accumulator, not the force/integration
path, so a smoke test that only checks energies won't catch it. **Do not switch any GaMD run to
resident mode.** Full validation numbers archived in `progress_log.md`.

Chen's build is still useful for **conventional** (non-GaMD) resident-mode MD, where it's fine —
`share_gamd_resident/` (repo root) has a verified-working reference config for that use case.
Requires `fullElectFrequency 1` (not 2), `wrapWater on`/`wrapAll on` (NAMD's default is off),
`pairlistdist 16.0` — invoke Chen's binary by full path, never bare `namd3`.

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
  other — transfer sequentially.
- **Production jobs going idle (not crashing) is the recurring failure mode.** Jobs exit 0 cleanly
  at their chunk/wall-time cap and nothing auto-resubmits. Check `squeue` every session against
  the Current Systems table.

---

## Local trajectory copies — `trajectories/`

Gitignored working copies for VMD/analysis. Cluster (`/scratch/beagle3/junseo/`) remains
authoritative. **Verify against the cluster before assuming these are current** — this list is a
snapshot, not live-synced.

```
trajectories/
├── README.md                  ← VMD load commands, selection strings, gotchas — READ FIRST
├── load_v1_v6.tcl             ← loads all Martini variants, handles the two-topology split
├── namd/                      all-atom (CHARMM36m)
│   ├── dome-bact/   step7_1-80 (80 ns) + step6.1-6.6 equilibration
│   ├── full-bact/   eq + 20 ns   (cluster ahead — check squeue)
│   └── full-model/  37 ns, production only (superseded build — full-model was rebuilt Aug 5,
│                    this local copy predates the rebuild)
├── martini/                   v1_elastic, v2_flatbottom, v3_go (full-length trajectories)
├── martini_sweep/             v4-v9 (50 ns each), v10/v11 pending download
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
already set up). Known issue: wrapping artifacts break center-of-mass calcs — unwrap the
trajectory first.

`control` system analysis (thickness/curvature/order-parameter/area-per-lipid) lives in
`analysis/control/<Nns>/<script>/`. The Voronoi APL script (code on Midway3 only, repo tracks just
`.npy`/`.png` outputs) should be **reused unchanged for the other 4 systems**, not reimplemented
per-system, for a fair comparison. `control` 35 ns result: combined 54.35 Ų (DPPE 52.93, POPG
54.60, DOPG 56.34, LOACL1 71.49, TLCL1 73.27).

## Workflow
- All large files (PDB, DCD, PSF, restart) live on the cluster — do NOT commit them here
- This repo tracks: scripts, configs, analysis notebooks, and progress notes
- `progress_log.md` — full dated narrative history, NOT auto-loaded; read it when you need the
  reasoning behind a past decision, a diagnostic play-by-play, or anything marked "archived" above
