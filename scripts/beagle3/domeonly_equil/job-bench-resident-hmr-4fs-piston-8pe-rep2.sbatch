#!/bin/bash
# NAMD speedup sweep -- 1 GPU, 16 PE, GPU-resident, HMR-repartitioned PSF (via VMD psfgen hmassrepart, target 3.024 amu) + 4fs timestep -- literature-validated, mirrors the OpenMM HMR test
# Short NPT production (25,000 steps), starting from step6.6_equilibration restart.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the namd/ directory: sbatch job-bench-resident-hmr-4fs-piston-8pe-rep2.sbatch
#
#SBATCH --job-name=bench-resident-hmr-4fs-piston-8pe-rep2
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-resident-hmr-4fs-piston-8pe-rep2_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-8pe-rep2_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-hmr-4fs-piston-8pe-rep2"
namd3 +p8 +devices 0 step7_bench_resident_hmr_4fs_piston_8pe_rep2.inp > $(basename step7_bench_resident_hmr_4fs_piston_8pe_rep2.inp .inp).out
echo "$(date): completed bench-resident-hmr-4fs-piston-8pe-rep2"
