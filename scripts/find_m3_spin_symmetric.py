#!/usr/bin/env python3
"""
Symmetric 2D M3 rotation search (spin × tilt).

Finds a single (spin, tilt) pair applied uniformly to all 12 HflK M3 tails
(resid 356-419) that minimises total clashes (M3 vs dome backbone + inter-M3).

Strategy:
  - Reference dome backbone: HflK resid 79-355 + all HflC from dome_m3_rotated.pdb
    (Rajiv's original structure; M3-region atoms filtered out)
  - M3 template: chain I (IP1) M3 atoms already in dome coordinate frame
  - For each other HflK chain: place canonical M3 by Kabsch superimposition of
    chain I CA(350-355) onto that chain's CA(350-355), then apply same transform
    to M3 template → symmetric starting orientation for all chains
  - Spin axis: centroid(CA 350-355) → centroid(CA 356-363) per chain
  - Tilt axis: outward from dome centroid, projected perp to spin axis per chain
    (positive tilt = lean M3 away from dome centre → reduces inter-M3 crowding)
  - Grid: spin 0-358° (2° step) × tilt -60° to +60° (2° step) = 10,980 combos
  - Precompute tilt-only positions (61 tilt angles) then spin over each → fast
  - Clash metric: heavy-atom distance < 1.5 Å (M3 vs backbone AND inter-M3)

Output: dome_m3_symmetric.pdb + clash profile printed to stdout
"""

import numpy as np
from scipy.spatial import cKDTree
import os

BASE    = "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
IN_PDB  = os.path.join(BASE, "dome_m3_rotated.pdb")
OUT_PDB = os.path.join(BASE, "dome_m3_symmetric.pdb")

HFLK_SEGS = ['AP1','CP1','EP1','GP1','IP1','KP1','MP1','OP1','QP1','SP1','UP1','XP1']
HFLC_SEGS = ['BP1','DP1','FP1','HP1','JP1','LP1','NP1','PP1','RP1','TP1','VP1','WP1']
CHAIN_TO_SEG = {'A':'AP1','C':'CP1','E':'EP1','G':'GP1','I':'IP1','K':'KP1',
                'M':'MP1','O':'OP1','Q':'QP1','S':'SP1','U':'UP1','X':'XP1'}
SEG_TO_CHAIN = {v: k for k, v in CHAIN_TO_SEG.items()}
REF_SEG  = 'IP1'   # most constrained (highest non-M3 atom density at CA-355)
CLASH_D   = 1.5    # Angstroms
SPIN_STEP = 2      # degrees
TILT_STEP = 2      # degrees
TILT_MAX  = 60     # degrees


# ── Utilities ──────────────────────────────────────────────────────────────────

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
            atoms.append({
                'seg': seg, 'chain': chain_id, 'resid': resid,
                'name': line[12:16].strip(),
                'xyz':  np.array([x, y, z]),
                'line': line,
            })
    return atoms


def kabsch(P, Q):
    """R, t such that R @ P[i] + t ≈ Q[i] (least-squares)."""
    p0, q0 = P.mean(0), Q.mean(0)
    Pc, Qc = P - p0, Q - q0
    U, _, Vt = np.linalg.svd(Pc.T @ Qc)
    d = np.linalg.det(Vt.T @ U.T)
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, q0 - R @ p0


def rodrigues(points, axis, angle_deg, pivot):
    """Rigid rotation of (N,3) points around unit axis about pivot."""
    k = axis / np.linalg.norm(axis)
    t = np.radians(angle_deg)
    p = points - pivot
    rot = p * np.cos(t) + np.cross(k, p) * np.sin(t) + k * (p @ k)[:, None] * (1 - np.cos(t))
    return rot + pivot


def count_clashes(A, B, cutoff=CLASH_D):
    if len(A) == 0 or len(B) == 0:
        return 0
    tree = cKDTree(B)
    return sum(len(nb) for nb in tree.query_ball_point(A, cutoff))


def write_serial(n):
    return f"{n:5d}" if n <= 99999 else f"{n:5x}"


# ── Load and partition atoms ───────────────────────────────────────────────────

all_atoms = parse_pdb(IN_PDB)

# Dome backbone: HflK resid 79-355 (by segname) + all HflC (by segname)
backbone = [a for a in all_atoms
            if (a['seg'] in HFLK_SEGS and a['resid'] <= 355)
            or  a['seg'] in HFLC_SEGS]
backbone_xyz = np.array([a['xyz'] for a in backbone])
print(f"Backbone: {len(backbone)} atoms")

# M3 template: chain I, resid 356-419, empty segname
ref_chain_id = SEG_TO_CHAIN[REF_SEG]   # 'I'
m3_tmpl = [a for a in all_atoms
           if a['chain'] == ref_chain_id and 356 <= a['resid'] <= 419 and a['seg'] == '']
m3_tmpl_xyz = np.array([a['xyz'] for a in m3_tmpl])
print(f"M3 template (chain {ref_chain_id}): {len(m3_tmpl)} atoms")
if len(m3_tmpl) == 0:
    raise RuntimeError("M3 template empty — check chain ID / segname filter")


def ca_range(seg, r0, r1):
    return np.array([a['xyz'] for a in backbone
                     if a['seg'] == seg and a['name'] == 'CA' and r0 <= a['resid'] <= r1])


