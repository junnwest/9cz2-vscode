#!/bin/bash
# Beagle3 GPU equilibration — 9cz2 dome-only (no FtsH), 24 chains + membrane
# (1,742,229 atoms; CHARMM-GUI job 8349249136).
# Runs CHARMM-GUI steps 6.1–6.6 sequentially via run_equilibration_gpu.sh.
# Total: 2.25 ns (steps 6.1–6.3 @ 125k steps, 6.4–6.6 @ 250k steps).
# 2 GPUs / 16 PE-per-GPU (not 4/8 like main_equil's reference script): the Midway3
# A100 GPU benchmark suite (namd_performance.md) found 16 PE clearly beat 8 PE per
# GPU for a system this size, and 1->2 GPU scaling already showed strong diminishing
# returns (1.32x) -- the 2->4 GPU benchmark never completed, so 4 GPUs was untested,
# not confirmed. This config uses the actually-benchmarked-good ratio instead of the
# untested default, and doubles as a first real Beagle3-specific GPU/PE data point
# (Midway3 numbers don't necessarily transfer to Beagle3 hardware).
# Submit from the namd/ directory: sbatch job-submit-beagle3.sbatch
#
#SBATCH --job-name=domeonly-equil
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:2
#SBATCH --exclude=beagle3-0028
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_equilibration_gpu.sh
