#!/usr/bin/env python3
"""
Superimpose AF3 HflK monomer onto each of the 12 HflK chains in the dome,
then report clashes between the M3 tail (biological 356-419, internal 278-341)
and all other dome atoms.
"""
import numpy as np
import copy
from Bio.PDB import MMCIFParser, PDBParser, Superimposer

CIF_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/fold_hflk_full_model_0.cif"
DOME_PATH = "/scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/9cz2minimized_08jun_01_ftsh_fixed.pdb"

HFLK_CHAINS   = ['A', 'C', 'E', 'G', 'I', 'K', 'M', 'O', 'Q', 'S', 'U', 'X']
ANCHOR_INT    = (1, 277)   # internal resid range for superimposition anchor
M3_INT        = (278, 341) # internal resid range for M3 tail
ANCHOR_BIO    = (79, 355)  # corresponding biological resid in dome

def is_heavy(atom):
    elem = (atom.element or '').strip()
    name = atom.get_name().strip()
    if elem:
        return elem not in ('H', 'D')
    return not (name.startswith('H') or name.startswith('D'))

print("Loading AF3 CIF...")
af3_struct = MMCIFParser(QUIET=True).get_structure("af3", CIF_PATH)
af3_chain  = list(af3_struct[0].get_chains())[0]

af3_anchor_ca = [
    res['CA'] for res in af3_chain
    if ANCHOR_INT[0] <= res.id[1] <= ANCHOR_INT[1] and 'CA' in res
]
print(f"  AF3 anchor CAs: {len(af3_anchor_ca)}")

print("Loading dome PDB (this may take a moment)...")
dome       = PDBParser(QUIET=True).get_structure("dome", DOME_PATH)
dome_model = dome[0]

print("Collecting dome heavy atoms...")
dome_heavy_coords = np.array([
    atom.coord
    for chain in dome_model
    for res   in chain
    for atom  in res
    if is_heavy(atom)
])
print(f"  Dome heavy atoms: {len(dome_heavy_coords)}")

print()
print(f"{'Chain':<7} {'Anchor CAs':<12} {'RMSD (Å)':<11} {'MinDist (Å)':<14} {'<1.5 Å':<9} {'<2.0 Å'}")
print("-" * 62)

for chain_id in HFLK_CHAINS:
    try:
        dome_chain = dome_model[chain_id]
    except KeyError:
        print(f"{chain_id:<7} NOT FOUND IN DOME")
        continue

    dome_anchor_ca = [
        res['CA'] for res in dome_chain
        if ANCHOR_BIO[0] <= res.id[1] <= ANCHOR_BIO[1] and 'CA' in res
    ]

    n_fixed  = len(dome_anchor_ca)
    n_mobile = len(af3_anchor_ca)
    n_use    = min(n_fixed, n_mobile)

    if n_use < 10:
        print(f"{chain_id:<7} too few anchor atoms ({n_use}), skipping")
        continue

    fixed  = dome_anchor_ca[:n_use]
    mobile = af3_anchor_ca[:n_use]

    sup = Superimposer()
    sup.set_atoms(fixed, mobile)

    # Deep copy chain, apply superimposition, extract M3 heavy atom coords
    af3_copy   = copy.deepcopy(af3_chain)
    all_atoms  = list(af3_copy.get_atoms())
    sup.apply(all_atoms)

    m3_coords = np.array([
        atom.coord
        for res  in af3_copy
        if M3_INT[0] <= res.id[1] <= M3_INT[1]
        for atom in res
        if is_heavy(atom)
    ])

    if len(m3_coords) == 0:
        print(f"{chain_id:<7} no M3 atoms after transform")
        continue

    # Vectorised distance: for each M3 atom find min dist to any dome heavy atom
    min_dists = np.array([
        np.linalg.norm(dome_heavy_coords - coord, axis=1).min()
        for coord in m3_coords
    ])

    print(f"{chain_id:<7} {n_use:<12} {sup.rms:<11.3f} {min_dists.min():<14.3f} "
          f"{(min_dists < 1.5).sum():<9} {(min_dists < 2.0).sum()}")

print()
print("Done.")
