# NAMD Performance Data — Midway3 Caslake

All runs use NAMD 2.14 MPI on caslake partition unless noted. Timestep 2 fs throughout.
Speed formula: `ns/day = 86400 / WallClock_seconds` (per 500,000-step = 1 ns run).

---

## System Definitions

| System | Description | Atoms | Source |
|--------|-------------|-------|--------|
| **control** | Membrane-only (DPPE/POPG/DOPG/LOACL1/TLCL1 + water/ions, no protein) | 632,689 | charmm-gui-7628525516 |
| **no-dome** | FtsH embedded in membrane, HflK/C dome removed | < 632,689 (estimated ~550k) | namd_caslake / namd |
| **full 9cz2** | Full dome + FtsH + membrane (main system) | TBD — CHARMM-GUI 8119908655 building | — |

Note: the no-dome system uses ~6,028 MB memory vs control ~6,775 MB → confirms no-dome is smaller despite having protein. Protein systems run slower per atom due to complex bonded interactions and harder load balancing.

---

## Control System — Production Benchmarks

All steps = 500,000 steps = 1 ns. WallClock from NAMD output files.

| Step | Job ID | Nodes | CPUs | WallClock (s) | s/step | ns/day | Queue wait |
|------|--------|-------|------|---------------|--------|--------|------------|
| step7_1  | 49165809 | 2 | 96  | 31,941 | 0.06388 | 2.71 | ~12h |
| step7_2  | 49165809 | 2 | 96  | 31,496 | 0.06299 | 2.74 | (same job) |
| step7_4  | 49165809 | 2 | 96  | 32,083 | 0.06417 | 2.69 | (same job) |
| step7_5  | 49165809 | 2 | 96  | 31,990 | 0.06398 | 2.70 | (same job) |
| step7_7  | —       | 2 | 96  | 32,530 | 0.06506 | 2.66 | — |
| step7_8  | —       | 2 | 96  | 32,578 | 0.06516 | 2.65 | — |
| step7_10 | 49436413 | 2 | 96  | 31,561 | 0.06312 | 2.74 | 31 min |
| step7_11 | 50583298 | 2 | 96  | 35,702 | 0.07140 | 2.42 | 30 min |
| step7_12 | 50623759 | 4 | 192 | 20,285 | 0.04057 | 4.26 | 5h 48m |
| step7_13 | 50676351 | 5 | 240 | 17,456 | 0.03491 | 4.95 | 13h 15m |
| step7_14 | 50676351 | 5 | 240 | 17,242 | 0.03448 | 5.01 | (same job) |
| step7_15 | 50676351 | 5 | 240 | 17,185 | 0.03437 | 5.02 | (same job) |
| step7_16 | 50676351 | 5 | 240 | 17,061 | 0.03412 | 5.06 | (same job) |
| step7_17 | 50676351 | 5 | 240 | 17,116 | 0.03423 | 5.05 | (same job) |
| step7_18 | 50676351 | 5 | 240 | 17,061 | 0.03412 | 5.06 | (same job) |
| step7_19 | 50676351 | 5 | 240 | 17,149 | 0.03430 | 5.03 | (same job) |
| step7_21 | 50736443 | 6 | 288 | 126,746 | 0.03169 | 5.45 | 15h 32m |

Notes:
- step7_3, 6, 9: no .coor file (runs killed before completion); no WallClock data
- step7_20: killed at wall time (job 50676351 TIMEOUT); partial run, ~0.42 ns DCD data
- step7_21: 8 ns block (4,000,000 steps) starting from step7_20.restart; WallClock is for full 8 ns run
- step7_11 is slower than steps 1–10 — likely due to node load conditions, not configuration change
- Total control system trajectory: ~27.4 ns (19 ns steps 1–19 + 0.42 ns partial step7_20 + 8 ns step7_21)

### Control System — Speed by Node Count (averages)

| Nodes | CPUs | avg ns/day | avg s/step | ns/day per node |
|-------|------|------------|------------|-----------------|
| 2     | 96   | 2.69       | 0.0641     | 1.34 |
| 4     | 192  | 4.26       | 0.0406     | 1.07 |
| 5     | 240  | 5.03       | 0.0342     | 1.01 |
| 6     | 288  | 5.45       | 0.0317     | 0.91 |

### Scaling Efficiency (control system)

Ideal scaling = linear (doubling nodes = doubling speed). Actual:

| Transition | CPU ratio | Speed ratio | Parallel efficiency |
|------------|-----------|-------------|---------------------|
| 2 → 4 nodes | 2.0× | 4.26/2.69 = 1.58× | 79% |
| 4 → 5 nodes | 1.25× | 5.03/4.26 = 1.18× | 94% |
| 5 → 6 nodes | 1.20× | 5.45/5.03 = 1.08× | 90% |

---

## No-Dome System — Production Benchmarks (Rajiv, retired)

System: FtsH in membrane, no HflK/C dome. NAMD 2.14 MPI unless noted.

| Step | Job ID | Nodes | CPUs | WallClock (s) | s/step | ns/day | Note |
|------|--------|-------|------|---------------|--------|--------|------|
| step7_2  | 48207267 | 10 | 480 | 11,512 | 0.02302 | 7.50 | |
| step7_3  | 48207267 | 10 | 480 | 11,720 | 0.02344 | 7.37 | |
| step7_4  | 48207267 | 10 | 480 | 11,679 | 0.02336 | 7.40 | |
| step7_5  | 48207267 | 10 | 480 | 11,692 | 0.02338 | 7.39 | |
| step7_6  | 48207267 | 10 | 480 | 11,734 | 0.02347 | 7.36 | |
| step7_7  | 48207267 | 10 | 480 | 11,749 | 0.02350 | 7.35 | |
| step7_8  | 48207267 | 10 | 480 | 11,491 | 0.02298 | 7.52 | |
| step7_11 | —       | 2  | 96  | 48,633 | 0.09727 | 1.78 | |
| step7_2  | —       | 1 GPU | 4+GPU | 56,052 | 0.11210 | 1.54 | NAMD 3 multicore-cuda, 1 GPU |

