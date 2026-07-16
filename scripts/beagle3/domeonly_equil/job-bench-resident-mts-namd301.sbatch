#!/bin/bash
# Retest of the FAILED multiple-timestepping config (fullElectFrequency=4, GPU-resident mode)
# on the OFFICIAL namd/3.0.1-multicore-cuda module instead of the alpha13 build. NAMD 3.0.1's
# release notes specifically mention a fix for "pressure tensor calculation when running
# GPU-resident mode with multiple time stepping enabled" -- this is a direct test of whether
# that fix resolves the RATTLE/"periodic cell too small" failures we hit on alpha13.
# Submit from the namd/ directory: sbatch job-bench-resident-mts-namd301.sbatch
#
#SBATCH --job-name=bench-resident-mts-namd301
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-resident-mts-namd301_%j.out
#SBATCH --error=bench-resident-mts-namd301_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-mts-namd301"
namd3 +p16 +devices 0 step7_bench_resident_mts_namd301.inp > step7_bench_resident_mts_namd301.out
echo "$(date): completed bench-resident-mts-namd301"
