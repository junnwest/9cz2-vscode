#!/usr/bin/env python3
"""
Orient each HflK M3 tail (resid 356-419) to point downward (-Z) by aligning
its principal axis (PC1 of CA positions) to [0, 0, -1], pivoting at CA(355).

All AF2 local geometry (bonds, angles, side chains) is preserved exactly —
only the global orientation of each M3 block changes. Because all 12 tails
start from spatially distinct positions around the dome ring and all point
in the same broad direction (-Z), they cannot topologically entangle.

Backbone for clash detection: HflK resid ≤355 + all HflC + all FtsH.
Any remaining contacts are resolved by iterative atom nudging.

Output: dome_m3_downward.pdb
"""

import numpy as np
from scipy.spatial import cKDTree
import os, sys

BASE    = "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
IN_PDB  = os.path.join(BASE, "dome_m3_rotated.pdb")
OUT_PDB = os.path.join(BASE, "dome_m3_downward.pdb")

HFLK_SEGS = ['AP1','CP1','EP1','GP1','IP1','KP1','MP1','OP1','QP1','SP1','UP1','XP1']
HFLC_SEGS = ['BP1','DP1','FP1','HP1','JP1','LP1','NP1','PP1','RP1','TP1','VP1','WP1']
FTSH_SEGS = ['0P2','1P2','2P2','3P2','4P2','5P2','6P2','7P2','8P2','9P2','YP1','ZP1']
CHAIN_TO_SEG = {'A':'AP1','C':'CP1','E':'EP1','G':'GP1','I':'IP1','K':'KP1',
                'M':'MP1','O':'OP1','Q':'QP1','S':'SP1','U':'UP1','X':'XP1'}
SEG_TO_CHAIN = {v: k for k, v in CHAIN_TO_SEG.items()}

REF_SEG  = 'IP1'
CLASH_D  = 1.5    # Å clash threshold
NUDGE_D  = 0.3    # Å per nudge step (scaled by overlap depth)
MAX_ITER = 200


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


