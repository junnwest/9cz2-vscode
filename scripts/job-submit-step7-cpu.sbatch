#!/bin/bash
# SLURM job for step7 production on caslake (CPU, NAMD 2.14 MPI).
#
# First run: starts from step6.6_equilibration automatically.
# Restarts: re-submit this script as-is; run_prod_cpu.sh detects the last
# completed or partial step and continues from there.
#
# Adjust --nodes and STEPS_PER_RUN in run_prod_cpu.sh to match system size:
#   Control membrane (6 nodes, ~5.5 ns/day): STEPS_PER_RUN=4000000 (8 ns)
#   Full 9cz2 system (slower): reduce STEPS_PER_RUN to fit within wall time
#
#SBATCH --job-name=9cz2_prod
#SBATCH --output=prod_%j.out
#SBATCH --error=prod_%j.err
#SBATCH --time=1-12:00:00
#SBATCH --partition=caslake
#SBATCH --nodes=5
#SBATCH --ntasks-per-node=48
#SBATCH --account=pi-haddadian

module unload namd
module load namd/2.14

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

chmod +x run_prod_cpu.sh
./run_prod_cpu.sh
