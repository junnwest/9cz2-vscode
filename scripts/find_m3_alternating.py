#!/usr/bin/env python3
"""
Alternating-angle M3 rotation search + local atom nudge.

Group 1 (HflK ring positions 1,3,5,7,9,11): A, E, I, M, Q, U  → spin θ₁
Group 2 (HflK ring positions 2,4,6,8,10,12): C, G, K, O, S, X → spin θ₂

Every adjacent HflK pair straddles the two groups → different M3 orientations
→ adjacent tails (e.g. E/G, G/I) can no longer entangle.

Tilt fixed at BEST_TILT=-28° (best from prior 2D symmetric search).
Search: θ₁ × θ₂ at SPIN_STEP° resolution → 180×180 = 32,400 combos.

Optimised: backbone + intra-group + inter-group clashes are all pre-computed
per spin angle; the combo loop is pure array lookup + 36 cross-pair sums.

After the search: iterative atom nudge pushes any remaining M3 clash contacts
apart. Bond geometry is slightly distorted, but NAMD minimisation restores it.
"""

import numpy as np
from scipy.spatial import cKDTree
import os, sys

BASE     = "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
IN_PDB   = os.path.join(BASE, "dome_m3_rotated.pdb")
OUT_PDB  = os.path.join(BASE, "dome_m3_alternating.pdb")

HFLK_SEGS    = ['AP1','CP1','EP1','GP1','IP1','KP1','MP1','OP1','QP1','SP1','UP1','XP1']
HFLC_SEGS    = ['BP1','DP1','FP1','HP1','JP1','LP1','NP1','PP1','RP1','TP1','VP1','WP1']
CHAIN_TO_SEG = {'A':'AP1','C':'CP1','E':'EP1','G':'GP1','I':'IP1','K':'KP1',
                'M':'MP1','O':'OP1','Q':'QP1','S':'SP1','U':'UP1','X':'XP1'}
SEG_TO_CHAIN = {v: k for k, v in CHAIN_TO_SEG.items()}

# Alternating groups — every adjacent HflK pair straddles these two groups
GROUP1 = ['AP1','EP1','IP1','MP1','QP1','UP1']   # ring positions 1,3,5,7,9,11
GROUP2 = ['CP1','GP1','KP1','OP1','SP1','XP1']   # ring positions 2,4,6,8,10,12

REF_SEG    = 'IP1'
BEST_TILT  = -28      # degrees; best tilt from prior 2D symmetric search
CLASH_D    = 1.5      # Å — clash threshold
SPIN_STEP  = 2        # degrees
NUDGE_D    = 0.3      # Å per nudge step (proportional to overlap depth)
MAX_ITER   = 150      # max nudge iterations


# ── Utilities ─────────────────────────────────────────────────────────────────

