#!/bin/bash
# Beagle3 GPU equilibration — 9cz2 full dome + membrane (1,733,042 atoms)
# Runs CHARMM-GUI steps 6.1–6.6 sequentially via run_equilibration_gpu.sh.
# Total: 2.25 ns (steps 6.1–6.3 @ 125k steps, 6.4–6.6 @ 250k steps).
# Submit from the namd/ directory: sbatch job-submit-beagle3.sbatch
#
#SBATCH --job-name=9cz2-equil
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:4
#SBATCH --exclude=beagle3-0028
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err

export PATH=${PATH}:/project2/haddadian/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_equilibration_gpu.sh
