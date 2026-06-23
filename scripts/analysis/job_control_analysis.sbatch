#!/bin/bash
#SBATCH --job-name=ctrl_analysis
#SBATCH --partition=caslake
#SBATCH --account=pi-haddadian
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/midway3/junseo/26summer-research/analysis/ctrl_analysis_%j.log

module load python
source ~/mda_env/bin/activate

SCRIPTS=/scratch/midway3/junseo/26summer-research/analysis

echo "=== Thickness ===" && python $SCRIPTS/control_thickness.py
echo "=== Curvature ===" && python $SCRIPTS/control_curvature.py