def parse_pdb(path):
    atoms = []
    with open(path) as f:
        for line in f:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            seg      = line[72:76].strip()
            chain_id = line[21]
            try:
                resid = int(line[22:26])
                x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            except ValueError:
                continue
            atoms.append({'seg': seg, 'chain': chain_id, 'resid': resid,
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


def rodrigues(points, axis, angle_deg, pivot):
    k = axis / np.linalg.norm(axis)
    t = np.radians(angle_deg)
    p = points - pivot
    return p * np.cos(t) + np.cross(k, p) * np.sin(t) + k * (p @ k)[:, None] * (1 - np.cos(t)) + pivot


def write_serial(n):
    return f"{n:5d}" if n <= 99999 else f"{n:5x}"


def count_pairs(xyz_a, tree_b, cutoff):
    return sum(len(nb) for nb in tree_b.query_ball_point(xyz_a, cutoff))


# ── Load and partition ────────────────────────────────────────────────────────

all_atoms = parse_pdb(IN_PDB)

backbone = [a for a in all_atoms
            if (a['seg'] in HFLK_SEGS and a['resid'] <= 355)
            or  a['seg'] in HFLC_SEGS]
backbone_xyz = np.array([a['xyz'] for a in backbone])
print(f"Backbone: {len(backbone)} atoms")

ref_chain_id = SEG_TO_CHAIN[REF_SEG]
m3_tmpl = [a for a in all_atoms
           if a['chain'] == ref_chain_id and 356 <= a['resid'] <= 419 and a['seg'] == '']
m3_tmpl_xyz = np.array([a['xyz'] for a in m3_tmpl])
print(f"M3 template (chain {ref_chain_id}): {len(m3_tmpl)} atoms")
if len(m3_tmpl) == 0:
    sys.exit("ERROR: M3 template empty — check chain ID / segname filter")


def ca_range(seg, r0, r1):
    return np.array([a['xyz'] for a in backbone
                     if a['seg'] == seg and a['name'] == 'CA' and r0 <= a['resid'] <= r1])


ref_ca_align  = ca_range(REF_SEG, 350, 355)
dome_centroid = np.array([a['xyz'] for a in backbone if a['name'] == 'CA']).mean(0)


# ── Place M3 on each chain via Kabsch + compute rotation axes ─────────────────

m3_placed = {}    # seg → (N,3) placed M3 coords (before any spin/tilt)
spin_axes = {}    # seg → unit vec (spin axis pointing along M3 extension)
tilt_axes = {}    # seg → unit vec (outward, perp to spin)
pivots    = {}    # seg → (3,) pivot = CA of res 355

for seg in HFLK_SEGS:
    tgt_ca = ca_range(seg, 350, 355)
    if len(tgt_ca) < len(ref_ca_align):
        print(f"  WARNING: {seg} has only {len(tgt_ca)} CA in 350–355, skipping")
        continue
    xyz = m3_tmpl_xyz.copy() if seg == REF_SEG else (lambda R, t: (R @ m3_tmpl_xyz.T).T + t)(*kabsch(ref_ca_align, tgt_ca))
    m3_placed[seg] = xyz

    bb_ca  = ca_range(seg, 350, 355)
    m3_idx = [i for i, a in enumerate(m3_tmpl) if a['name'] == 'CA' and 356 <= a['resid'] <= 363]
    m3_ca_near = xyz[m3_idx] if m3_idx else xyz[:8]
    ax = m3_ca_near.mean(0) - bb_ca.mean(0)
    spin_axes[seg] = ax / np.linalg.norm(ax)

    ca355 = ca_range(seg, 355, 355)
    pivots[seg] = ca355[0] if len(ca355) else bb_ca[-1]

    outward = pivots[seg] - dome_centroid
    perp    = outward - (outward @ spin_axes[seg]) * spin_axes[seg]
    norm_p  = np.linalg.norm(perp)
    if norm_p < 1e-6:
        fb   = np.array([1.0, 0.0, 0.0])
        perp = fb - (fb @ spin_axes[seg]) * spin_axes[seg]
        norm_p = np.linalg.norm(perp)
    tilt_axes[seg] = perp / norm_p

segs_ok = [s for s in HFLK_SEGS if s in m3_placed]
g1 = [s for s in GROUP1 if s in m3_placed]
g2 = [s for s in GROUP2 if s in m3_placed]
print(f"Placed M3 on {len(segs_ok)} chains  (group1={g1}, group2={g2})\n")


# ── Pre-compute all spin positions (tilt fixed at BEST_TILT) ──────────────────

spin_angles = list(range(0, 360, SPIN_STEP))
N_S = len(spin_angles)

print(f"Pre-computing {N_S} spin positions for {len(segs_ok)} chains at tilt={BEST_TILT}° …")
m3_spun = {}   # seg → list[N_S] of (N_atoms, 3)
for seg in segs_ok:
    tilted = rodrigues(m3_placed[seg], tilt_axes[seg], BEST_TILT, pivots[seg])
    m3_spun[seg] = [rodrigues(tilted, spin_axes[seg], s, pivots[seg]) for s in spin_angles]

print(f"  done ({sum(len(v) for v in m3_spun.values())} arrays total)\n")


# ── Pre-compute backbone clash counts per (seg, spin) ─────────────────────────

print("Pre-computing backbone clash counts …")
bb_tree = cKDTree(backbone_xyz)

bb_per = {}   # seg → np.array[N_S]
for seg in segs_ok:
    counts = np.zeros(N_S, dtype=np.int32)
    for si, xyz in enumerate(m3_spun[seg]):
        counts[si] = sum(len(nb) for nb in bb_tree.query_ball_point(xyz, CLASH_D))
    bb_per[seg] = counts
print(f"  done\n")


# ── Pre-compute intra-group clash counts per spin ─────────────────────────────

def intra_clashes(group_segs):
    counts = np.zeros(N_S, dtype=np.int32)
    pairs  = [(i, j) for i in range(len(group_segs)) for j in range(i+1, len(group_segs))]
    for si in range(N_S):
        n = 0
        for ia, ib in pairs:
            ta = cKDTree(m3_spun[group_segs[ia]][si])
            n += count_pairs(m3_spun[group_segs[ib]][si], ta, CLASH_D)
        counts[si] = n
    return counts

print("Pre-computing intra-group clash counts …")
intra_g1 = intra_clashes(g1)
intra_g2 = intra_clashes(g2)
print(f"  done\n")


# ── Pre-compute inter-group cross-clash matrix ────────────────────────────────
# cross[ia, s1, ib, s2] = clashes between g1[ia]@spin_angles[s1] and g2[ib]@spin_angles[s2]

print(f"Pre-computing inter-group cross-clash matrix ({len(g1)}×{N_S}×{len(g2)}×{N_S}) …")
cross = np.zeros((len(g1), N_S, len(g2), N_S), dtype=np.int32)
for ia, seg_a in enumerate(g1):
    for s1i in range(N_S):
        tree_a = cKDTree(m3_spun[seg_a][s1i])
        for ib, seg_b in enumerate(g2):
            for s2i in range(N_S):
                cross[ia, s1i, ib, s2i] = count_pairs(m3_spun[seg_b][s2i], tree_a, CLASH_D)
    print(f"  group1[{ia}] ({seg_a}) done")

# Sum cross over all pairs into a (N_S, N_S) matrix
cross_sum = cross.sum(axis=(0, 2))   # shape (N_S, N_S): total inter-group clashes[s1, s2]
print(f"  done\n")


# ── Pre-compute bb sums per group per spin ────────────────────────────────────

bb_g1 = np.array([sum(bb_per[s][si] for s in g1) for si in range(N_S)], dtype=np.int32)
bb_g2 = np.array([sum(bb_per[s][si] for s in g2) for si in range(N_S)], dtype=np.int32)


# ── Combo search (pure array indexing) ───────────────────────────────────────

print(f"Searching {N_S}×{N_S} = {N_S*N_S} spin combos …")

# total[s1, s2] = bb_g1[s1] + intra_g1[s1] + bb_g2[s2] + intra_g2[s2] + cross_sum[s1, s2]
total_mat = (bb_g1[:, None] + intra_g1[:, None]
           + bb_g2[None, :] + intra_g2[None, :]
           + cross_sum)

best_idx  = np.unravel_index(total_mat.argmin(), total_mat.shape)
best_s1i, best_s2i = best_idx
best_spin1 = spin_angles[best_s1i]
best_spin2 = spin_angles[best_s2i]
best_total = total_mat[best_s1i, best_s2i]
best_bb    = int(bb_g1[best_s1i] + bb_g2[best_s2i])
best_m3    = int(intra_g1[best_s1i] + intra_g2[best_s2i] + cross_sum[best_s1i, best_s2i])

print(f"\nBest: θ₁={best_spin1}° (group1)  θ₂={best_spin2}° (group2)  "
      f"total={best_total}  (backbone={best_bb}, inter-M3={best_m3})\n")

# Top 10 combos
flat = [(total_mat[s1,s2], spin_angles[s1], spin_angles[s2], int(bb_g1[s1]+bb_g2[s2]),
         int(intra_g1[s1]+intra_g2[s2]+cross_sum[s1,s2]))
        for s1 in range(N_S) for s2 in range(N_S)]
flat.sort()
print(f"{'total':>7}  {'θ₁':>5}  {'θ₂':>5}  {'backbone':>9}  {'inter-M3':>9}")
for row in flat[:15]:
    print(f"{row[0]:>7}  {row[1]:>5}  {row[2]:>5}  {row[3]:>9}  {row[4]:>9}")


# ── Build final M3 at best angles ─────────────────────────────────────────────

final_m3 = {}
for seg in g1:
    final_m3[seg] = m3_spun[seg][best_s1i].copy()
for seg in g2:
    final_m3[seg] = m3_spun[seg][best_s2i].copy()

segs_final = [s for s in segs_ok if s in final_m3]


# ── Iterative clash nudge ─────────────────────────────────────────────────────

print(f"\nNudging clashes (cutoff {CLASH_D} Å, step {NUDGE_D} Å × overlap-depth, max {MAX_ITER} iter) …")

for iteration in range(MAX_ITER):
    forces = {seg: np.zeros_like(final_m3[seg]) for seg in segs_final}
    total_clashes = 0

    bb_tree_now = cKDTree(backbone_xyz)

    # M3 vs backbone
    for seg in segs_final:
        xyz = final_m3[seg]
        nbs_list = bb_tree_now.query_ball_point(xyz, CLASH_D)
        for i, nbs in enumerate(nbs_list):
            for j in nbs:
                diff = xyz[i] - backbone_xyz[j]
                d    = np.linalg.norm(diff)
                if d < 1e-8:
                    diff = np.random.randn(3) * 0.1; d = np.linalg.norm(diff)
                # force proportional to overlap depth
                forces[seg][i] += (diff / d) * (CLASH_D - d) / CLASH_D
                total_clashes  += 1

    # M3 vs other M3 chains
    trees = {s: cKDTree(final_m3[s]) for s in segs_final}
    for i, seg_a in enumerate(segs_final):
        for seg_b in segs_final[i+1:]:
            xyz_a = final_m3[seg_a]
            nbs_list = trees[seg_b].query_ball_point(xyz_a, CLASH_D)
            for ia, nbs in enumerate(nbs_list):
                for ib in nbs:
                    diff = xyz_a[ia] - final_m3[seg_b][ib]
                    d    = np.linalg.norm(diff)
                    if d < 1e-8:
                        diff = np.random.randn(3) * 0.1; d = np.linalg.norm(diff)
                    unit = diff / d
                    depth = (CLASH_D - d) / CLASH_D
                    forces[seg_a][ia] +=  unit * depth
                    forces[seg_b][ib] -= unit * depth
                    total_clashes += 1

    if total_clashes == 0:
        print(f"  Converged at iteration {iteration} — 0 clash contacts")
        break

    # Apply forces
    for seg in segs_final:
        f = forces[seg]
        norms = np.linalg.norm(f, axis=1, keepdims=True)
        mask  = norms.flatten() > 1e-8
        if mask.any():
            f[mask] /= norms[mask]
            f[mask] *= NUDGE_D
            final_m3[seg] += f

    if (iteration + 1) % 20 == 0:
        print(f"  iter {iteration+1:3d}: {total_clashes} clash contacts remaining")
else:
    print(f"  Reached max iterations ({MAX_ITER}); {total_clashes} clash contacts remain")

# Final count
all_m3_final = np.vstack([final_m3[s] for s in segs_final])
n_bb_f = sum(len(nb) for nb in cKDTree(backbone_xyz).query_ball_point(all_m3_final, CLASH_D))
rot_list = [final_m3[s] for s in segs_final]
n_m3_f  = 0
for i in range(len(rot_list)):
    ti = cKDTree(rot_list[i])
    for j in range(i+1, len(rot_list)):
        n_m3_f += count_pairs(rot_list[j], ti, CLASH_D)
print(f"\nFinal clash count: backbone={n_bb_f}, inter-M3={n_m3_f}, total={n_bb_f+n_m3_f}")


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

print(f"Done: {n} atoms written → {OUT_PDB}")
