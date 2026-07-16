#!/bin/bash
# OpenMM speedup sweep -- plain HMR+4fs + reduced reporting (nstout=5000), NO Middle/BlockSync/Switch -- isolating the true driver of lowreport's win
# Short NPT production, starting from step6.6_equilibration.rst.
# Submit from the openmm/ directory: sbatch job-bench-hmr-4fs-lowreport.sbatch
#
#SBATCH --job-name=bench-hmr-4fs-lowreport
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-hmr-4fs-lowreport_%j.out
#SBATCH --error=bench-hmr-4fs-lowreport_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-hmr-4fs-lowreport"
python -u speedup_sweep/openmm_run_hmr.py -i speedup_sweep/step7_bench_hmr_4fs_lowreport.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-hmr-4fs-lowreport.rst -odcd step7_bench-hmr-4fs-lowreport.dcd \
    > step7_bench-hmr-4fs-lowreport.out
echo "$(date): completed bench-hmr-4fs-lowreport"
