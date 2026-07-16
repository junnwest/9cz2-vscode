#!/bin/bash
# OpenMM benchmark -- dome-only system, short NPT production (25,000 steps, ~50 ps),
# 1 GPU, single precision (CudaPrecision='single', openmm_run.py's hardcoded default).
# Starts from the completed step6.6_equilibration.rst. First data point for the
# NAMD-vs-OpenMM sweep (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the openmm/ directory: sbatch job-bench-1gpu-single.sbatch
#
#SBATCH --job-name=bench-1gpu-single
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench_1gpu_single_%j.out
#SBATCH --error=bench_1gpu_single_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench_1gpu_single"
python -u openmm_run.py -i step7_bench.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench_1gpu_single.rst -odcd step7_bench_1gpu_single.dcd \
    > step7_bench_1gpu_single.out
echo "$(date): completed bench_1gpu_single"
