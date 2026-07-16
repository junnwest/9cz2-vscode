#!/bin/bash
# NAMD -- winning config (resident, HMR+4fs+piston) on 2 GPUs, 16 PE total (8 per GPU,
# matching Dr. Trung's convention from his STMV benchmark). Trung's data for a similar-sized
# system on the same A100 hardware showed 2 GPU = no gain over 1 GPU (13 -> 13 ns/day) and
# 4 GPU = regression (13 -> 8 ns/day) in GPU-resident mode. This tests whether that holds for
# our specific config rather than assuming it transfers from his system.
# Submit from the namd/ directory: sbatch job-bench-resident-hmr-4fs-piston-2gpu-namd301.sbatch
#
#SBATCH --job-name=bench-resident-hmr-4fs-piston-2gpu-namd301
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
#SBATCH --output=bench-resident-hmr-4fs-piston-2gpu-namd301_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-2gpu-namd301_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-hmr-4fs-piston-2gpu-namd301"
namd3 +p16 +devices 0,1 step7_bench_resident_hmr_4fs_piston_2gpu.inp > step7_bench_resident_hmr_4fs_piston_2gpu_namd301.out
echo "$(date): completed bench-resident-hmr-4fs-piston-2gpu-namd301"
