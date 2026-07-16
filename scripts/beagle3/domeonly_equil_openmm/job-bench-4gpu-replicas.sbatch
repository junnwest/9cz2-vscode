#!/bin/bash
# OpenMM benchmark -- dome-only system, short NPT production (25,000 steps, ~50 ps),
# 4 GPUs on ONE node running as 4 INDEPENDENT single-precision replicas (CUDA_VISIBLE_DEVICES
# pinned per process), not one simulation split across GPUs -- openmm_run.py has no
# multi-GPU support for a single context (confirmed by reading the script: Platform is
# picked once with no DeviceIndex option exposed). This tests whether per-GPU throughput
# degrades under node-level contention (shared PCIe/memory bandwidth/CPU) when running
# 4 concurrent replicas vs, the isolated 1-GPU number from job-bench-1gpu-single.sbatch --
# relevant for real production throughput if we end up running many replicas in parallel.
# Starts from the completed step6.6_equilibration.rst (all 4 replicas share it as read-only
# input; each writes distinctly-named output).
# Submit from the openmm/ directory: sbatch job-bench-4gpu-replicas.sbatch
#
#SBATCH --job-name=bench-4gpu-replicas
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:4
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench_4gpu_replicas_%j.out
#SBATCH --error=bench_4gpu_replicas_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting 4 concurrent replicas"
for dev in 0 1 2 3; do
    CUDA_VISIBLE_DEVICES=$dev python -u openmm_run.py -i step7_bench.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
        -irst step6.6_equilibration.rst \
        -orst step7_bench_4gpu_rep${dev}.rst -odcd step7_bench_4gpu_rep${dev}.dcd \
        > step7_bench_4gpu_rep${dev}.out 2>&1 &
done
wait
echo "$(date): completed 4 concurrent replicas"
