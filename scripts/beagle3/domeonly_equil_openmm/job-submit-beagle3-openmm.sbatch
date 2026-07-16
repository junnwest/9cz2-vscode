#!/bin/bash
# Beagle3 GPU equilibration -- 9cz2 dome-only (no FtsH), 24 chains + membrane, OpenMM engine
# (1,742,229 atoms; CHARMM-GUI session 8349249136, openmm/ output -- same session/system as
# the NAMD build in domeonly_equil/, just a different output format).
# Runs CHARMM-GUI steps 6.1-6.6 sequentially via run_equilibration_openmm.sh.
# 1 GPU: OpenMM's CUDA platform is built around one simulation per GPU (unlike NAMD's native
# multi-GPU mode for a single sim), and this is also the first data point for the NAMD-vs-OpenMM
# benchmark sweep (see analysis/namd_vs_openmm_benchmark_plan.md) -- smaller resource ask also
# clears the ~70-deep beagle3-prio queue faster than requesting the whole node.
# Submit from the openmm/ directory: sbatch job-submit-beagle3-openmm.sbatch
#
#SBATCH --job-name=domeonly-equil-omm
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_equilibration_openmm.sh
