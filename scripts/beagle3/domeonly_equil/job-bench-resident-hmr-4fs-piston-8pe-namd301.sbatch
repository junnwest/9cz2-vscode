#!/bin/bash
# NAMD speedup sweep -- same winning config (resident, HMR+4fs+piston, 8 PE) but on the
# OFFICIAL namd/3.0.1-multicore-cuda module instead of the ad-hoc alpha13 build we'd been
# using the whole time (/project2/haddadian/NAMD_3.0alpha13_..., installed by another lab
# member Sept 2024). 3.0.1's release notes specifically mention a fix for "pressure tensor
# calculation when running GPU-resident mode with multiple time stepping enabled" -- directly
# relevant to our RATTLE/patch-grid failures. Sanity/speed check on the stable build.
# Submit from the namd/ directory: sbatch job-bench-resident-hmr-4fs-piston-8pe-namd301.sbatch
#
#SBATCH --job-name=bench-resident-hmr-4fs-piston-8pe-namd301
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --constraint=a100
#SBATCH --output=bench-resident-hmr-4fs-piston-8pe-namd301_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-8pe-namd301_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-hmr-4fs-piston-8pe-namd301"
namd3 +p8 +devices 0 step7_bench_resident_hmr_4fs_piston_8pe.inp > step7_bench_resident_hmr_4fs_piston_8pe_namd301.out
echo "$(date): completed bench-resident-hmr-4fs-piston-8pe-namd301"
