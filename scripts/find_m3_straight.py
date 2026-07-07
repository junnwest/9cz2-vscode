#!/usr/bin/env python3
"""
Build each HflK M3 tail (resid 356-419) as a straight backbone along each
chain's unique fan direction:

  target_dir(chain) = normalize(outward_XY × sin(TILT) + [0,0,-1] × cos(TILT))

For each residue i (0-based from resid 356):
  CA_ideal_i = CA_placed_356 + i × CA_CA_STEP × target_dir
  translate ALL atoms of residue i by (CA_ideal_i - CA_placed_i)

This preserves every residue's internal geometry (bond lengths, angles,
side chains) exactly while giving a straight backbone along target_dir.
Inter-residue N-Cα-C bonds will be slightly stretched but NAMD minimisation
restores them.

Straight lines in different directions cannot topologically entangle —
the entanglement problem is eliminated by construction.

Backbone for clash detection: HflK≤355 + HflC + FtsH.
Residual contacts resolved by iterative atom nudge.

Output: dome_m3_straight.pdb
"""

import numpy as np
from scipy.spatial import cKDTree
import os, sys
from collections import defaultdict

BASE    = "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
IN_PDB  = os.path.join(BASE, "dome_m3_rotated.pdb")
OUT_PDB = os.path.join(BASE, "dome_m3_straight.pdb")

HFLK_SEGS = ['AP1','CP1','EP1','GP1','IP1','KP1','MP1','OP1','QP1','SP1','UP1','XP1']
HFLC_SEGS = ['BP1','DP1','FP1','HP1','JP1','LP1','NP1','PP1','RP1','TP1','VP1','WP1']
FTSH_SEGS = ['0P2','1P2','2P2','3P2','4P2','5P2','6P2','7P2','8P2','9P2','YP1','ZP1']
CHAIN_TO_SEG = {'A':'AP1','C':'CP1','E':'EP1','G':'GP1','I':'IP1','K':'KP1',
                'M':'MP1','O':'OP1','Q':'QP1','S':'SP1','U':'UP1','X':'XP1'}
SEG_TO_CHAIN = {v: k for k, v in CHAIN_TO_SEG.items()}

REF_SEG    = 'IP1'
TILT_DEG   = 45.0    # degrees from -Z toward each chain's radially-outward direction
CA_CA_STEP = 3.8     # Å between consecutive CA positions along the straight backbone
CLASH_D    = 1.5     # Å clash threshold
NUDGE_D    = 0.3     # Å per nudge step (scaled by overlap depth)
MAX_ITER   = 200


# ── Utilities ─────────────────────────────────────────────────────────────────

def parse_pdb(path):
    atoms = []
    with open(path) as f:
        for line in f:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            seg = line[72:76].strip()
            cid = line[21]
            try:
                resid = int(line[22:26])
                x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            except ValueError:
                continue
            atoms.append({'seg': seg, 'chain': cid, 'resid': resid,
                          'name': line[12:16].strip(),
                          'xyz':  np.array([x, y, z]),
                          'line': line})
    return atoms


def kabsch(P, Q):
    p0, q0 = P.mean(0), Q.mean(0)
    Pc, Qc = P - p0, Q - q0
    U, _, Vt = np.linalg.svd(Pc.T @ Qc)
    d = np.linalg.det(Vt.T @ U.T)
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, q0 - R @ p0


def write_serial(n):
    return f"{n:5d}" if n <= 99999 else f"{n:5x}"


# ── Load ──────────────────────────────────────────────────────────────────────

all_atoms = parse_pdb(IN_PDB)

backbone = [a for a in all_atoms
            if (a['seg'] in HFLK_SEGS and a['resid'] <= 355)
            or  a['seg'] in HFLC_SEGS
            or  a['seg'] in FTSH_SEGS]
backbone_xyz = np.array([a['xyz'] for a in backbone])
print(f"Backbone: {len(backbone)} atoms (HflK≤355 + HflC + FtsH)")

ref_chain_id = SEG_TO_CHAIN[REF_SEG]
m3_tmpl = [a for a in all_atoms
           if a['chain'] == ref_chain_id and 356 <= a['resid'] <= 419 and a['seg'] == '']
m3_tmpl_xyz = np.array([a['xyz'] for a in m3_tmpl])
print(f"M3 template (chain {ref_chain_id}): {len(m3_tmpl)} atoms")
if not m3_tmpl:
    sys.exit("ERROR: M3 template empty")

# Group template atoms by residue (in order)
tmpl_by_resid = defaultdict(list)
for i, a in enumerate(m3_tmpl):
    tmpl_by_resid[a['resid']].append(i)
