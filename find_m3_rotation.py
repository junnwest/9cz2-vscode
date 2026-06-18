#!/usr/bin/env python3
"""
2D rigid-body rotation search for M3 (residues 356-419) of AF2 HflK.

Searches spin (0-355°, step 5°) × tilt (-60 to +60°, step 5°) around
the 355-356 hinge and picks the combination minimising total heavy-atom
clashes across all 12 HflK superimposition sites in the dome.

Usage:
    python find_m3_rotation.py <rajiv.pdb> <af2_hflk.pdb> <output.pdb>
"""

import sys
import numpy as np

HFLK_SEGNAMES = ['AP1','CP1','EP1','GP1','IP1','KP1',
                 'MP1','OP1','QP1','SP1','UP1','XP1']
HFLK_CHAINS   = ['A','C','E','G','I','K','M','O','Q','S','U','X']
ALIGN_RESID   = (79, 355)
M3_START      = 356
CLASH_DIST    = 2.0    # Å, heavy-atom clash threshold
SPIN_STEP     = 5      # degrees
TILT_STEP     = 5      # degrees
TILT_RANGE    = 60     # ± degrees


def is_heavy(name):
    return name.strip()[0] != 'H'


def parse_pdb(path):
    atoms = []
    with open(path) as f:
        for line in f:
            if not line.startswith(('ATOM', 'HETATM')):
                continue
            atoms.append({
                'line':    line,
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
                'heavy':   is_heavy(line[12:16]),
            })
    return atoms


def kabsch(P, Q):
    cP, cQ = P.mean(0), Q.mean(0)
    H = (P - cP).T @ (Q - cQ)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    t = cQ - cP @ R.T
    return R, t


