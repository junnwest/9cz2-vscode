#!/usr/bin/env python3
"""
1. Fix missing segnames on M3 atoms (resid 356-419) in dome_with_m3_grafted.pdb
2. Remove OXT atoms (psfgen adds them via CTER patch)
3. Write per-segment PDB files for psfgen

Segment naming:
  Chains A-Z  -> XP1 (e.g. A->AP1, B->BP1, ..., Z->ZP1)
  Chains 0-9  -> XP2 (e.g. 1->1P2, 2->2P2, ..., 0->0P2)
"""
import os

IN_PDB  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/dome_m3_rotated.pdb"
OUT_DIR = "/scratch/midway3/junseo/26summer-research/minimize_m3/segments"
os.makedirs(OUT_DIR, exist_ok=True)

def chain_to_seg(ch):
    if ch.isalpha():
        return ch.upper() + "P1"
    else:
        return ch + "P2"

# Parse PDB and fix segnames
seg_lines = {}  # segname -> list of lines

with open(IN_PDB) as f:
    for line in f:
        if not line.startswith("ATOM") and not line.startswith("HETATM"):
            continue
        chain = line[21]
        resid = int(line[22:26].strip())
        atname = line[12:16].strip()

        # Skip OXT — psfgen generates it via CTER patch
        if atname == "OXT":
            continue

        seg = chain_to_seg(chain)

        # Fix missing segname (columns 72-75, 0-indexed)
        existing_seg = line[72:76].strip()
        if not existing_seg:
            line = line[:72] + f"{seg:<4}" + line[76:]

        seg_lines.setdefault(seg, []).append(line)

# Write per-segment PDB files
for seg, lines in seg_lines.items():
    out = os.path.join(OUT_DIR, f"{seg}.pdb")
    with open(out, "w") as f:
        f.writelines(lines)
        f.write("END\n")
    print(f"  {seg}: {len(lines)} atoms -> {out}")

print(f"\nDone. {len(seg_lines)} segment files written to {OUT_DIR}")
