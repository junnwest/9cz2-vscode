#!/usr/bin/env python3
"""
For each of the 12 HflK chains:
  1. Close the C355-N356 junction gap (translate N356 to ideal trans-peptide position).
  2. 2D rotation search:
       Axis 1 — C355->N356 (omega dihedral),  5-degree steps
       Axis 2 — N356->CA356 (phi of res 356), 5-degree steps
       Total: 72 x 72 = 5184 orientations per chain.
  3. Inward constraint: only consider orientations where M3's COM points
     toward the dome interior (positive dot product with dome-center direction).
  4. Among valid orientations, pick minimum clashes vs dome (excl. parent chain).
     If no inward orientation exists, fall back to global minimum.
Output: dome_m3_rotated.pdb
"""
import numpy as np
from scipy.spatial import KDTree
from Bio.PDB import PDBParser, PDBIO, Select

DOME_PATH  = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/dome_with_m3_grafted.pdb"
OUT_PATH   = "/scratch/midway3/junseo/26summer-research/alphafold/9cz2/dome_m3_rotated.pdb"

HFLK_CHAINS = list("ACEGIKMOQSUX")
HFLK_SET    = set(HFLK_CHAINS)
HFLC_SET    = set("BDFHJLNPRTVW")
CN_BOND     = 1.329
STEP_DEG    = 2.0
CLASH_DIST  = 1.5
CLASH_MOD   = 2.0

def is_heavy(atom):
    elem = (atom.element or '').strip()
    name = atom.get_name().strip()
    return (elem not in ('H', 'D') if elem else
            not (name.startswith('H') or name.startswith('D')))

def rotate_points(coords, axis, angle_rad, pivot):
    c, s  = np.cos(angle_rad), np.sin(angle_rad)
    v     = coords - pivot
    dot   = np.einsum('i,ni->n', axis, v)
    cross = np.cross(axis, v)
    return pivot + v * c + cross * s + np.outer(dot, axis) * (1 - c)

print("Loading dome PDB...")
dome       = PDBParser(QUIET=True).get_structure("dome", DOME_PATH)
dome_model = dome[0]

# --- Dome interior reference: centroid of all HflK/HflC Cα atoms ---
ca_coords = []
for ch in dome_model:
    if ch.id in HFLK_SET or ch.id in HFLC_SET:
        for res in ch:
            if 'CA' in res and res.id[1] <= 355:  # resolved region only
                ca_coords.append(res['CA'].coord)
dome_center = np.mean(ca_coords, axis=0)
print(f"  Dome center (Cα centroid): {dome_center.round(1)}")

# --- Per-chain heavy atom index ---
print("Indexing dome heavy atoms by chain...")
chain_heavy = {}
for ch in dome_model:
    coords = np.array([a.coord for r in ch for a in r if is_heavy(a)])
    if len(coords):
        chain_heavy[ch.id] = coords

print()
print(f"{'Chain':<7} {'Gap(Å)':<9} {'Omega°':<8} {'Phi°':<8} {'Inward':<8} {'<1.5Å':<8} {'<2.0Å'}")
print("-" * 57)

angles = np.arange(0, 360, STEP_DEG)

