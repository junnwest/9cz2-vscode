#!/usr/bin/env python3
"""
Build each HflK M3 tail (resid 356-419) by SHEARING the placed AF2 coil
along each chain's fan direction, so the end-to-end distance (82 Å) is
preserved and the backbone progresses monotonically along that direction.

For each residue i, the shift is ONLY along target_dir:
    delta_i = (p_ideal_i - p_placed_i) × target_dir

where p_ideal_i is a uniform linear progression from 0 to 82 Å,
and p_placed_i is the current projection of CA_i onto target_dir.

Effect:
  - Intra-residue geometry preserved exactly (translation of whole residue)
  - CA-CA 3D distances preserved (shear doesn't change the transverse component)
  - Inter-residue bonds distorted by at most ~1 Å → NAMD minimisation fixes
  - Chain progresses monotonically → no looping → zero topological entanglement
  - Tips land at Z ≈ -4 Å (above membrane)

target_dir(chain) = normalize(outward_XY × sin(TILT) + [0,0,-1] × cos(TILT))
"""

import numpy as np
from scipy.spatial import cKDTree
import os, sys
from collections import defaultdict

BASE    = "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
IN_PDB  = os.path.join(BASE, "dome_m3_rotated.pdb")
OUT_PDB = os.path.join(BASE, "dome_m3_shear.pdb")

HFLK_SEGS = ['AP1','CP1','EP1','GP1','IP1','KP1','MP1','OP1','QP1','SP1','UP1','XP1']
HFLC_SEGS = ['BP1','DP1','FP1','HP1','JP1','LP1','NP1','PP1','RP1','TP1','VP1','WP1']
FTSH_SEGS = ['0P2','1P2','2P2','3P2','4P2','5P2','6P2','7P2','8P2','9P2','YP1','ZP1']
CHAIN_TO_SEG = {'A':'AP1','C':'CP1','E':'EP1','G':'GP1','I':'IP1','K':'KP1',
                'M':'MP1','O':'OP1','Q':'QP1','S':'SP1','U':'UP1','X':'XP1'}
SEG_TO_CHAIN = {v: k for k, v in CHAIN_TO_SEG.items()}

REF_SEG  = 'IP1'
TILT_DEG = 45.0     # degrees from -Z toward each chain's outward-XY direction
END2END  = 82.0     # Å — target end-to-end (matches AF2 template; tips land ~Z=-4)
CLASH_D  = 1.5
NUDGE_D  = 0.3
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

# Group template atoms by residue order
tmpl_by_resid = defaultdict(list)
for i, a in enumerate(m3_tmpl):
    tmpl_by_resid[a['resid']].append(i)
resid_order = sorted(tmpl_by_resid.keys())
n_res = len(resid_order)
print(f"M3 residues: {resid_order[0]}–{resid_order[-1]}  ({n_res} residues)\n")


def bb_ca(seg, r0, r1):
    return np.array([a['xyz'] for a in backbone
                     if a['seg'] == seg and a['name'] == 'CA' and r0 <= a['resid'] <= r1])


ref_ca_align = bb_ca(REF_SEG, 350, 355)

all_bb_ca = np.array([a['xyz'] for a in backbone if a['name'] == 'CA'])
dome_cen  = all_bb_ca.mean(0)

# Template CA positions and ideal projections (uniform linear, 0 → END2END)
tmpl_ca_idx = [next(i for i in tmpl_by_resid[r] if m3_tmpl[i]['name'] == 'CA')
               for r in resid_order]
tmpl_ca_xyz = m3_tmpl_xyz[tmpl_ca_idx]          # (n_res, 3)
p_ideal     = np.linspace(0.0, END2END, n_res)  # ideal projections along target

tilt_rad = np.radians(TILT_DEG)
DOWN     = np.array([0.0, 0.0, -1.0])


# ── Shear M3 for each chain ───────────────────────────────────────────────────

final_m3 = {}
segs_ok  = []

for seg in HFLK_SEGS:
    tgt_ca = bb_ca(seg, 350, 355)
    if len(tgt_ca) < len(ref_ca_align):
        print(f"  WARNING: {seg} sparse CA 350-355, skipping")
        continue

    # Kabsch placement
    if seg == REF_SEG:
        placed = m3_tmpl_xyz.copy()
    else:
        R_k, t_k = kabsch(ref_ca_align, tgt_ca)
        placed = (R_k @ m3_tmpl_xyz.T).T + t_k

    placed_ca = placed[tmpl_ca_idx]   # (n_res, 3)

    # Per-chain target direction
    ca355_arr = bb_ca(seg, 355, 355)
    pivot     = ca355_arr[0] if len(ca355_arr) else tgt_ca[-1]

    oxy = pivot[:2] - dome_cen[:2]
    oxy_n = np.linalg.norm(oxy)
    if oxy_n < 1e-6:
        oxy = np.array([1.0, 0.0]); oxy_n = 1.0
    out3 = np.array([oxy[0]/oxy_n, oxy[1]/oxy_n, 0.0])
    target = out3 * np.sin(tilt_rad) + DOWN * np.cos(tilt_rad)
    target /= np.linalg.norm(target)

    # Current projections of each placed CA onto target, relative to CA(356)
    ca356_pos = placed_ca[0]
    p_placed  = (placed_ca - ca356_pos) @ target   # (n_res,)

    # Per-residue shift: only along target direction
    shifts = p_ideal - p_placed   # (n_res,)  scalar per residue

    # Apply shift to all atoms of each residue
    new_xyz = placed.copy()
    for ri, resid in enumerate(resid_order):
        shift_vec = shifts[ri] * target
        for idx in tmpl_by_resid[resid]:
            new_xyz[idx] = placed[idx] + shift_vec

    final_m3[seg] = new_xyz
    segs_ok.append(seg)

    tip_z = new_xyz[tmpl_ca_idx[-1]][2]
    az    = np.degrees(np.arctan2(oxy[1], oxy[0]))
    max_shift = np.abs(shifts).max()
    print(f"  {seg}: az={az:+.0f}°  tip_Z={tip_z:.1f}  max_CA_shift={max_shift:.1f} Å")

print(f"\nSheared {len(segs_ok)} chains (TILT={TILT_DEG}°, end-to-end={END2END} Å)\n")

# Verify CA-CA distances after shearing
all_new_ca = np.array([final_m3[seg][tmpl_ca_idx[ri]] for seg in segs_ok
                       for ri in range(n_res)]).reshape(len(segs_ok), n_res, 3)
caca_dists = np.linalg.norm(np.diff(all_new_ca, axis=1), axis=2)
print(f"CA-CA distances after shear: mean={caca_dists.mean():.2f}  "
      f"min={caca_dists.min():.2f}  max={caca_dists.max():.2f} Å\n")


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
