#!/bin/bash
# OpenMM version comparison -- same winning config (plain HMR+4fs, force-switch preserved)
# as the trustworthy A100 baseline (10.87/10.95 ns/day on openmm/8.1.0 module), but on a
# freshly-installed OpenMM 8.5.2 (conda-forge, user-local env "openmm820" -- Beagle3 only has
# 7.5.1/8.1.0 as modules). 8.2.0's changelog claimed "reduced overhead for trajectory disk I/O
# operations"; this is the actual empirical test of that claim rather than trusting the
# changelog. Pinned to A100 given the GPU-model confound found in the NAMD sweep.
# Submit from the openmm/ directory: sbatch job-bench-hmr-4fs-openmm820.sbatch
#
#SBATCH --job-name=bench-hmr-4fs-openmm820
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-hmr-4fs-openmm820_%j.out
#SBATCH --error=bench-hmr-4fs-openmm820_%j.err

module load python/miniforge-25.3.0
source $(conda info --base)/etc/profile.d/conda.sh
conda activate openmm820

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-hmr-4fs-openmm820"
python -c "import openmm; print('OpenMM version:', openmm.version.version)"
python -u speedup_sweep/openmm_run_hmr.py -i speedup_sweep/step7_bench_hmr_4fs.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-hmr-4fs-openmm820.rst -odcd step7_bench-hmr-4fs-openmm820.dcd \
    > step7_bench-hmr-4fs-openmm820.out
echo "$(date): completed bench-hmr-4fs-openmm820"