ref_ca_align = ca_range(REF_SEG, 350, 355)   # 6 CA atoms for Kabsch

# ── Place M3 on each chain via Kabsch ─────────────────────────────────────────

m3_placed  = {}   # seg -> (N,3)
spin_axes  = {}   # seg -> unit vec
tilt_axes  = {}   # seg -> unit vec (outward, perp to spin)
pivots     = {}   # seg -> (3,)

dome_centroid = np.array([a['xyz'] for a in backbone if a['name'] == 'CA']).mean(0)

for seg in HFLK_SEGS:
    tgt_ca_align = ca_range(seg, 350, 355)
    if len(tgt_ca_align) < len(ref_ca_align):
        print(f"  WARNING: {seg} only has {len(tgt_ca_align)} CA in 350-355, skipping")
        continue

    if seg == REF_SEG:
        xyz = m3_tmpl_xyz.copy()
    else:
        R, t = kabsch(ref_ca_align, tgt_ca_align)
        xyz = (R @ m3_tmpl_xyz.T).T + t

    m3_placed[seg] = xyz

    bb_ca = ca_range(seg, 350, 355)
    m3_ca_idx = [i for i, a in enumerate(m3_tmpl)
                 if a['name'] == 'CA' and 356 <= a['resid'] <= 363]
    m3_ca_near = xyz[m3_ca_idx] if m3_ca_idx else xyz[:8]
    ax = m3_ca_near.mean(0) - bb_ca.mean(0)
    spin_ax = ax / np.linalg.norm(ax)
    spin_axes[seg] = spin_ax

    ca355 = ca_range(seg, 355, 355)
    piv = ca355[0] if len(ca355) else bb_ca[-1]
    pivots[seg] = piv

    # Tilt axis: outward from dome centroid, projected perp to spin axis
    outward = piv - dome_centroid
    outward_perp = outward - (outward @ spin_ax) * spin_ax
    norm_op = np.linalg.norm(outward_perp)
    if norm_op < 1e-6:
        fallback = np.array([1.0, 0.0, 0.0])
        outward_perp = fallback - (fallback @ spin_ax) * spin_ax
        norm_op = np.linalg.norm(outward_perp)
    tilt_axes[seg] = outward_perp / norm_op

print(f"Placed M3 on {len(m3_placed)} / {len(HFLK_SEGS)} chains\n")

# ── 2D spin × tilt search ──────────────────────────────────────────────────────

spin_angles = list(range(0, 360, SPIN_STEP))
tilt_angles = list(range(-TILT_MAX, TILT_MAX + 1, TILT_STEP))
segs_ok     = list(m3_placed.keys())
n_combos    = len(spin_angles) * len(tilt_angles)
print(f"2D search: {len(spin_angles)} spin × {len(tilt_angles)} tilt = {n_combos} combos, "
      f"clash cutoff {CLASH_D} Å …")

# Pre-compute tilt-only M3 positions (avoids recomputing tilt inside spin loop)
m3_tilted = {}   # seg -> list[tilt_idx] -> (N,3)
for seg in segs_ok:
    m3_tilted[seg] = [
        rodrigues(m3_placed[seg], tilt_axes[seg], tilt, pivots[seg])
        for tilt in tilt_angles
    ]

bb_tree = cKDTree(backbone_xyz)

profile = []   # (tilt, spin, total, bb, m3m3)

for ti, tilt in enumerate(tilt_angles):
    for spin in spin_angles:
        rot_list = [rodrigues(m3_tilted[seg][ti], spin_axes[seg], spin, pivots[seg])
                    for seg in segs_ok]

        all_m3 = np.vstack(rot_list)
        n_bb   = sum(len(nb) for nb in bb_tree.query_ball_point(all_m3, CLASH_D))

        n_m3 = 0
        for i in range(len(rot_list)):
            tree_i = cKDTree(rot_list[i])
            for j in range(i + 1, len(rot_list)):
                n_m3 += sum(len(nb) for nb in tree_i.query_ball_point(rot_list[j], CLASH_D))

        profile.append((tilt, spin, n_bb + n_m3, n_bb, n_m3))

best = min(profile, key=lambda x: x[2])
print(f"\nBest: tilt={best[0]}°  spin={best[1]}°  "
      f"total={best[2]}  (backbone={best[3]}, inter-M3={best[4]})\n")

print(f"{'tilt':>5}  {'spin':>5}  {'total':>6}  {'backbone':>9}  {'inter-M3':>9}")
for row in sorted(profile, key=lambda x: x[2])[:15]:
    print(f"{row[0]:>5}  {row[1]:>5}  {row[2]:>6}  {row[3]:>9}  {row[4]:>9}")

# ── Write output PDB ───────────────────────────────────────────────────────────

best_tilt, best_spin = best[0], best[1]
print(f"\nWriting {OUT_PDB} (tilt={best_tilt}°, spin={best_spin}°) …")

ti_best = tilt_angles.index(best_tilt)
final_m3 = {seg: rodrigues(m3_tilted[seg][ti_best], spin_axes[seg], best_spin, pivots[seg])
            for seg in segs_ok}

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
            line = f"{line[:6]}{write_serial(n)}{line[11:21]}{chain_id}{line[22:30]}{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{line[54:72]}{seg:<4}{line[76:]}"
            out.write(line)

    out.write("END\n")

print(f"Done: {n} atoms written")
