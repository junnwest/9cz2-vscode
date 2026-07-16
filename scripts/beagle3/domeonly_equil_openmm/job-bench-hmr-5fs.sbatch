#!/bin/bash
# OpenMM speedup sweep round 2 -- 5fs timestep + HMR, force-switch preserved -- literature-validated for CHARMM lipid systems, more aggressive than the standard 4fs
# Short NPT production, starting from step6.6_equilibration.rst.
# Submit from the openmm/ directory: sbatch job-bench-hmr-5fs.sbatch
#
#SBATCH --job-name=bench-hmr-5fs
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-hmr-5fs_%j.out
#SBATCH --error=bench-hmr-5fs_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-hmr-5fs"
python -u speedup_sweep/openmm_run_hmr.py -i speedup_sweep/step7_bench_hmr_5fs.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-hmr-5fs.rst -odcd step7_bench-hmr-5fs.dcd \
    > step7_bench-hmr-5fs.out
echo "$(date): completed bench-hmr-5fs"
