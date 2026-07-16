#!/bin/bash
# Beagle3 GPU equilibration -- full system (dome + FtsH), lipid composition #1, using the
# AF3 ic-minimized structure (dome_m3_af3_ic_minimized_final.pdb, CHARMM-GUI session
# 8349253187). Runs CHARMM-GUI steps 6.1-6.6 sequentially via run_equilibration_gpu.sh.
# 1 GPU, offload mode (CUDASOAintegrate off, pre-patched into all step6/step7 .inp files --
# missing by default from this CHARMM-GUI download, same gap found and fixed for the
# dome-only system). Offload mode is the proven-robust recipe for equilibration specifically
# (survives the risky minimize->velocity-reassignment transition at step6.1); the multi-GPU/
# resident-mode speed optimizations found this summer are for PRODUCTION, not this one-time
# equilibration step.
# Submit from the namd/ directory: sbatch job-submit-beagle3.sbatch
#
#SBATCH --job-name=full-equil
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_equilibration_gpu.sh
