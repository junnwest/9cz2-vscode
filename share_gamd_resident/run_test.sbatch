#!/bin/bash
#SBATCH --job-name=namd-chen-resident-test
#SBATCH --account=beagle3-exusers
#SBATCH --partition=beagle3
#SBATCH --qos=beagle3-prio
#SBATCH -t 00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --output=test_resident_%j.out
#SBATCH --error=test_resident_%j.err

module load cuda/11.5
cd "$SLURM_SUBMIT_DIR"

NAMD3=/scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3
"$NAMD3" +p16 +devices 0,1 +setcpuaffinity gamd-resident-test.inp > gamd-resident-test.log
