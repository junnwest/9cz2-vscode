#!/usr/bin/env python3
"""
Superimpose AF3 HflK onto chain A of the dome (anchor: bio 79-355 / internal 1-277),
renumber residues to biological (internal + 78), and write the result as a PDB.
Load the output alongside the dome PDB in VMD to visualize M3 placement.
"""
import copy
from Bio.PDB import MMCIFParser, PDBParser, Superimposer, PDBIO, Structure, Model

CIF_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/fold_hflk_full_model_0.cif"
DOME_PATH = "/scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/9cz2minimized_08jun_01_ftsh_fixed.pdb"
OUT_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/fold_hflk_superimposed_chainA.pdb"

BIO_OFFSET = 78  # internal resid + 78 = biological resid

print("Loading AF3 CIF...")
af3_struct = MMCIFParser(QUIET=True).get_structure("af3", CIF_PATH)
af3_chain  = list(af3_struct[0].get_chains())[0]
af3_anchor_ca = [res['CA'] for res in af3_chain
                 if 1 <= res.id[1] <= 277 and 'CA' in res]

print("Loading dome PDB...")
dome = PDBParser(QUIET=True).get_structure("dome", DOME_PATH)
dome_anchor_ca = [res['CA'] for res in dome[0]['A']
                  if 79 <= res.id[1] <= 355 and 'CA' in res]

n = min(len(dome_anchor_ca), len(af3_anchor_ca))
print(f"Anchor CAs — dome: {len(dome_anchor_ca)}, AF3: {len(af3_anchor_ca)}, using: {n}")

sup = Superimposer()
sup.set_atoms(dome_anchor_ca[:n], af3_anchor_ca[:n])
print(f"RMSD: {sup.rms:.3f} Å")

# Deep copy chain, apply superimposition
af3_copy = copy.deepcopy(af3_chain)
sup.apply(list(af3_copy.get_atoms()))

# Renumber to biological (internal + 78) and assign distinct chain ID
for res in af3_copy:
    rid = res.id
    res.id = (rid[0], rid[1] + BIO_OFFSET, rid[2])
af3_copy.id = 'a'  # lowercase to distinguish from dome chain A

# Wrap in a minimal structure and write
out = Structure.Structure("af3_sup")
m   = Model.Model(0)
out.add(m)
m.add(af3_copy)

io = PDBIO()
io.set_structure(out)
io.save(OUT_PATH)
print(f"Written: {OUT_PATH}")
print(f"  Chain a, resid 79-419 (M3 = resid 356-419)")
