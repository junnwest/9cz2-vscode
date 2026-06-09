#!/bin/bash
# Template SLURM job for step7 production restarts on caslake (CPU)
# Actual files: charmm-gui-7628525516/namd/job-submit-step7-{N}-restart-cpu.sbatch
#
#SBATCH --job-name=9cz2_step7_cpu
#SBATCH --output=step7_%j.out
#SBATCH --error=step7_%j.err
#SBATCH --time=1-12:00:00
#SBATCH --partition=caslake
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=48
#SBATCH --cpus-per-task=1
#SBATCH --account=pi-haddadian

module unload namd
module load namd/2.14

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

chmod +x run_step7_12_restart_cpu.sh
./run_step7_12_restart_cpu.sh
