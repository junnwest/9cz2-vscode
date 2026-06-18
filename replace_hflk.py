#!/usr/bin/env python3
"""
Replaces the 12 HflK chains in Rajiv's 9cz2 structure with AF2-predicted HflK
(residues 79-419), aligning each copy onto the original chain using CA atoms
from residues 79-355.

Usage:
    python replace_hflk.py <rajiv.pdb> <af2_hflk.pdb> <output.pdb>

    rajiv.pdb   - 9cz2minimized_08jun_01_ftsh_fixed.pdb (full structure)
    af2_hflk.pdb - manipulated AF2 HflK monomer (residues 79-419, any chain)
    output.pdb   - HflC + FtsH from Rajiv + 12 aligned AF2 HflK copies
"""

import sys
import numpy as np

HFLK_SEGNAMES = ['AP1', 'CP1', 'EP1', 'GP1', 'IP1', 'KP1',
                 'MP1', 'OP1', 'QP1', 'SP1', 'UP1', 'XP1']
HFLK_CHAINS   = ['A',   'C',   'E',   'G',   'I',   'K',
                 'M',   'O',   'Q',   'S',   'U',   'X']
ALIGN_RESID   = (79, 355)


def parse_pdb(path):
    atoms, header = [], []
    with open(path) as f:
        for line in f:
            if line.startswith(('ATOM', 'HETATM')):
                atoms.append({
                    'rec':     line[0:6].strip(),
                    'name':    line[12:16],
                    'altloc':  line[16],
                    'resname': line[17:20],
                    'chain':   line[21],
                    'resid':   int(line[22:26]),
                    'icode':   line[26],
                    'x':       float(line[30:38]),
                    'y':       float(line[38:46]),
                    'z':       float(line[46:54]),
                    'occ':     line[54:60],
                    'bfac':    line[60:66],
                    'segname': line[72:76].strip() if len(line) > 72 else '',
                })
            elif line.startswith(('CRYST1', 'REMARK', 'TITLE')):
                header.append(line)
    return atoms, header


def kabsch(P, Q):
    """Rotation R and translation t that minimise RMSD of P onto Q."""
    cP, cQ = P.mean(0), Q.mean(0)
    H = (P - cP).T @ (Q - cQ)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    t = cQ - cP @ R.T
    return R, t


def fmt_line(a, serial):
    return (
        f"{'ATOM':<6}{serial:5d} {a['name']}{a['altloc']}"
        f"{a['resname']} {a['chain']}{a['resid']:4d}{a['icode']}"
        f"   {a['x']:8.3f}{a['y']:8.3f}{a['z']:8.3f}"
        f"{a['occ']}{a['bfac']}      "
        f"{a['segname']:<4}\n"
    )


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    rajiv_pdb, af2_pdb, out_pdb = sys.argv[1], sys.argv[2], sys.argv[3]

    rajiv_atoms, header = parse_pdb(rajiv_pdb)
    af2_atoms, _        = parse_pdb(af2_pdb)

    # AF2 CA coords for alignment region, keyed by resid
    af2_ca = {a['resid']: np.array([a['x'], a['y'], a['z']])
              for a in af2_atoms
              if a['name'].strip() == 'CA'
              and ALIGN_RESID[0] <= a['resid'] <= ALIGN_RESID[1]}

    af2_xyz = np.array([[a['x'], a['y'], a['z']] for a in af2_atoms])

    # Non-HflK atoms from Rajiv stay unchanged
    out_atoms = [a for a in rajiv_atoms if a['segname'] not in HFLK_SEGNAMES]

    for seg, chain in zip(HFLK_SEGNAMES, HFLK_CHAINS):
        ref_ca = {a['resid']: np.array([a['x'], a['y'], a['z']])
                  for a in rajiv_atoms
                  if a['segname'] == seg
                  and a['name'].strip() == 'CA'
                  and ALIGN_RESID[0] <= a['resid'] <= ALIGN_RESID[1]}

        common = sorted(set(af2_ca) & set(ref_ca))
        print(f"{seg} (chain {chain}): {len(common)} CA residues used for alignment")
        if len(common) < 10:
            print(f"  WARNING: too few common residues, skipping {seg}")
            continue

        P = np.array([af2_ca[r]  for r in common])
        Q = np.array([ref_ca[r]  for r in common])
        R, t = kabsch(P, Q)

        new_xyz = af2_xyz @ R.T + t

        for i, a in enumerate(af2_atoms):
            new_a = dict(a)
            new_a['x'], new_a['y'], new_a['z'] = new_xyz[i]
            new_a['chain']   = chain
            new_a['segname'] = seg
            out_atoms.append(new_a)

    with open(out_pdb, 'w') as f:
        for line in header:
            f.write(line)
        for serial, a in enumerate(out_atoms, start=1):
            f.write(fmt_line(a, serial))
        f.write("END\n")

    print(f"Done — {len(out_atoms)} atoms written to {out_pdb}")


if __name__ == '__main__':
    main()
