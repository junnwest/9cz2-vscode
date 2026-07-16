#!/bin/bash
# Control system (632,689 atoms) -- GPU-count validation for resident mode, UNCHANGED
# physics (2fs, no HMR). Testing whether the dome-only system's 2-GPU sweet spot (16.71
# ns/day there) transfers to this smaller, different system before touching production.
# Short benchmark (25,000 steps) from the current production tip (step7_45.restart).
#SBATCH --job-name=bench-ctrl-resident-2gpu
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-ctrl-resident-2gpu_%j.out
#SBATCH --error=bench-ctrl-resident-2gpu_%j.err

module load namd/3.0.1-multicore-cuda
cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
echo "$(date): starting bench-ctrl-resident-2gpu"
namd3 +p16 +devices 0,1 step7_bench_ctrl_resident_2gpu.inp > step7_bench_ctrl_resident_2gpu.out
echo "$(date): completed bench-ctrl-resident-2gpu"
