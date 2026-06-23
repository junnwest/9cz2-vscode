#!/bin/bash
#SBATCH --job-name=minimize_m3
#SBATCH --partition=caslake
#SBATCH --account=pi-haddadian
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=48
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/midway3/junseo/26summer-research/minimize_m3/minimize_m3_%j.log

module load namd/2.14

NAMD2=$(which namd2)
CONF=/scratch/midway3/junseo/26summer-research/minimize_m3/05_minimize.conf

mpirun -np 192 $NAMD2 +isomalloc_sync $CONF