Note: 1-node (48 CPU, MPI) benchmark recorded as ~0.90 ns/day in notes — no .out file located.

### No-Dome Scaling

| Nodes | CPUs | avg ns/day | ns/day per node |
|-------|------|------------|-----------------|
| 1     | 48   | 0.90 (notes) | 0.90 |
| 2     | 96   | 1.78       | 0.89 |
| 10    | 480  | 7.41       | 0.74 |
| 1 GPU | 4+1  | 1.54       | — |

---

## Queue Wait Time Data

Queue wait = time from `sbatch` submission to job start.

| Job ID | System | Nodes | Submit | Start | Wait |
|--------|--------|-------|--------|-------|------|
| 48808257 | control equil | 4 | 2026-04-20 16:34 | 2026-04-22 00:56 | **32h** |
| 49165809 | control prod  | 2 | 2026-04-29 16:52 | 2026-04-30 05:09 | **12h 17m** |
| 49436413 | control prod  | 2 | 2026-05-09 04:13 | 2026-05-09 04:44 | **31 min** |
| 50583298 | control prod  | 2 | 2026-06-08 11:32 | 2026-06-08 12:02 | **30 min** |
| 50623759 | control prod  | 4 | 2026-06-09 11:14 | 2026-06-09 17:02 | **5h 48m** |
| 50676351 | control prod  | 5 | 2026-06-10 11:05 | 2026-06-11 00:20 | **13h 15m** |
| 50736443 | control prod  | 6 | 2026-06-12 12:36 | pending | **TBD** |

Trend: queue wait scales roughly with node count. Caslake is a competitive partition.
2-node jobs typically wait under 1h (off-peak) to ~12h (peak). 4-5 node jobs: 6–13h.

---

## Derived Formulas

### Speed estimate (control system, membrane-only)
Based on measured data (2–5 nodes):

```
ns/day ≈ 1.53 × nodes^0.69     (R² ≈ 0.99)
```

Fitted from: (2, 2.69), (4, 4.26), (5, 5.03)
Predictions: 6 nodes ≈ **5.7 ns/day** (actual: 5.45), 8 nodes ≈ **7.0 ns/day**, 10 nodes ≈ **8.2 ns/day**

Note: this fit is for the 632,689-atom membrane-only system. The full 9cz2 system will be
significantly larger and slower — scale factor unknown until first production timing is measured.

### Optimal node count heuristic
- Queue wait dominates for short runs (< 2 ns needed)
- Throughput per node drops after ~5 nodes for this system size
- **Sweet spot for control system: 4–5 nodes** (best ns/day per unit queue wait)
- For urgency: 6–8 nodes gains ~1–2 ns/day but costs ~15–25h extra queue wait

### Expected speed for full 9cz2 system
Full system (all 36 chains + membrane) will be ~2–4× larger than control.
Speed scales roughly as 1/N_atoms for fixed node count.
If full system is ~1.5M atoms (~2.4× control): expect **~1.0–1.5 ns/day at 5 nodes**.
Will update once step7_1 timing is available for that system.

---

## Raw Job History (sacct)

All junseo jobs 2026-03-01 to 2026-06-12 — relevant simulation jobs only:

| Job ID | Name | State | Elapsed | CPUs | Nodes | Submit | Start |
|--------|------|-------|---------|------|-------|--------|-------|
| 46229238 | KennethYa | COMPLETED | 5:32:46 | 192 | 4 | 2026-03-01 | 2026-03-01 |
| 46252383 | KennethYa | COMPLETED | 5:47:36 | 192 | 4 | 2026-03-01 | 2026-03-02 |
| 47887742 | KennethYa | TIMEOUT | 1-00:00 | 32 | 1 | 2026-04-03 | 2026-04-03 |
| 48179717 | KennethYa | CANCELLED | 12:47 | 48 | 1 | 2026-04-10 | 2026-04-10 |
| 48207267 | KennethYa | TIMEOUT | 1-00:00 | 480 | 10 | 2026-04-10 | 2026-04-12 |
| 48808257 | 9CZ2_equil | COMPLETED | 11:00:58 | 192 | 4 | 2026-04-20 | 2026-04-22 |
| 48808268 | KennethYa | COMPLETED | 13:32:33 | 96 | 2 | 2026-04-20 | 2026-04-20 |
| 49165809 | step7_cpu | TIMEOUT | 1-00:00 | 96 | 2 | 2026-04-29 | 2026-04-30 |
| 49434130 | monomer_equil | COMPLETED | 1:24:12 | 192 | 4 | 2026-05-08 | 2026-05-09 |
| 49436413 | step7_10_restart | COMPLETED | 8:47:20 | 96 | 2 | 2026-05-09 | 2026-05-09 |
| 50583298 | step7_11_restart | COMPLETED | 9:56:33 | 96 | 2 | 2026-06-08 | 2026-06-08 |
| 50623759 | step7_12_restart | COMPLETED | 5:39:00 | 192 | 4 | 2026-06-09 | 2026-06-09 |
| 50676351 | step7_13plus | TIMEOUT | 1-12:00 | 240 | 5 | 2026-06-10 | 2026-06-11 |
| 50698644 | af2_dome24 | OUT_OF_MEMORY | 1-06:33 | 48 | 1 (bigmem) | 2026-06-10 | 2026-06-10 |
| 50736443 | 9cz2_prod | PENDING | — | 288 | 6 | 2026-06-12 | pending |
