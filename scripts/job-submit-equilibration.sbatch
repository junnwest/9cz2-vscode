#!/bin/bash
# SLURM job for CHARMM-GUI step6 equilibration (GPU, NAMD 3)
# Source: namd-af-singlechain/job-submit-equilibration.sbatch
# For CPU-only equilibration, use namd/2.14 on caslake instead.
#
#SBATCH --job-name=9cz2_equil
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err
#SBATCH --time=24:00:00
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:1
#SBATCH --account=pi-haddadian

module unload namd
module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

for i in 1 2 3 4 5 6; do
    step="step6.${i}_equilibration"
    namd3 +p${SLURM_CPUS_PER_TASK} +devices 0 ${step}.inp > ${step}.out
done
