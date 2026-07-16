#!/bin/bash
# NAMD -- winning config (resident, HMR+4fs+piston, NAMD 3.0.1) on 4 GPU(s), 16 PE.
# Follow-up to the surprising 2-GPU result (16.71 ns/day, 1.52x over 1-GPU's 10.99) which
# contradicted Dr. Trung's flat/regressing multi-GPU scaling for a smaller (1M-atom) system --
# mapping out the curve for our larger (1.74M-atom) system before concluding.
# Submit from the namd/ directory: sbatch job-bench-resident-hmr-4fs-piston-4gpu_16pe.sbatch
#
#SBATCH --job-name=bench-resident-hmr-4fs-piston-4gpu_16pe
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:4
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-resident-hmr-4fs-piston-4gpu_16pe_%j.out
#SBATCH --error=bench-resident-hmr-4fs-piston-4gpu_16pe_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

echo "$(date): starting bench-resident-hmr-4fs-piston-4gpu_16pe"
namd3 +p16 +devices 0,1,2,3 step7_bench_resident_hmr_4fs_piston_4gpu_16pe.inp > step7_bench_resident_hmr_4fs_piston_4gpu_16pe.out
echo "$(date): completed bench-resident-hmr-4fs-piston-4gpu_16pe"
