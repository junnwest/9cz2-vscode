#!/bin/bash
# OpenMM speedup sweep -- LangevinMiddleIntegrator instead of LangevinIntegrator -- confirmed genuinely different classes in this OpenMM 8.1.0 install (unlike newer versions where they're aliased)
# Short NPT production, starting from step6.6_equilibration.rst.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the openmm/ directory: sbatch job-bench-middle.sbatch
#
#SBATCH --job-name=bench-middle
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-middle_%j.out
#SBATCH --error=bench-middle_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-middle"
python -u speedup_sweep/openmm_run_middle.py -i speedup_sweep/step7_bench.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-middle.rst -odcd step7_bench-middle.dcd \
    > step7_bench-middle.out
echo "$(date): completed bench-middle"
