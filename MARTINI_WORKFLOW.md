# Martini CG Dome System — Ready-to-Run Workflow

> **SUPERSEDED — this is the July 22 planning doc, written before the pipeline was actually built
> and validated.** Several values below are now known wrong (PME instead of reaction-field, 1.2 nm
> cutoffs instead of 1.1, `gromacs/2022.4` — a PLUMED-patched build that segfaults on Martini
> virtual-site construction, use `2025.3`). Kept for historical reference only. **The real,
> validated recipe is in `CLAUDE.md` under "Martini 3 coarse-grained comparison" (10-step build
> recipe + selection gotchas + the full v1–v11 restraint-scheme comparison against CHARMM-GUI).**

**Status**: Setup in progress (July 22, 2026)  
**CHARMM-GUI Job**: 8458753726  
**Target**: Convert AA dome from CHARMM-GUI → Martini 3 CG → GROMACS production

---

## Workflow Overview

```
CHARMM-GUI (CHARMM36m, AA)
    ↓ download step5_input.pdb/.psf
    ↓
martinize2 (AA → CG conversion)
    ↓ output: .gro + .top (Martini 3)
    ↓
GROMACS (production, CG)
```

---

## Step 1: Get CHARMM-GUI Outputs (Tomorrow)

When job 8458753726 finishes:
1. Go to https://www.charmm-gui.org/?doc=input_gen&jobid=8458753726
2. Download **NAMD input files** section:
   - `step5_input.pdb` (coordinates)
   - `step5_input.psf` (topology/parameters)
3. Save to local disk, e.g., `~/Downloads/charmm-gui-8458753726/`

---

## Step 2: Convert to Martini CG

### Option A: Using martinize2 (pip/conda, once installed)

```bash
# On Beagle3 or Midway3 (after installing martinize2)
cd ~/Downloads/charmm-gui-8458753726/

martinize2 \
  -f step5_input.pdb \
  -ff martini3001 \
  -o dome_martini.gro \
  -x dome_martini-cg.pdb \
  -p dome_martini.top \
  -posres \
  -v
```

**Outputs**:
- `dome_martini.gro` — GROMACS coordinates (CG)
- `dome_martini-cg.pdb` — PDB format (CG)
- `dome_martini.top` — topology file (Martini 3 force field)

### Option B: Manual Workflow (if martinize2 unavailable)

Use GROMACS's built-in tools:

```bash
# Convert PSF → GROMACS format (intermediate)
gmx trjconv -f step5_input.pdb -s step5_input.psf -o dome_aa.gro

# Use GROMACS editconf + other tools to build CG system
# (This requires hand-mapping AA atoms → CG beads, more manual)
```

---

## Step 3: Prepare GROMACS Job

Once you have `dome_martini.gro` and `dome_martini.top`:

1. **Create an MDP file** (GROMACS simulation parameters):
   ```
   ; minimal GROMACS MD config for Martini 3 dome
   integrator                = md
   dt                        = 0.01  ; 10 fs timestep (CG standard)
   nsteps                    = 50000 ; 500 ps
   nstxout                   = 500   ; save every 5 ps
   nstlog                    = 100
   nstenergy                 = 100
   cutoff-scheme             = Verlet
   coulombtype               = PME
   rcoulomb                  = 1.2
   rvdw                      = 1.2
   tcoupl                    = v-rescale
   tau-t                     = 0.1
   ref-t                     = 303.15
   pcoupl                    = c-rescale
   tau-p                     = 12.0
   ref-p                     = 1.0
   compressibility           = 3e-4
   ```

2. **Prepare the system**:
   ```bash
   gmx grompp -f md.mdp -c dome_martini.gro -p dome_martini.top -o dome.tpr
   ```

3. **Submit to Beagle3**:
   ```bash
   sbatch run_martini_gromacs.sbatch  # (script below)
   ```

### SBATCH Template (run_martini_gromacs.sbatch)

```bash
#!/bin/bash
#SBATCH --job-name=martini-dome-cg
#SBATCH --account=beagle3-exusers
#SBATCH --partition=beagle3
#SBATCH --qos=beagle3-prio
#SBATCH -t 02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --output=martini-dome-cg_%j.out

module load gromacs/2022.4
cd $SLURM_SUBMIT_DIR

gmx mdrun -s dome.tpr -ntomp 16 -ntmpi 1 -nb gpu -pme gpu -v
```

---

## Step 4: Analysis

Once the CG run completes:

- **Trajectory**: `traj.trr` / `traj.xtc`
- **Dome opening**: Use GROMACS tools or Python to analyze CG bead positions
  - Compare to AA dome-model/dome-bact results
  - Lipid interaction / coverage changes?

---

## Installation Status (July 22, 2026)

- [ ] martinize2 install via conda (in progress on Beagle3)
- [ ] Conversion script ready to run
- [ ] GROMACS template job ready

---

## Timeline

- **Tomorrow (July 23)**: CHARMM-GUI downloads → convert to CG → queue GROMACS job
- **GROMACS runtime**: ~30–60 min on 2 GPU (vs ~26 days for AA GaMD)
- **Analysis**: Same day or next day

---

## Reference

- **Martinize2 docs**: https://github.com/marrink-lab/martinize-tools
- **Martini 3 force field**: https://cgmartini.nl/
- **GROMACS manual**: https://manual.gromacs.org/

