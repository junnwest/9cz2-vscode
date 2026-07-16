#!/bin/bash
# OpenMM speedup sweep -- native OpenMM Switch vdW (removes CustomNonbondedForce entirely) -- CHANGES vdW physics from CHARMM36-validated force-switch, tests the magnitude of the custom-force tax
# Short NPT production, starting from step6.6_equilibration.rst.
# Part of the NAMD-vs-OpenMM benchmark (analysis/namd_vs_openmm_benchmark_plan.md).
# Submit from the openmm/ directory: sbatch job-bench-switch.sbatch
#
#SBATCH --job-name=bench-switch
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-switch_%j.out
#SBATCH --error=bench-switch_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-switch"
python -u speedup_sweep/openmm_run_base.py -i speedup_sweep/step7_bench_switch.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-switch.rst -odcd step7_bench-switch.dcd \
    > step7_bench-switch.out
echo "$(date): completed bench-switch"
