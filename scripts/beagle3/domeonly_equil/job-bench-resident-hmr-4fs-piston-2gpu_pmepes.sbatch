#!/bin/bash
# 2 GPU with explicit +pmePEs 4 (default lets NAMD auto-assign; testing whether reducing
# the PME device's PE load pushes past 2-GPU's already-strong 16.71 ns/day).
#SBATCH --job-name=bench-resident-hmr-4fs-piston-2gpu_pmepes
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
#SBATCH --output=bench-resident-hmr-4fs-piston-2gpu_pmepes_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-2gpu_pmepes_%j.err

module load namd/3.0.1-multicore-cuda
cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
echo "$(date): starting 2gpu_pmepes"
namd3 +p16 +pmePEs 4 +devices 0,1 step7_bench_resident_hmr_4fs_piston_2gpu_pmepes.inp > step7_bench_resident_hmr_4fs_piston_2gpu_pmepes.out
echo "$(date): completed 2gpu_pmepes"
