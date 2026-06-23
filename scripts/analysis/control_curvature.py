import MDAnalysis as mda
from membrane_curvature.base import MembraneCurvature
import matplotlib.pyplot as plt
import numpy as np

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
OUTDIR  = "/scratch/midway3/junseo/26summer-research/analysis"
OUT_PNG = f"{OUTDIR}/control_curvature_31ns.png"
OUT_NPY = f"{OUTDIR}/control_curvature_31ns.npy"

u = mda.Universe(PSF, *DCDS)
print(f"Frames: {len(u.trajectory)}, Box: {u.dimensions[:3]}")
Lx, Ly = u.dimensions[0], u.dimensions[1]

upper_sel = "(name P or name P1) and prop z > 0"
lower_sel = "(name P or name P1) and prop z < 0"

print("Running upper leaflet curvature...")
curv_upper = MembraneCurvature(
    universe=u,
    select=upper_sel,
    n_x_bins=15,
    n_y_bins=15,
    wrap=True
).run()

print("Running lower leaflet curvature...")
curv_lower = MembraneCurvature(
    universe=u,
    select=lower_sel,
    n_x_bins=15,
    n_y_bins=15,
    wrap=True
).run()

curv = 0.5 * (curv_upper.results.average_mean + curv_lower.results.average_mean)

np.save(OUT_NPY, curv)
print(f"Raw data saved to {OUT_NPY}")
print(f"Min curvature: {np.nanmin(curv):.4f}, Max: {np.nanmax(curv):.4f} (1/A)")

plt.figure(figsize=(6, 5))
plt.title("Control System — Mean Membrane Curvature (~31 ns)", fontsize=12)
im = plt.imshow(curv, cmap="coolwarm", origin="lower",
                vmin=-0.01, vmax=0.01,
                extent=[0, Lx, 0, Ly])
plt.colorbar(im, label="Mean curvature (1/A)")
plt.xlabel("X (A)")
plt.ylabel("Y (A)")
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
print(f"Plot saved to {OUT_PNG}")
