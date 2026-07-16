#!/bin/bash
# OpenMM speedup sweep -- safe-combined + Switch vdW -- max speedup ceiling IF the force-switch->switch physics tradeoff is accepted (not yet decided, informational only)
# Short NPT production, starting from step6.6_equilibration.rst.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the openmm/ directory: sbatch job-bench-aggressive.sbatch
#
#SBATCH --job-name=bench-aggressive
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-aggressive_%j.out
#SBATCH --error=bench-aggressive_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-aggressive"
python -u speedup_sweep/openmm_run_safe_combined.py -i speedup_sweep/step7_bench_aggressive.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-aggressive.rst -odcd step7_bench-aggressive.dcd \
    > step7_bench-aggressive.out
echo "$(date): completed bench-aggressive"
