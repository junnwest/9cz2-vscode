#!/bin/bash
# NAMD speedup sweep -- 1 GPU, 32 PE, GPU-resident mode -- same PE-scaling test but resident mode
# Short NPT production (25,000 steps), starting from step6.6_equilibration restart.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the namd/ directory: sbatch job-bench-resident-32pe.sbatch
#
#SBATCH --job-name=bench-resident-32pe
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-resident-32pe_%j.out
#SBATCH --error=bench-resident-32pe_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-32pe"
namd3 +p32 +devices 0 step7_bench_resident_32pe.inp > $(basename step7_bench_resident_32pe.inp .inp).out
echo "$(date): completed bench-resident-32pe"
