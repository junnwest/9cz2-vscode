#!/bin/bash
# NAMD speedup sweep -- resident, HMR+4fs+piston, 4 PE. NAMD developer guidance (namd-l
# mailing list) recommends LOW core counts (2-4 PE) for GPU-resident mode since nearly
# everything is offloaded to the GPU -- our own PE curve (16->8 helped) was still
# improving when we stopped at 8; this tests whether it improves further at 4.
# Submit from the namd/ directory: sbatch job-bench-resident-hmr-4fs-piston-4pe.sbatch
#
#SBATCH --job-name=bench-resident-hmr-4fs-piston-4pe
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --constraint=a100
#SBATCH --output=bench-resident-hmr-4fs-piston-4pe_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-4pe_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-hmr-4fs-piston-4pe"
namd3 +p4 +devices 0 step7_bench_resident_hmr_4fs_piston_4pe.inp > step7_bench_resident_hmr_4fs_piston_4pe.out
echo "$(date): completed bench-resident-hmr-4fs-piston-4pe"
