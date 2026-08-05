#!/usr/bin/env python3
"""Add BILAYER_LIPIDHEAD_FC z-restraints to our Martini 3 lipid topologies.

Our lipid .itp files come from Martini-Force-Field-Initiative/M3-Lipid-Parameters,
which -- unlike CHARMM-GUI's bundled copies -- carry no [position_restraints]
block at all. So -DBILAYER_LIPIDHEAD_FC is currently a silent no-op for us.

The restraint pins the phosphate bead's z ONLY (fcx = fcy = 0), so lipids still
diffuse laterally and mix freely; it just stops the bilayer buckling while a
freshly-packed system relaxes. This matters for this system specifically: its
membrane needed the hand-tuned `insane -fudge 0.9` sweep to close a 147 nm2 void,
so it starts further from equilibrium than a routine build.

Cardiolipin gets BOTH phosphates restrained (it spans the leaflet as one molecule
with two headgroups; restraining only PO41 would tilt it).

Idempotent -- re-running detects the existing block and skips. Writes .bak once.

Usage:
    python3 add_lipid_headgroup_posres.py <martini_ff_dir> [--dry-run]
"""
import os
import re
import shutil
import sys

# lipid resname -> phosphate bead indices (1-based, verified against the actual
# [atoms] blocks of our M3 .itp files, not assumed from CHARMM-GUI's ordering)
PHOSPHATE_BEADS = {
    "DPPE": [2],
    "POPG": [2],
    "DOPG": [2],
    "TOCL": [2, 13],   # PO41, PO42
}

BLOCK = """
#ifdef BILAYER_LIPIDHEAD_FC
[ position_restraints ]
; Restrain headgroup phosphate z only -- keeps the bilayer planar during
; equilibration while leaving lateral diffusion untouched.
; atom funct  fcx  fcy  fcz
{lines}
#endif
"""


def find_moleculetype_span(lines, resname):
    """Return (start, end) line indices spanning `resname`'s moleculetype block.

    start = the '[ moleculetype ]' line; end = index just past the block's last
    line (i.e. at the next '[ moleculetype ]' or EOF).
    """
    mol_re = re.compile(r"^\s*\[\s*moleculetype\s*\]")
    starts = [i for i, l in enumerate(lines) if mol_re.match(l)]
    for si, start in enumerate(starts):
        end = starts[si + 1] if si + 1 < len(starts) else len(lines)
        # first non-comment, non-blank line after the directive names the molecule
        for l in lines[start + 1:end]:
            s = l.split(";")[0].strip()
            if not s:
                continue
            if s.split()[0] == resname:
                return start, end
            break
    return None


def patch_file(path, dry_run=False):
    with open(path) as fh:
        lines = fh.readlines()

    changed = []
    for resname, beads in PHOSPHATE_BEADS.items():
        span = find_moleculetype_span(lines, resname)
        if span is None:
            continue
        start, end = span
        body = "".join(lines[start:end])
        if "BILAYER_LIPIDHEAD_FC" in body:
            print(f"    {resname}: already patched, skipping")
            continue

        # sanity: the bead indices must actually exist in this moleculetype
        natoms = 0
        in_atoms = False
        for l in lines[start:end]:
            if re.match(r"^\s*\[\s*atoms\s*\]", l):
                in_atoms = True
                continue
            if in_atoms and re.match(r"^\s*\[", l):
                break
            if in_atoms:
                s = l.split(";")[0].strip()
                if s and s.split()[0].isdigit():
                    natoms = max(natoms, int(s.split()[0]))
        bad = [b for b in beads if b > natoms]
        if bad:
            raise SystemExit(
                f"ERROR {os.path.basename(path)} / {resname}: bead index {bad} "
                f"exceeds the molecule's {natoms} atoms -- bead ordering differs "
                f"from what this script assumes. Fix PHOSPHATE_BEADS before rerunning."
            )

        rest = "\n".join(f"  {b:<4d} 1    0.0  0.0  BILAYER_LIPIDHEAD_FC" for b in beads)
        # insert at the end of the moleculetype block, trimming trailing blanks
        ins = end
        while ins > start and not lines[ins - 1].strip():
            ins -= 1
        lines[ins:ins] = [BLOCK.format(lines=rest)]
        changed.append(f"{resname} (bead{'s' if len(beads) > 1 else ''} "
                       f"{', '.join(map(str, beads))})")

    if not changed:
        return False

    print(f"    patched: {'; '.join(changed)}")
    if not dry_run:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        with open(path, "w") as fh:
            fh.writelines(lines)
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 1:
        raise SystemExit(__doc__)
    ffdir = os.path.expanduser(args[0])
    if not os.path.isdir(ffdir):
        raise SystemExit(f"not a directory: {ffdir}")

    if dry:
        print("DRY RUN -- nothing will be written\n")
    total = 0
    for fn in sorted(os.listdir(ffdir)):
        if not fn.endswith(".itp"):
            continue
        path = os.path.join(ffdir, fn)
        print(f"  {fn}")
        if patch_file(path, dry_run=dry):
            total += 1

    print(f"\n{total} file(s) {'would be ' if dry else ''}patched.")
    if total:
        print("Verify with:  gmx grompp -f step6.2_equilibration.mdp ... "
              "(must report 0 errors)")


if __name__ == "__main__":
    main()
