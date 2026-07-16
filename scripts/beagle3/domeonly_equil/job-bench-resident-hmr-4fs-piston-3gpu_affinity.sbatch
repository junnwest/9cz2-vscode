#!/bin/bash
# 3 GPU with +setcpuaffinity -- testing whether CPU-GPU affinity pinning fixes the
# 3-GPU regression (8.87 ns/day vs 1-GPU's 10.99, 2-GPU's 16.71).
#SBATCH --job-name=bench-resident-hmr-4fs-piston-3gpu_affinity
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=24
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:3
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-resident-hmr-4fs-piston-3gpu_affinity_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-3gpu_affinity_%j.err

module load namd/3.0.1-multicore-cuda
cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
echo "$(date): starting 3gpu_affinity"
namd3 +p24 +setcpuaffinity +devices 0,1,2 step7_bench_resident_hmr_4fs_piston_3gpu_pmepes.inp > step7_bench_resident_hmr_4fs_piston_3gpu_affinity.out
echo "$(date): completed 3gpu_affinity"