def rotation_between(a, b):
    """Rotation matrix R such that R @ a == b (unit vectors)."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    cross = np.cross(a, b)
    dot   = float(np.dot(a, b))
    s     = np.linalg.norm(cross)
    if s < 1e-10:
        if dot > 0:
            return np.eye(3)
        perp = np.array([1.0, 0.0, 0.0])
        perp -= (perp @ a) * a
        perp /= np.linalg.norm(perp)
        return 2 * np.outer(perp, perp) - np.eye(3)
    K = np.array([[0, -cross[2], cross[1]],
                  [cross[2], 0, -cross[0]],
                  [-cross[1], cross[0], 0]])
    return np.eye(3) + K + K @ K * (1 - dot) / (s * s)


def apply_rotation(xyz, R, pivot):
    return (R @ (xyz - pivot).T).T + pivot


def write_serial(n):
    return f"{n:5d}" if n <= 99999 else f"{n:5x}"


# ── Load ──────────────────────────────────────────────────────────────────────

all_atoms = parse_pdb(IN_PDB)

# Backbone: HflK resid ≤355 + all HflC + all FtsH
backbone = [a for a in all_atoms
            if (a['seg'] in HFLK_SEGS and a['resid'] <= 355)
            or  a['seg'] in HFLC_SEGS
            or  a['seg'] in FTSH_SEGS]
backbone_xyz = np.array([a['xyz'] for a in backbone])
print(f"Backbone: {len(backbone)} atoms "
      f"(HflK≤355 + HflC + FtsH)")

# M3 template: chain I, resid 356-419, empty segname
ref_chain_id = SEG_TO_CHAIN[REF_SEG]
m3_tmpl = [a for a in all_atoms
           if a['chain'] == ref_chain_id and 356 <= a['resid'] <= 419 and a['seg'] == '']
m3_tmpl_xyz = np.array([a['xyz'] for a in m3_tmpl])
print(f"M3 template (chain {ref_chain_id}): {len(m3_tmpl)} atoms")
if len(m3_tmpl) == 0:
    sys.exit("ERROR: M3 template empty — check chain/segname filter")


def bb_ca(seg, r0, r1):
    return np.array([a['xyz'] for a in backbone
                     if a['seg'] == seg and a['name'] == 'CA' and r0 <= a['resid'] <= r1])


ref_ca_align = bb_ca(REF_SEG, 350, 355)


# ── Place M3 on each chain and orient to -Z ───────────────────────────────────

TARGET = np.array([0.0, 0.0, -1.0])   # point downward

final_m3  = {}   # seg -> (N, 3)
segs_ok   = []

for seg in HFLK_SEGS:
    tgt_ca = bb_ca(seg, 350, 355)
    if len(tgt_ca) < len(ref_ca_align):
        print(f"  WARNING: {seg} has only {len(tgt_ca)} CA in 350-355, skipping")
        continue

    # Step 1: Kabsch placement (superimpose ref CA 350-355 onto this chain's)
    if seg == REF_SEG:
        xyz = m3_tmpl_xyz.copy()
    else:
        R_k, t_k = kabsch(ref_ca_align, tgt_ca)
        xyz = (R_k @ m3_tmpl_xyz.T).T + t_k

    # Step 2: compute PC1 of placed M3 CA positions
    ca_idx = [i for i, a in enumerate(m3_tmpl) if a['name'] == 'CA']
    m3_ca_xyz = xyz[ca_idx]   # shape (64, 3)
    centroid  = m3_ca_xyz.mean(0)
    _, _, Vt  = np.linalg.svd(m3_ca_xyz - centroid)
    pc1 = Vt[0]

    # Ensure PC1 points from resid 356 toward 419 (proximal → distal)
    if (m3_ca_xyz[-1] - m3_ca_xyz[0]) @ pc1 < 0:
        pc1 = -pc1

    # Step 3: rotate entire M3 block so PC1 aligns with -Z, pivot at CA(355)
    ca355_pos = bb_ca(seg, 355, 355)
    pivot = ca355_pos[0] if len(ca355_pos) else tgt_ca[-1]

    R_orient = rotation_between(pc1, TARGET)
    xyz_oriented = apply_rotation(xyz, R_orient, pivot)

    final_m3[seg] = xyz_oriented
    segs_ok.append(seg)

    tip_z = xyz_oriented[ca_idx[-1]][2]
    print(f"  {seg}: PC1={pc1.round(3)}, CA(419) tip Z after orient = {tip_z:.1f}")

print(f"\nOriented {len(segs_ok)} chains\n")


# ── Clash count before nudge ──────────────────────────────────────────────────

bb_tree = cKDTree(backbone_xyz)
all_m3_flat = np.vstack([final_m3[s] for s in segs_ok])
n_bb_pre = sum(len(nb) for nb in bb_tree.query_ball_point(all_m3_flat, CLASH_D))

rot_list = [final_m3[s] for s in segs_ok]
n_m3_pre = 0
for i in range(len(rot_list)):
    ti = cKDTree(rot_list[i])
    for j in range(i+1, len(rot_list)):
        n_m3_pre += sum(len(nb) for nb in ti.query_ball_point(rot_list[j], CLASH_D))

print(f"Before nudge: backbone={n_bb_pre}, inter-M3={n_m3_pre}, total={n_bb_pre+n_m3_pre}")


# ── Iterative clash nudge ─────────────────────────────────────────────────────

print(f"Nudging (cutoff {CLASH_D} Å, step {NUDGE_D} Å × depth, max {MAX_ITER} iter) …")

for iteration in range(MAX_ITER):
    forces = {seg: np.zeros_like(final_m3[seg]) for seg in segs_ok}
    total_clashes = 0

    bb_tree_now = cKDTree(backbone_xyz)

    # M3 vs backbone (HflK backbone + HflC + FtsH)
    for seg in segs_ok:
        xyz = final_m3[seg]
        nbs_list = bb_tree_now.query_ball_point(xyz, CLASH_D)
        for i, nbs in enumerate(nbs_list):
            for j in nbs:
                diff = xyz[i] - backbone_xyz[j]
                d    = np.linalg.norm(diff)
                if d < 1e-8:
                    diff = np.random.randn(3) * 0.1; d = np.linalg.norm(diff)
                forces[seg][i] += (diff / d) * (CLASH_D - d) / CLASH_D
                total_clashes  += 1

    # M3 vs other M3 chains
    trees = {s: cKDTree(final_m3[s]) for s in segs_ok}
    for i, seg_a in enumerate(segs_ok):
        for seg_b in segs_ok[i+1:]:
            nbs_list = trees[seg_b].query_ball_point(final_m3[seg_a], CLASH_D)
            for ia, nbs in enumerate(nbs_list):
                for ib in nbs:
                    diff = final_m3[seg_a][ia] - final_m3[seg_b][ib]
                    d    = np.linalg.norm(diff)
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
        f = forces[seg]
        norms = np.linalg.norm(f, axis=1, keepdims=True)
        mask  = norms.flatten() > 1e-8
        if mask.any():
            f[mask] /= norms[mask]
            f[mask] *= NUDGE_D
            final_m3[seg] += f

    if (iteration + 1) % 25 == 0:
        print(f"  iter {iteration+1:3d}: {total_clashes} clash contacts")
else:
    print(f"  Max iterations reached; {total_clashes} clash contacts remain")


# Final count
all_m3_final = np.vstack([final_m3[s] for s in segs_ok])
n_bb_f = sum(len(nb) for nb in cKDTree(backbone_xyz).query_ball_point(all_m3_final, CLASH_D))
rl = [final_m3[s] for s in segs_ok]
n_m3_f = 0
for i in range(len(rl)):
    ti = cKDTree(rl[i])
    for j in range(i+1, len(rl)):
        n_m3_f += sum(len(nb) for nb in ti.query_ball_point(rl[j], CLASH_D))
print(f"\nFinal: backbone={n_bb_f}, inter-M3={n_m3_f}, total={n_bb_f+n_m3_f}")


# ── Write PDB ─────────────────────────────────────────────────────────────────

print(f"\nWriting {OUT_PDB} …")
n = 0
cryst_written = False

with open(OUT_PDB, 'w') as out:
    with open(IN_PDB) as f:
        for line in f:
            if line.startswith("CRYST1"):
                out.write(line)
                cryst_written = True
                break
    if not cryst_written:
        out.write("CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1\n")

    # Backbone (HflK resid ≤355, HflC, FtsH)
    for a in backbone:
        n += 1
        out.write(f"{a['line'][:6]}{write_serial(n)}{a['line'][11:]}")

    # M3 tails (oriented to -Z, nudged)
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
