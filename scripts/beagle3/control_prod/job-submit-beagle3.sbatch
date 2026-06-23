#!/bin/bash
# Beagle3 GPU production — control membrane system (632,689 atoms)
# Continues from step7_21 (21 ns completed on Midway3).
# Resubmit as-is for additional blocks; run_prod_gpu.sh auto-detects last step.
#
#SBATCH --job-name=ctrl-prod
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:4
#SBATCH --exclude=beagle3-0028
#SBATCH --output=prod_%j.out
#SBATCH --error=prod_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_prod_gpu.sh
