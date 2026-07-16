#!/bin/bash
# OpenMM benchmark -- dome-only system, short NPT production (25,000 steps, ~50 ps),
# 1 GPU, mixed precision (CudaPrecision='mixed', via openmm_run_mixed.py -- the stock
# openmm_run.py hardcodes 'single' with no CLI override, so this uses a patched copy).
# Starts from the completed step6.6_equilibration.rst. Second data point for the
# NAMD-vs-OpenMM sweep (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the openmm/ directory: sbatch job-bench-1gpu-mixed.sbatch
#
#SBATCH --job-name=bench-1gpu-mixed
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench_1gpu_mixed_%j.out
#SBATCH --error=bench_1gpu_mixed_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench_1gpu_mixed"
python -u openmm_run_mixed.py -i step7_bench.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench_1gpu_mixed.rst -odcd step7_bench_1gpu_mixed.dcd \
    > step7_bench_1gpu_mixed.out
echo "$(date): completed bench_1gpu_mixed"