for chain_id in HFLK_CHAINS:
    dome_chain = dome_model[chain_id]

    # Junction atoms
    res355 = next((r for r in dome_chain if r.id[1] == 355), None)
    if res355 is None or 'C' not in res355:
        print(f"{chain_id:<7} missing res 355")
        continue
    c355 = res355['C'].coord.copy()
    o355 = (res355['O'] if 'O' in res355 else res355['OT1']).coord.copy()

    co_unit    = (c355 - o355) / np.linalg.norm(c355 - o355)
    n356_ideal = c355 + CN_BOND * co_unit
    translation = n356_ideal - next(
        (r for r in dome_chain if r.id[1] == 356), None)['N'].coord

    # M3 atoms + objects
    m3_res      = [r for r in dome_chain if 356 <= r.id[1] <= 419]
    m3_objs     = [(a, a.coord.copy()) for r in m3_res for a in r if is_heavy(a)]
    m3_coords_0 = np.array([c for _, c in m3_objs]) + translation  # after gap close

    # Axis 1: omega (C355->N356)
    ax1 = co_unit

    # Axis 2: phi (N356->CA356, after translation)
    ca356_coord = next(
        (r for r in dome_chain if r.id[1] == 356), None)['CA'].coord + translation
    ax2_raw  = ca356_coord - n356_ideal
    ax2      = ax2_raw / np.linalg.norm(ax2_raw)

    # Other-chain KD-tree
    other_coords = np.vstack([v for k, v in chain_heavy.items()
                               if k != chain_id and len(v)])
    tree = KDTree(other_coords)

    # Direction from C355 toward dome center (reference for "inward")
    inward_ref = dome_center - c355
    inward_ref /= np.linalg.norm(inward_ref)

    gap = float(np.linalg.norm(c355 - (m3_coords_0[0] - translation +
                 next((r for r in dome_chain if r.id[1] == 356), None)['N'].coord - translation +
                 next((r for r in dome_chain if r.id[1] == 356), None)['N'].coord)))
    # Simpler gap calc
    n356_orig = next((r for r in dome_chain if r.id[1] == 356), None)['N'].coord
    gap = float(np.linalg.norm(c355 - n356_orig))

    best = {'c15': int(1e9), 'c20': int(1e9), 'omega': 0.0, 'phi': 0.0, 'inward': False}
    best_inward = {'c15': int(1e9), 'c20': int(1e9), 'omega': 0.0, 'phi': 0.0}

    for omega_deg in angles:
        # Apply omega rotation first
        r1 = rotate_points(m3_coords_0, ax1, np.radians(omega_deg), n356_ideal)

        # Re-derive ax2 after omega rotation (CA356 moves with M3)
        ca356_r1  = rotate_points(ca356_coord[None, :], ax1,
                                   np.radians(omega_deg), n356_ideal)[0]
        ax2_r1    = ca356_r1 - n356_ideal
        ax2_r1   /= np.linalg.norm(ax2_r1)

        for phi_deg in angles:
            rotated  = rotate_points(r1, ax2_r1, np.radians(phi_deg), n356_ideal)

            # Inward check: M3 COM direction vs dome center direction
            m3_com   = rotated.mean(axis=0)
            m3_dir   = m3_com - c355
            if np.linalg.norm(m3_dir) > 0:
                m3_dir /= np.linalg.norm(m3_dir)
            is_inward = float(np.dot(m3_dir, inward_ref)) > 0

            dists, _ = tree.query(rotated, k=1)
            c15 = int((dists < CLASH_DIST).sum())
            c20 = int((dists < CLASH_MOD).sum())

            # Track global best
            if c15 < best['c15'] or (c15 == best['c15'] and c20 < best['c20']):
                best.update({'c15': c15, 'c20': c20,
                             'omega': omega_deg, 'phi': phi_deg, 'inward': is_inward})

            # Track inward-only best
            if is_inward:
                if c15 < best_inward['c15'] or (c15 == best_inward['c15'] and
                                                  c20 < best_inward['c20']):
                    best_inward.update({'c15': c15, 'c20': c20,
                                        'omega': omega_deg, 'phi': phi_deg})

    # Choose: prefer inward solution; fall back to global if none found
    use_inward = best_inward['c15'] < int(1e9)
    chosen     = best_inward if use_inward else best
    print(f"{chain_id:<7} {gap:<9.2f} {chosen['omega']:<8.0f} {chosen['phi']:<8.0f} "
          f"{'yes' if use_inward else 'NO':<8} {chosen['c15']:<8} {chosen['c20']}")

    # Apply chosen rotation to atom objects
    r1 = rotate_points(m3_coords_0, ax1, np.radians(chosen['omega']), n356_ideal)
    ca356_r1 = rotate_points(ca356_coord[None, :], ax1,
                              np.radians(chosen['omega']), n356_ideal)[0]
    ax2_r1   = ca356_r1 - n356_ideal
    ax2_r1  /= np.linalg.norm(ax2_r1)
    final    = rotate_points(r1, ax2_r1, np.radians(chosen['phi']), n356_ideal)

    for i, (atom, _) in enumerate(m3_objs):
        atom.set_coord(final[i])

class HeavySelect(Select):
    def accept_atom(self, a): return 1 if is_heavy(a) else 0

print("\nWriting output PDB...")
io = PDBIO()
io.set_structure(dome)
io.save(OUT_PATH, select=HeavySelect())
print(f"Done: {OUT_PATH}")
