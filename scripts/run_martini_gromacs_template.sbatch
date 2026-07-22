#!/bin/bash
# GROMACS production for Martini 3 CG dome system
# Beagle3 A100 GPU node
#
# Setup:
#   1. Have dome_martini.gro + dome_martini.top (from conversion script)
#   2. Have md.mdp (see MARTINI_WORKFLOW.md)
#   3. Run: gmx grompp -f md.mdp -c dome_martini.gro -p dome_martini.top -o dome.tpr
#   4. sbatch run_martini_gromacs_template.sbatch

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
#SBATCH --error=martini-dome-cg_%j.err

set -e

module load gromacs/2022.4

cd "$SLURM_SUBMIT_DIR"

echo "=== Martini 3 CG dome production on Beagle3 ==="
echo "Job: $SLURM_JOB_ID on $(hostname)"
echo "GPUs: 2 × A100"
echo ""

# Check for required TPR file
if [ ! -f dome.tpr ]; then
  echo "ERROR: dome.tpr not found. Did you run: gmx grompp -f md.mdp -c dome_martini.gro -p dome_martini.top -o dome.tpr ?"
  exit 1
fi

# Run GROMACS
# -ntomp 16: 16 OpenMP threads (to match ntasks-per-node)
# -ntmpi 1: 1 MPI task (simpler, single-GPU balanced mode on 2 GPU)
# -nb gpu: nonbonded on GPU
# -pme gpu: PME on GPU
gmx mdrun \
  -s dome.tpr \
  -ntomp 16 \
  -ntmpi 1 \
  -nb gpu \
  -pme gpu \
  -v \
  2>&1 | tee mdrun_${SLURM_JOB_ID}.log

echo ""
echo "=== GROMACS run complete ==="
echo "Output files:"
echo "  - confout.gro    (final coordinates)"
echo "  - traj.trr       (full trajectory)"
echo "  - ener.edr       (energy)"
echo ""
echo "Next: trajectory analysis (GROMACS tools or Python)"
