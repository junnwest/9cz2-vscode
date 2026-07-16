#!/bin/bash
# NAMD benchmark -- dome-only system, short NPT production (25,000 steps, ~50 ps at 2fs),
# 1 GPU, 16 PE, CUDASOAintegrate ON (GPU-resident mode). This is the key hypothesis test:
# GPU-resident mode crashed with a RATTLE constraint failure during step6.1 (the harsh
# minimize -> instant-velocity-reassignment-to-303K transition), but here we're starting
# from step6.6's restart -- an already-relaxed, already-thermalized state, much closer to
# the scenario where the Midway3 GPU-resident benchmark (analysis/namd_performance.md)
# succeeded. If this run completes without a RATTLE error, GPU-resident mode is usable for
# production even though it can't survive the initial equilibration transition, and NAMD's
# true production speed is likely much faster than the offload-mode numbers above suggest
# (NAMD's own docs: GPU-resident gives "more than 2x" over offload mode).
# Submit from the namd/ directory: sbatch job-bench-resident-16pe.sbatch
#
#SBATCH --job-name=bench-resident-16pe
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench_resident_16pe_%j.out
#SBATCH --error=bench_resident_16pe_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench_resident_16pe"
namd3 +p16 +devices 0 step7_bench_resident_16pe.inp > step7_bench_resident_16pe.out
echo "$(date): completed bench_resident_16pe"
