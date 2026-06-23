#!/bin/bash
# SLURM job for CHARMM-GUI step6 equilibration on caslake (CPU, NAMD 2.14 MPI).
# Runs steps 6.1–6.6 sequentially via run_equilibration.sh.
# Steps must stay separate — each .inp has different restraint strengths.
#
# System: 9cz2 full dome + membrane, 1.73M atoms
# Total equilibration: 2.25 ns (steps 6.1–6.3 @ 125k steps, 6.4–6.6 @ 250k steps)
# At 6 nodes: ~2.2 ns/day → fits within 36h wall time
# Submit from the namd/ directory: sbatch job-submit-equilibration.sbatch
#
#SBATCH --job-name=9cz2_equil
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err
#SBATCH --time=36:00:00
#SBATCH --partition=caslake
#SBATCH --nodes=6
#SBATCH --ntasks-per-node=48
#SBATCH --account=pi-haddadian

module unload namd
module load namd/2.14

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

chmod +x run_equilibration.sh
./run_equilibration.sh
