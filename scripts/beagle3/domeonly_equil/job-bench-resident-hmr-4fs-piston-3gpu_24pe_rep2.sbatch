#!/bin/bash
# Replicate of the surprising 3-GPU regression (8.87 ns/day, below even 1-GPU's 10.99,
# while 2-GPU gave 16.71). Confirming before trusting a single run.
#SBATCH --job-name=bench-resident-hmr-4fs-piston-3gpu_24pe_rep2
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
#SBATCH --output=bench-resident-hmr-4fs-piston-3gpu_24pe_rep2_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-3gpu_24pe_rep2_%j.err

module load namd/3.0.1-multicore-cuda
cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
echo "$(date): starting 3gpu_24pe_rep2"
namd3 +p24 +devices 0,1,2 step7_bench_resident_hmr_4fs_piston_3gpu_24pe_rep2.inp > step7_bench_resident_hmr_4fs_piston_3gpu_24pe_rep2.out
echo "$(date): completed 3gpu_24pe_rep2"
