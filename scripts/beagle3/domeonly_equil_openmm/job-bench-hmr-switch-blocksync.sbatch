#!/bin/bash
# OpenMM speedup sweep round 2 -- HMR+4fs + Switch vdW + BlockSync, WITHOUT LangevinMiddle -- isolates whether dropping Middle's double-constraint cost beats the 'aggressive' config (11.05)
# Short NPT production, starting from step6.6_equilibration.rst.
# Submit from the openmm/ directory: sbatch job-bench-hmr-switch-blocksync.sbatch
#
#SBATCH --job-name=bench-hmr-switch-blocksync
#SBATCH --time=00:45:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --exclude=beagle3-0028
#SBATCH --output=bench-hmr-switch-blocksync_%j.out
#SBATCH --error=bench-hmr-switch-blocksync_%j.err

module load openmm/8.1.0

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e
export PYTHONPATH="$SLURM_SUBMIT_DIR:$PYTHONPATH"

echo "$(date): starting bench-hmr-switch-blocksync"
python -u speedup_sweep/openmm_run_hmr_switch_blocksync.py -i speedup_sweep/step7_bench_hmr_switch_blocksync.inp -t toppar.str -p step5_input.psf -c step5_input.crd \
    -irst step6.6_equilibration.rst \
    -orst step7_bench-hmr-switch-blocksync.rst -odcd step7_bench-hmr-switch-blocksync.dcd \
    > step7_bench-hmr-switch-blocksync.out
echo "$(date): completed bench-hmr-switch-blocksync"
