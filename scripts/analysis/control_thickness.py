import MDAnalysis as mda
import numpy as np
import matplotlib.pyplot as plt

PSF = "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step5_input.psf"
DCDS = [
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_1.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_2.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_3.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_4.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_5.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_6.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_7.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_8.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_9.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_10.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_11.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_12.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_13.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_14.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_15.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_16.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_17.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_18.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_19.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_20.dcd",
    "/scratch/midway3/junseo/26summer-research/charmm-gui-7628525516/namd/step7_21.dcd",
    "/project2/haddadian/junseo/beagle3-jobs/control_prod/step7_22.dcd",
]
OUTDIR   = "/scratch/midway3/junseo/26summer-research/analysis"
GRID     = (20, 20)
OUT_PNG  = f"{OUTDIR}/control_thickness_31ns.png"
OUT_NPY  = f"{OUTDIR}/control_thickness_31ns.npy"

u = mda.Universe(PSF, *DCDS)
headgroups = u.select_atoms("name P or name P1")
print(f"Headgroup atoms: {len(headgroups)}, Frames: {len(u.trajectory)}")

nx, ny = GRID
x_max = u.dimensions[0]
y_max = u.dimensions[1]
dx = x_max / nx
dy = y_max / ny

z_upper = np.zeros((nx, ny))
z_lower = np.zeros((nx, ny))
c_upper = np.zeros((nx, ny))
c_lower = np.zeros((nx, ny))

for i, ts in enumerate(u.trajectory):
    if i % 50 == 0:
        print(f"  frame {i}/{len(u.trajectory)}")

    pos    = headgroups.positions
    z_mid  = np.median(pos[:, 2])
    pos_u  = pos[pos[:, 2] > z_mid]
    pos_l  = pos[pos[:, 2] <= z_mid]

    xs = ((pos_u[:, 0] + (x_max / 2)) / dx).astype(int)
    ys = ((pos_u[:, 1] + (y_max / 2)) / dy).astype(int)
    xs = np.clip(xs, 0, nx - 1)
    ys = np.clip(ys, 0, ny - 1)
    np.add.at(z_upper, (xs, ys), pos_u[:, 2])
    np.add.at(c_upper, (xs, ys), 1)

    xs = ((pos_l[:, 0] + (x_max / 2)) / dx).astype(int)
    ys = ((pos_l[:, 1] + (y_max / 2)) / dy).astype(int)
    xs = np.clip(xs, 0, nx - 1)
    ys = np.clip(ys, 0, ny - 1)
    np.add.at(z_lower, (xs, ys), pos_l[:, 2])
    np.add.at(c_lower, (xs, ys), 1)

z_upper_avg = np.divide(z_upper, c_upper, out=np.zeros_like(z_upper), where=c_upper > 0)
z_lower_avg = np.divide(z_lower, c_lower, out=np.zeros_like(z_lower), where=c_lower > 0)
thickness   = z_upper_avg - z_lower_avg

np.save(OUT_NPY, thickness)
print(f"Raw data saved to {OUT_NPY}")
print(f"Mean bilayer thickness: {np.nanmean(thickness):.2f} A")
print(f"Min: {thickness.min():.2f}, Max: {thickness.max():.2f}")

plt.figure(figsize=(6, 5))
im = plt.imshow(thickness.T, origin="lower",
                extent=[0, x_max, 0, y_max],
                cmap="viridis", interpolation="nearest",
                aspect="auto", vmin=20, vmax=45)
plt.colorbar(im, label="Bilayer thickness (A)")
plt.xlabel("X (A)")
plt.ylabel("Y (A)")
plt.title("Control System — Average Bilayer Thickness (~31 ns)")
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
print(f"Plot saved to {OUT_PNG}")
