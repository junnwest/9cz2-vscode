#!/bin/bash
# Beagle3 GPU production -- dome-only system (1,742,229 atoms).
# Non-HMR (physics-neutral) config: resident mode, 2 GPU, 16 PE, A100,
# standard 2fs timestep -- benchmarked at 8.23 ns/day (job 52126502).
# HMR's 16.71 ns/day config was not adopted here; see run_prod_gpu.sh header
# and progress_log.md for the accuracy-tradeoff reasoning.
#
# Resubmit as-is for additional 8 ns blocks; run_prod_gpu.sh auto-detects
# the last completed block from cumulative_ns.txt and self-heals if the
# previous submission was truncated by wall time.
#
#SBATCH --job-name=domeonly-prod
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=prod_%j.out
#SBATCH --error=prod_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_prod_gpu.sh