def rodrigues(axis, angle_deg):
    a = np.radians(angle_deg)
    u = axis / np.linalg.norm(axis)
    K = np.array([[0, -u[2], u[1]],
                  [u[2], 0, -u[0]],
                  [-u[1], u[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


def count_clashes_batched(m3_xyz, ref_xyz, threshold=CLASH_DIST):
    """Count M3 heavy atoms that clash with any ref heavy atom."""
    if len(ref_xyz) == 0 or len(m3_xyz) == 0:
        return 0
    # Chunk over ref to avoid huge memory allocation
    clash_mask = np.zeros(len(m3_xyz), dtype=bool)
    chunk = 2000
    for i in range(0, len(ref_xyz), chunk):
        r = ref_xyz[i:i+chunk]
        diff = m3_xyz[:, None, :] - r[None, :, :]   # (M3, chunk, 3)
        d2 = (diff**2).sum(axis=2)                    # (M3, chunk)
        clash_mask |= (d2 < threshold**2).any(axis=1)
        if clash_mask.all():
            break
    return int(clash_mask.sum())


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    rajiv_pdb, af2_pdb, out_pdb = sys.argv[1], sys.argv[2], sys.argv[3]

    print("Parsing structures...")
    rajiv = parse_pdb(rajiv_pdb)
    af2   = parse_pdb(af2_pdb)

    # ── AF2 heavy atoms ──────────────────────────────────────────────────────
    af2_heavy = [a for a in af2 if a['heavy']]
    af2_H     = [a for a in af2 if not a['heavy']]

    af2_xyz = np.array([[a['x'], a['y'], a['z']] for a in af2_heavy])

    m3_mask    = np.array([a['resid'] >= M3_START        for a in af2_heavy])
    align_mask = np.array([a['name'].strip() == 'CA' and
                            ALIGN_RESID[0] <= a['resid'] <= ALIGN_RESID[1]
                            for a in af2_heavy])

    af2_ca_xyz    = af2_xyz[align_mask]
    af2_ca_resids = [a['resid'] for a, ok in zip(af2_heavy, align_mask) if ok]

    # ── Rajiv: non-HflK heavy atoms for clash reference ─────────────────────
    ref_nonhflk_xyz = np.array([[a['x'], a['y'], a['z']] for a in rajiv
                                 if a['heavy'] and a['segname'] not in HFLK_SEGNAMES])
    print(f"  Non-HflK heavy atoms for clash detection: {len(ref_nonhflk_xyz)}")

    # ── Rajiv: per-chain CA coords for alignment ─────────────────────────────
    rajiv_chains = {}
    for seg in HFLK_SEGNAMES:
        ca_map = {a['resid']: np.array([a['x'], a['y'], a['z']])
                  for a in rajiv
                  if a['segname'] == seg and a['name'].strip() == 'CA'
                  and ALIGN_RESID[0] <= a['resid'] <= ALIGN_RESID[1]}
        rajiv_chains[seg] = ca_map

    # Precompute Kabsch transforms for each chain (based on UNROTATED AF2)
    transforms = {}
    for seg in HFLK_SEGNAMES:
        ref_map = rajiv_chains[seg]
        common = sorted(set(af2_ca_resids) & set(ref_map))
        P = np.array([af2_ca_xyz[af2_ca_resids.index(r)] for r in common])
        Q = np.array([ref_map[r] for r in common])
        R, t = kabsch(P, Q)
        transforms[seg] = (R, t, len(common))
        print(f"  {seg}: {len(common)} alignment CAs")

    # ── Rotation hinge ────────────────────────────────────────────────────────
    ca_coords = {a['resid']: np.array([a['x'], a['y'], a['z']])
                 for a in af2_heavy if a['name'].strip() == 'CA'}

    pivot = ca_coords.get(355, ca_coords.get(354, ca_coords.get(353)))
    pre_m3  = np.array([ca_coords[r] for r in range(348, 356) if r in ca_coords])
    post_m3 = np.array([ca_coords[r] for r in range(356, 364) if r in ca_coords])
    if len(pre_m3) == 0 or len(post_m3) == 0:
        print("ERROR: cannot find CA atoms near the 355/356 hinge")
        sys.exit(1)

    # Spin axis: along the chain direction at the hinge
    spin_axis = post_m3.mean(0) - pre_m3.mean(0)
    spin_axis /= np.linalg.norm(spin_axis)

    # Tilt axis: perpendicular to spin, in the plane with global Z
    perp = np.array([0, 0, 1]) - np.dot(np.array([0, 0, 1]), spin_axis) * spin_axis
    if np.linalg.norm(perp) < 1e-6:
        perp = np.array([1, 0, 0]) - np.dot(np.array([1, 0, 0]), spin_axis) * spin_axis
    tilt_axis = perp / np.linalg.norm(perp)

    print(f"\nSpin axis: {spin_axis}")
    print(f"Tilt axis: {tilt_axis}")

    # ── 2D grid search ────────────────────────────────────────────────────────
    spins  = list(range(0, 360, SPIN_STEP))
    tilts  = list(range(-TILT_RANGE, TILT_RANGE + 1, TILT_STEP))
    total_combos = len(spins) * len(tilts)
    print(f"\nSearching {len(spins)} spin × {len(tilts)} tilt = {total_combos} combinations...")

    base_xyz   = af2_xyz.copy()
    best_score = 10**9
    best_spin  = 0
    best_tilt  = 0
    results    = {}

    for spin in spins:
        R_spin = rodrigues(spin_axis, spin)
        for tilt in tilts:
            R_tilt = rodrigues(tilt_axis, tilt)
            Rot = R_tilt @ R_spin  # apply spin first, then tilt

            xyz = base_xyz.copy()
            m3_c = xyz[m3_mask] - pivot
            xyz[m3_mask] = m3_c @ Rot.T + pivot

            total_clashes = 0
            for seg in HFLK_SEGNAMES:
                R_k, t_k, _ = transforms[seg]
                m3_t = xyz[m3_mask] @ R_k.T + t_k
                m3_min = m3_t.min(0) - 15
                m3_max = m3_t.max(0) + 15
                in_box = np.all((ref_nonhflk_xyz >= m3_min) &
                                (ref_nonhflk_xyz <= m3_max), axis=1)
                total_clashes += count_clashes_batched(m3_t, ref_nonhflk_xyz[in_box])

            results[(spin, tilt)] = total_clashes
            if total_clashes < best_score:
                best_score = total_clashes
                best_spin  = spin
                best_tilt  = tilt
                print(f"  New best — spin {spin:3d}°, tilt {tilt:+3d}°: {total_clashes} clashes")

    print(f"\nBest: spin {best_spin}°, tilt {best_tilt:+d}° → {best_score} total clashes across 12 chains")

    # ── Apply best rotation and write output ─────────────────────────────────
    R_spin_best = rodrigues(spin_axis, best_spin)
    R_tilt_best = rodrigues(tilt_axis, best_tilt)
    Rot_best    = R_tilt_best @ R_spin_best

    all_xyz = np.array([[a['x'], a['y'], a['z']] for a in af2])
    all_m3  = np.array([a['resid'] >= M3_START for a in af2])
    all_xyz_rotated = all_xyz.copy()
    m3_c = all_xyz[all_m3] - pivot
    all_xyz_rotated[all_m3] = m3_c @ Rot_best.T + pivot

    print(f"\nWriting {out_pdb}...")
    with open(out_pdb, 'w') as f:
        for i, (a, xyz) in enumerate(zip(af2, all_xyz_rotated)):
            line = (
                f"{'ATOM':<6}{i+1:5d} {a['name']}{a['altloc']}"
                f"{a['resname']} {a['chain']}{a['resid']:4d}{a['icode']}"
                f"   {xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}"
                f"{a['occ']}{a['bfac']}      "
                f"{a['segname']:<4}\n"
            )
            f.write(line)
        f.write("END\n")
    print("Done.")


if __name__ == '__main__':
    main()
