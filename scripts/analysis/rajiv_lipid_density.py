import MDAnalysis as mda
import numpy as np
import matplotlib.pyplot as plt

# ----------- USER INPUT -----------
psf_file = "step5_input.psf"       # Topology file
dcd_file = "gamd-all-prod-20.dcd"     # Trajectory file
lipid_sel = "resname DPPE and name P"         # Select lipid type here
n_x_bins = 15                      # Number of x bins
n_y_bins = 15                      # Number of y bins
wrap_atoms = True                  # Wrap coordinates in periodic box
# ----------------------------------

# Load syste
print("Loading system...")
u = mda.Universe(psf_file, dcd_file)
lipids = u.select_atoms(lipid_sel)

print("Getting dimensions...")
# Get box dimensions (assuming rectangular box)
Lx, Ly = np.mean([ts.dimensions[0:2] for ts in u.trajectory], axis=0)

# Storage for histogram accumulation
hist_total = np.zeros((n_x_bins, n_y_bins))
frame_count = 0

# Loop over trajectory
for ts in u.trajectory:
    coords = lipids.positions[:, :2]  # take x,y coordinates
    if wrap_atoms:
        coords[:, 0] %= ts.dimensions[0]
        coords[:, 1] %= ts.dimensions[1]

    # Compute 2D histogram for this frame
    H, xedges, yedges = np.histogram2d(
        coords[:, 0], coords[:, 1],
        bins=[n_x_bins, n_y_bins],
        range=[[0, ts.dimensions[0]], [0, ts.dimensions[1]]]
    )
    hist_total += H
    frame_count += 1

# Average density map
density_map = hist_total / frame_count

# Put protein COMs
protein = u.select_atoms("protein")

# storage: sum of COMs and counts per segment
seg_sums = {seg.segid: np.zeros(2) for seg in u.segments}
seg_counts = {seg.segid: 0 for seg in u.segments}
prev_com = {}

# single pass over trajectory
for ts in u.trajectory:
    for seg in protein.segments:
        com = seg.atoms.center_of_mass()[:2]

        if seg.segid == "PROU" and seg.segid in prev_com:
            Lx, Ly = u.dimensions[:2]
            dx = com[0] - prev_com[seg.segid][0]
            dy = com[1] - prev_com[seg.segid][1]
            if dx > Lx/2: com[0] -= Lx
            if dx < -Lx/2: com[0] += Lx
            if dy > Ly/2: com[1] -= Ly
            if dy < -Ly/2: com[1] += Ly

        prev_com[seg.segid] = com.copy()
        seg_sums[seg.segid] += com
        seg_counts[seg.segid] += 1

# compute averages
x, y = [], []
for seg in u.segments:
    mean_com = seg_sums[seg.segid] / seg_counts[seg.segid]
    x.append(mean_com[0] + (Lx / 2))
    y.append(mean_com[1] + (Ly / 2))

# -------- Plot Lipid Density --------
plt.figure(figsize=(6, 5))
plt.title(f"Lipid Density: {lipid_sel}", fontsize=14)
im = plt.imshow(
    density_map.T, origin="lower", cmap="BuPu",
    extent=[0, Lx, 0, Ly], aspect="auto"
)
plt.scatter(x, y, c="red", marker="o", s=50, label="Segment COMs")
plt.colorbar(im, label="Average lipid count per bin")
plt.xlabel("X (Å)")
plt.ylabel("Y (Å)")
plt.tight_layout()

# Save heatmap to file
plt.savefig("DPPE_prot_300_gamd_density_heatmap_top.png", dpi=300)
print("Heatmap saved as lipid_density_heatmap.png")

