# Local trajectories

Gitignored. Working copies for visual inspection / analysis — the authoritative
data lives on Beagle3 `/scratch/beagle3/junseo/`.

## namd/ — all-atom (CHARMM36m, NAMD)

| System | Equilibration | Production (local) | On cluster |
|---|---|---|---|
| `dome-bact` | 6 DCDs (step6.1–6.6) | 44 ns (`step7_1–44`) | 56 ns |
| `full-bact` | 6 DCDs (step6.1–6.6) | 20 ns (`step7_1–20`) | 40 ns |
| `full-model` | — none pulled — | 37 ns (`step7_1–37`) | 37 ns (blocked, see below) |

Each folder has its own `step5_input.psf` + `step5_input.pdb`.

Not local: `control` (membrane-only baseline) and `dome-model` — the latter is
stuck behind the `/project2` mount outage.

Load in VMD (Tk Console), e.g. dome-bact:
```tcl
cd .../trajectories/namd/dome-bact
mol new step5_input.psf
mol addfile step5_input.pdb
foreach f {step6.1_equilibration.dcd step6.2_equilibration.dcd step6.3_equilibration.dcd \
           step6.4_equilibration.dcd step6.5_equilibration.dcd step6.6_equilibration.dcd} {
    mol addfile $f waitfor all
}
for {set i 1} {$i <= 44} {incr i} { mol addfile step7_$i.dcd waitfor all }
```
`full-bact` starts at `step7_1` (its `step7_0` warm-up wrote no DCD).
`full-model` is production-only — skip the step6 loop.

Selections (all-atom):
- protein: `protein`
- FtsH only: `segname PRAA PRAB PRAC PRAD PRAE PRAF PRAG PRAH PRAI PRAJ PROY PROZ`
- lipids: `resname DPPE POPG DOPG LOACL1 TLCL1`

## martini/ — coarse-grained (Martini 3, GROMACS)

Three variants of the same dome-only system, differing **only** in how protein
structure is restrained. All PBC-corrected (`trjconv -pbc mol -center`) and
decimated to 1 ns/frame.

| Dir | Variant | Span | Intra-chain | Inter-chain |
|---|---|---|---|---|
| `v1_elastic` | elastic network only | 1,228 ns | elastic network | **none** |
| `v2_flatbottom` | v1 + flat-bottom restraints | 1,084 ns | elastic network | 5,015 flat-bottom |
| `v3_go` | Go-Martini | 1,703 ns | 10,612 Go contacts | 4,663 Go contacts |

v1 is the **broken baseline** — chains stay folded but slide past each other into
disorder. Kept for comparison, not for analysis.

Structural comparison at ~900 ns (RMSD vs frame 0):

| | whole-assembly | per-chain |
|---|---|---|
| v1 elastic | 27.17 Å | 10.96 Å |
| v2 flat-bottom | 20.38 Å | **6.14 Å** |
| v3 Go | **18.78 Å** | 8.16 Å |

Load (v3 needs its **own** .gro/.top — it has 8,040 extra virtual sites):
```tcl
cd .../trajectories/martini/v3_go
mol new dome_go_membrane_system.gro
mol addfile production_1703ns.xtc waitfor all
source cg_bonds.tcl
cg_bonds -top ./dome_go_membrane_system.top -cutoff 6.2 -topoltype martini
```
For v1/v2 use `dome_martini_system.gro` / `.top` instead.

Note the `./` on `-top` — `cg_bonds.tcl` derives the include path by splitting on
`/`, so a bare filename resolves includes to `/martini_ff/...` and fails.

Selections (CG — note different names from all-atom):
- protein: `not resname DPPE POPG DOPG TOCL W NA CL`  (VMD's `protein` macro is
  unreliable on CG beads — they're `BB`/`SC1`/…, not `CA`/`N`/`C`)
- lipids: `resname DPPE POPG DOPG TOCL`  (cardiolipin is `TOCL`, not LOACL1/TLCL1)
- water `resname W`, ions `resname NA CL`
- **v3/v4/v5**: add `and not name CA` to hide the 8,040 massless Go virtual sites
  (they sit exactly on the `BB` beads — without this every backbone bead renders twice)

## `martini_sweep/` — v4 / v5 (added Aug 4, 2026)

Two more Go variants, 50 ns each, same processing (PBC-corrected, 1 ns/frame,
51 frames, 38 MB). They use **v3's** 185,885-atom structure with the Go virtual
sites — v1/v2's topology will not load them.

| Dir | Variant | Change from v3 |
|---|---|---|
| `martini_sweep/v4` | Go intra-chain only | 4,663 inter-chain contacts deleted |
| `martini_sweep/v5` | Go weakened | ε 9.414 → 5.0, all contacts kept |

Each also carries a `prod_v.xtc` = the 0–32 ns analysis window (33 frames) used
for the AA comparison.

```tcl
cd .../trajectories/martini_sweep/v4
mol new dome_go_membrane_system.gro
mol addfile v4_full_1nsframe.xtc waitfor all
source cg_bonds.tcl
cg_bonds -top ./dome_go_membrane_system.top -cutoff 6.2 -topoltype martini
```
Same for `v5` with `v5_full_1nsframe.xtc` (skip `source` if already loaded).

**Read the numbers before reading the movies.** Both start production **already
collapsed** — Rg_xy 75.76 (v4) and 76.14 (v5) versus AA's start of **79.65**,
i.e. essentially AA's *endpoint* (76.25) — and both finish *below* it. The
contraction happened during equilibration under the Go contact map, before frame
0. So frame 0 is the informative frame, not the trajectory's motion. v1/v2 start
at 79.00/79.51, where AA starts.

## Deleted as redundant

- `md_prod1_1ns_stride50.xtc` — original run built with **no** elastic network
  (`martinize2` was run without `-elastic`); scientifically invalid
- non-PBC-corrected duplicates, and the partial 917 ns flat-bottom snapshot
