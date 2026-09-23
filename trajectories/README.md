# Local trajectories

Gitignored working copies for visual inspection / analysis — the authoritative data lives on
Beagle3 `/scratch/beagle3/junseo/`. **Verify against the live cluster before assuming these are
current.**

This file previously duplicated per-system trajectory coverage, ns counts, and Martini variant
details directly — that content drifted out of sync with reality repeatedly (last version still
described `dome-bact` at 44 ns and claimed `control`/`dome-model` weren't pulled locally at all,
long after both were). Rather than maintain two copies of the same fast-changing state, current
details now live in one place: **CLAUDE.md's "Local trajectory copies — `trajectories/`" section**
(directory tree, per-system selection strings, load-script list, and known gotchas), kept in sync
there since it's loaded every session anyway.

## Quick pointers (stable across sessions, safe to keep here)

- **Load scripts**: `load_control.tcl`, `load_dome_model.tcl`, `load_dome_bact.tcl`,
  `load_full_model.tcl`, `load_full_bact.tcl` (one each), `load_all_5_namd.tcl` (all 5 at once),
  `load_v15.tcl`/`load_v16.tcl`/`load_v14.tcl` (Martini timestep-sensitivity variants). Source
  from VMD's Tk Console: `source /path/to/load_X.tcl`.
- **All-atom selections**: `protein`; lipids `resname DPPE POPG DOPG LOACL1 TLCL1` (cardiolipin is
  `LOACL1`/`TLCL1` here — that's the all-atom name, NOT `TOCL`, which is the Martini CG name for
  the same lipid). FtsH segnames vary by build — check CLAUDE.md's FtsH section, don't assume.
- **Martini (CG) selections**: VMD's `protein` macro doesn't work on CG beads (`BB`/`SC1`/... not
  `CA`/`N`/`C`). Use `not resname DPPE POPG DOPG TOCL W NA CL`. `cg_bonds -top` needs a `./`-prefixed
  relative path (it derives include paths by splitting on `/`) and must be pointed at its OWN
  variant's `.top` file, never borrowed from another variant.
- **Gotcha for any all-atom system**: VMD's built-in STRIDE fails silently above 99,999 protein
  atoms (writes a malformed temp PDB, leaving everything coil) — `source stride_by_segment.tcl`
  before using NewCartoon. Also: `STRIDE_BIN` isn't set by default in this shell environment; every
  `load_*.tcl` script sets a fallback before sourcing it.
- **v1-v13 Martini variants were removed from Beagle3 Sep 7** (disk-quota cleanup) — fully analyzed,
  with confirmed-complete local copies here first, so nothing was lost. v14/v15/v16 remain live on
  cluster and are the only ones still resubmittable.
