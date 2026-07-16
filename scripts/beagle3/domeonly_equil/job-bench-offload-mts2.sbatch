#!/bin/bash
# NAMD speedup sweep -- 1 GPU, 16 PE, GPU-resident, multiple timestepping (nonbondedFreq=2, fullElectFrequency=4) -- standard r-RESPA technique, PME every 4th step
# Short NPT production (25,000 steps), starting from step6.6_equilibration restart.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the namd/ directory: sbatch job-bench-offload-mts2.sbatch
#
#SBATCH --job-name=bench-offload-mts2
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-offload-mts2_%j.out
#SBATCH --error=bench-offload-mts2_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-offload-mts2"
namd3 +p16 +devices 0 step7_bench_offload_mts2.inp > $(basename step7_bench_offload_mts2.inp .inp).out
echo "$(date): completed bench-offload-mts2"
