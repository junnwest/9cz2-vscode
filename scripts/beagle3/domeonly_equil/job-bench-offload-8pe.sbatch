#!/bin/bash
# NAMD benchmark -- dome-only system, short NPT production (25,000 steps, ~50 ps at 2fs),
# 1 GPU, 8 PE, CUDASOAintegrate off (GPU-offload mode -- the mode the just-completed
# equilibration ran in, confirmed stable). Baseline data point for the NAMD-vs-OpenMM
# sweep (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the namd/ directory: sbatch job-bench-offload-8pe.sbatch
#
#SBATCH --job-name=bench-offload-8pe
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench_offload_8pe_%j.out
#SBATCH --error=bench_offload_8pe_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench_offload_8pe"
namd3 +p8 +devices 0 step7_bench_offload_8pe.inp > step7_bench_offload_8pe.out
echo "$(date): completed bench_offload_8pe"
