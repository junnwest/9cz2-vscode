#!/bin/bash
# Beagle3 GPU equilibration -- full system (dome + FtsH), bacterial (cardiolipin-
# microdomain) lipid composition #2 (74% PG / 20% CL / 6% PE), same AF3 ic-minimized
# protein structure as full-model (dome_m3_af3_ic_minimized_final.pdb).
# Runs CHARMM-GUI steps 6.1-6.6 sequentially via run_equilibration_gpu.sh.
# 1 GPU, offload mode (CUDASOAintegrate off, patched into all step6/step7 .inp
# files -- missing by default from this CHARMM-GUI download, same gap found and
# fixed for dome-model/full-model). This exactly mirrors full-model's
# equilibration script, which completed steps 6.1-6.5 cleanly and is currently
# finishing step6.6.
# Submit from the namd/ directory: sbatch job-submit-beagle3.sbatch
#
#SBATCH --job-name=full-bact-equil
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=equil_%j.out
#SBATCH --error=equil_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_equilibration_gpu.sh
