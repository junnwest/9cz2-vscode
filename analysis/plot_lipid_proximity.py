import pandas as pd
import matplotlib.pyplot as plt

DAT = "analysis/lipid_count_FtsH_nodome_namd.dat"
OUT = "analysis/lipid_proximity_FtsH_nodome.png"

df = pd.read_csv(DAT, sep="\t")
time_ns = df["Frame"] * 0.1  # 1 frame = 100 ps = 0.1 ns

fig, ax = plt.subplots(figsize=(10, 5))

colors = {"POPG_Count": "#e41a1c", "DOPG_Count": "#ff7f00",
          "DPPE_Count": "#377eb8", "LOACL_Count": "#4daf4a", "TLCL_Count": "#984ea3"}
labels = {"POPG_Count": "POPG", "DOPG_Count": "DOPG",
          "DPPE_Count": "DPPE", "LOACL_Count": "LOACL1", "TLCL_Count": "TLCL1"}

for col, color in colors.items():
    ax.plot(time_ns, df[col], label=labels[col], color=color, lw=1.2)

ax.set_xlabel("Time (ns)")
ax.set_ylabel("Lipid count within 6 Å of FtsH TM helices")
ax.set_title("Lipid proximity to FtsH TM — no-dome system (~10 ns)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT, dpi=150)
print(f"Saved: {OUT}")