resid_order = sorted(tmpl_by_resid.keys())   # [356, 357, ..., 419]
print(f"M3 residues: {resid_order[0]}–{resid_order[-1]}  ({len(resid_order)} residues)")


def bb_ca(seg, r0, r1):
    return np.array([a['xyz'] for a in backbone
                     if a['seg'] == seg and a['name'] == 'CA' and r0 <= a['resid'] <= r1])


ref_ca_align = bb_ca(REF_SEG, 350, 355)

all_bb_ca  = np.array([a['xyz'] for a in backbone if a['name'] == 'CA'])
dome_cen   = all_bb_ca.mean(0)
print(f"Dome centroid XY: ({dome_cen[0]:.1f}, {dome_cen[1]:.1f})\n")

tilt_rad = np.radians(TILT_DEG)
DOWN     = np.array([0.0, 0.0, -1.0])


# ── Straighten M3 for each chain ─────────────────────────────────────────────

final_m3 = {}   # seg -> (N_atoms, 3)  indices match m3_tmpl
segs_ok  = []

for seg in HFLK_SEGS:
    tgt_ca = bb_ca(seg, 350, 355)
    if len(tgt_ca) < len(ref_ca_align):
        print(f"  WARNING: {seg} sparse CA 350-355, skipping")
        continue

    # Step 1: Kabsch placement (only used to get CA(356) anchor position)
    if seg == REF_SEG:
        placed_xyz = m3_tmpl_xyz.copy()
    else:
        R_k, t_k = kabsch(ref_ca_align, tgt_ca)
        placed_xyz = (R_k @ m3_tmpl_xyz.T).T + t_k

    # CA(356) anchor: position of the first M3 CA after Kabsch placement
    first_resid = resid_order[0]
    ca356_idx   = next((i for i in tmpl_by_resid[first_resid]
                        if m3_tmpl[i]['name'] == 'CA'), tmpl_by_resid[first_resid][0])
    ca356_pos   = placed_xyz[ca356_idx]

    # Step 2: per-chain target direction (outward XY + -Z)
    ca355_arr = bb_ca(seg, 355, 355)
    pivot     = ca355_arr[0] if len(ca355_arr) else tgt_ca[-1]

    outward_xy = pivot[:2] - dome_cen[:2]
    norm_oxy   = np.linalg.norm(outward_xy)
    if norm_oxy < 1e-6:
        outward_xy = np.array([1.0, 0.0]); norm_oxy = 1.0
    outward_3d = np.array([outward_xy[0]/norm_oxy, outward_xy[1]/norm_oxy, 0.0])
    target = outward_3d * np.sin(tilt_rad) + DOWN * np.cos(tilt_rad)
    target /= np.linalg.norm(target)

    # Step 3: build ideal CA positions along straight line from CA(356)
    ca_ideal = {resid: ca356_pos + i * CA_CA_STEP * target
                for i, resid in enumerate(resid_order)}

    # Step 4: translate each residue's atoms by (ca_ideal - ca_placed) for that residue
    new_xyz = placed_xyz.copy()
    for resid in resid_order:
        indices = tmpl_by_resid[resid]
        # Find CA of this residue in placed structure
        ca_placed = None
        for idx in indices:
            if m3_tmpl[idx]['name'] == 'CA':
                ca_placed = placed_xyz[idx]
                break
        if ca_placed is None:
            ca_placed = placed_xyz[indices[0]]   # fallback: any atom

        shift = ca_ideal[resid] - ca_placed
        for idx in indices:
            new_xyz[idx] = placed_xyz[idx] + shift

    final_m3[seg] = new_xyz
    segs_ok.append(seg)

    tip_ca_idx = next((i for i in tmpl_by_resid[resid_order[-1]]
                       if m3_tmpl[i]['name'] == 'CA'), tmpl_by_resid[resid_order[-1]][0])
    tip_z = new_xyz[tip_ca_idx][2]
    az    = np.degrees(np.arctan2(outward_xy[1], outward_xy[0]))
    print(f"  {seg}: azimuth={az:+.0f}°  CA(419) tip Z={tip_z:.1f}")

print(f"\nBuilt straight M3 for {len(segs_ok)} chains (TILT={TILT_DEG}°)\n")


# ── Pre-nudge clash count ─────────────────────────────────────────────────────

