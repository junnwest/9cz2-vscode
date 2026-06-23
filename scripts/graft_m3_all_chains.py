#!/usr/bin/env python3
"""
For each of the 12 HflK chains in Rajiv's dome:
  1. Superimpose AF3 HflK onto that chain (anchor: bio 79-355 / internal 1-277)
  2. Extract M3 (internal 278-341 = bio 356-419) from the superimposed AF3
  3. Check clashes of M3 against all dome atoms EXCLUDING the parent HflK chain
  4. Append M3 to the parent chain in the output structure

Output: Rajiv's dome + all 12 M3 tails grafted on, as a single PDB.
"""
import copy
import numpy as np
from Bio.PDB import MMCIFParser, PDBParser, Superimposer, PDBIO

CIF_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/fold_hflk_full_model_0.cif"
DOME_PATH = "/scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/9cz2minimized_08jun_01_ftsh_fixed.pdb"
OUT_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/dome_with_m3_grafted.pdb"

HFLK_CHAINS = ['A', 'C', 'E', 'G', 'I', 'K', 'M', 'O', 'Q', 'S', 'U', 'X']
BIO_OFFSET  = 78  # internal resid + 78 = biological resid

def is_heavy(atom):
    elem = (atom.element or '').strip()
    name = atom.get_name().strip()
    return (elem not in ('H', 'D') if elem else
            not (name.startswith('H') or name.startswith('D')))

# --- Load AF3 ---
print("Loading AF3 CIF...")
af3_chain = list(MMCIFParser(QUIET=True).get_structure("af3", CIF_PATH)[0].get_chains())[0]
af3_anchor_ca = [res['CA'] for res in af3_chain if 1 <= res.id[1] <= 277 and 'CA' in res]
print(f"  AF3 anchor CAs: {len(af3_anchor_ca)}")

# --- Load dome ---
print("Loading dome PDB...")
dome = PDBParser(QUIET=True).get_structure("dome", DOME_PATH)
dome_model = dome[0]

# --- Pre-collect heavy atom coords per chain for fast exclusion ---
print("Indexing dome heavy atoms by chain...")
chain_heavy = {}  # chain_id -> (coords array, atom list)
for ch in dome_model:
    coords = np.array([a.coord for r in ch for a in r if is_heavy(a)])
    chain_heavy[ch.id] = coords

all_chain_ids = list(chain_heavy.keys())

print()
print(f"{'Chain':<7} {'Anchor CAs':<12} {'RMSD (Å)':<11} {'Junc C-N (Å)':<15} {'<1.5 Å':<9} {'<2.0 Å'}")
print("-" * 60)

grafted_residues = {}  # chain_id -> list of transformed M3 residues

for chain_id in HFLK_CHAINS:
    try:
        dome_chain = dome_model[chain_id]
    except KeyError:
        print(f"{chain_id:<7} NOT FOUND")
        continue

    dome_anchor_ca = [res['CA'] for res in dome_chain
                      if 79 <= res.id[1] <= 355 and 'CA' in res]
    n = min(len(dome_anchor_ca), len(af3_anchor_ca))

    sup = Superimposer()
    sup.set_atoms(dome_anchor_ca[:n], af3_anchor_ca[:n])

    # Deep copy AF3 chain, apply superimposition
    af3_copy = copy.deepcopy(af3_chain)
    sup.apply(list(af3_copy.get_atoms()))

    # Extract M3 residues (internal 278-341)
    m3_residues = [res for res in af3_copy if 278 <= res.id[1] <= 341]

    # Renumber M3 to biological resid (internal + 78)
    for res in m3_residues:
        rid = res.id
        res.id = (rid[0], rid[1] + BIO_OFFSET, rid[2])

    # Junction geometry: distance from C of dome resid 355 to N of M3 resid 356
    junc_dist = float('nan')
    try:
        c355 = dome_chain[355]['C'].coord
        n356 = m3_residues[0]['N'].coord
        junc_dist = float(np.linalg.norm(c355 - n356))
    except (KeyError, IndexError):
        pass

    # Clash check: M3 heavy atoms vs all dome heavy atoms EXCEPT parent chain
    other_coords = np.vstack([v for k, v in chain_heavy.items()
                               if k != chain_id and len(v) > 0])
    m3_coords = np.array([a.coord for res in m3_residues for a in res if is_heavy(a)])

    min_dists = np.array([
        np.linalg.norm(other_coords - coord, axis=1).min()
        for coord in m3_coords
    ])

    print(f"{chain_id:<7} {n:<12} {sup.rms:<11.3f} {junc_dist:<15.3f} "
          f"{(min_dists < 1.5).sum():<9} {(min_dists < 2.0).sum()}")

    grafted_residues[chain_id] = m3_residues

# --- Build output: dome + grafted M3 residues ---
print("\nBuilding output structure...")
for chain_id, m3_res_list in grafted_residues.items():
    dome_chain = dome_model[chain_id]
    for res in m3_res_list:
        res.detach_parent()
        dome_chain.add(res)

print(f"Writing to {OUT_PATH} (heavy atoms only to stay within PDB serial limit)...")

class HeavyAtomSelect(object):
    def accept_model(self, m):   return 1
    def accept_chain(self, c):   return 1
    def accept_residue(self, r): return 1
    def accept_atom(self, a):    return 1 if is_heavy(a) else 0

io = PDBIO()
io.set_structure(dome)
io.save(OUT_PATH, select=HeavyAtomSelect())
print("Done.")