bb_tree     = cKDTree(backbone_xyz)
all_m3_flat = np.vstack([final_m3[s] for s in segs_ok])
n_bb_pre    = sum(len(nb) for nb in bb_tree.query_ball_point(all_m3_flat, CLASH_D))
rl          = [final_m3[s] for s in segs_ok]
n_m3_pre    = 0
for i in range(len(rl)):
    ti = cKDTree(rl[i])
    for j in range(i+1, len(rl)):
        n_m3_pre += sum(len(nb) for nb in ti.query_ball_point(rl[j], CLASH_D))
print(f"Before nudge: backbone={n_bb_pre}, inter-M3={n_m3_pre}, total={n_bb_pre+n_m3_pre}")


# ── Iterative clash nudge ─────────────────────────────────────────────────────

print(f"Nudging (cutoff {CLASH_D} Å, step {NUDGE_D} Å × depth, max {MAX_ITER} iter) …")

for iteration in range(MAX_ITER):
    forces = {seg: np.zeros_like(final_m3[seg]) for seg in segs_ok}
    total_clashes = 0
    bb_tree_now = cKDTree(backbone_xyz)

    for seg in segs_ok:
        xyz = final_m3[seg]
        for i, nbs in enumerate(bb_tree_now.query_ball_point(xyz, CLASH_D)):
            for j in nbs:
                diff = xyz[i] - backbone_xyz[j]
                d = np.linalg.norm(diff)
                if d < 1e-8:
                    diff = np.random.randn(3) * 0.1; d = np.linalg.norm(diff)
                forces[seg][i] += (diff / d) * (CLASH_D - d) / CLASH_D
                total_clashes  += 1

    trees = {s: cKDTree(final_m3[s]) for s in segs_ok}
    for i, seg_a in enumerate(segs_ok):
        for seg_b in segs_ok[i+1:]:
            for ia, nbs in enumerate(trees[seg_b].query_ball_point(final_m3[seg_a], CLASH_D)):
                for ib in nbs:
                    diff  = final_m3[seg_a][ia] - final_m3[seg_b][ib]
                    d     = np.linalg.norm(diff)
                    if d < 1e-8:
                        diff = np.random.randn(3) * 0.1; d = np.linalg.norm(diff)
                    unit  = diff / d
                    depth = (CLASH_D - d) / CLASH_D
                    forces[seg_a][ia] +=  unit * depth
                    forces[seg_b][ib] -= unit * depth
                    total_clashes += 1

    if total_clashes == 0:
        print(f"  Converged at iteration {iteration} — 0 clash contacts")
        break

    for seg in segs_ok:
        f     = forces[seg]
        norms = np.linalg.norm(f, axis=1, keepdims=True)
        mask  = norms.flatten() > 1e-8
        if mask.any():
            f[mask] /= norms[mask]
            f[mask] *= NUDGE_D
            final_m3[seg] += f

    if (iteration + 1) % 25 == 0:
        print(f"  iter {iteration+1:3d}: {total_clashes} contacts")
else:
    print(f"  Max iterations ({MAX_ITER}) reached; {total_clashes} contacts remain")


# Final count
all_f  = np.vstack([final_m3[s] for s in segs_ok])
n_bb_f = sum(len(nb) for nb in cKDTree(backbone_xyz).query_ball_point(all_f, CLASH_D))
rl_f   = [final_m3[s] for s in segs_ok]
n_m3_f = 0
for i in range(len(rl_f)):
    ti = cKDTree(rl_f[i])
    for j in range(i+1, len(rl_f)):
        n_m3_f += sum(len(nb) for nb in ti.query_ball_point(rl_f[j], CLASH_D))
print(f"\nFinal: backbone={n_bb_f}, inter-M3={n_m3_f}, total={n_bb_f+n_m3_f}")


# ── Write PDB ─────────────────────────────────────────────────────────────────

print(f"\nWriting {OUT_PDB} …")
n = 0
with open(OUT_PDB, 'w') as out:
    with open(IN_PDB) as f:
        for line in f:
            if line.startswith("CRYST1"):
                out.write(line)
                break

    for a in backbone:
        n += 1
        out.write(f"{a['line'][:6]}{write_serial(n)}{a['line'][11:]}")

    for seg in HFLK_SEGS:
        if seg not in final_m3:
            continue
        chain_id = SEG_TO_CHAIN[seg]
        xyz_arr  = final_m3[seg]
        for i, a in enumerate(m3_tmpl):
            n += 1
            xyz  = xyz_arr[i]
            line = a['line']
            line = (f"{line[:6]}{write_serial(n)}{line[11:21]}{chain_id}"
                    f"{line[22:30]}{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}"
                    f"{line[54:72]}{seg:<4}{line[76:]}")
            out.write(line)

    out.write("END\n")

print(f"Done: {n} atoms → {OUT_PDB}")
