#!/bin/bash
# Beagle3 GPU production — control membrane system (632,689 atoms)
# Continues from step7_37 (37.53 ns cumulative, renamed from step7_22 July 8, 2026).
# Resubmit as-is for additional 8 ns blocks; run_prod_gpu.sh auto-detects last step
# and names outputs by cumulative ns (see CLAUDE.md "Naming convention" note).
#
# Fixed July 13, 2026: account was pi-haddadian (not in beagle3 partition's
# AllowAccounts whitelist -- would be rejected at submission, see progress_log.md
# July 8 entry); switched to beagle3-exusers, which is what every job this summer
# has actually submitted under. Also switched off the ad-hoc NAMD_3.0alpha13 build
# (installed by another lab member, Sept 2024) to the properly-installed
# namd/3.0.1-multicore-cuda module, which has a documented fix for a GPU-resident
# pressure-tensor bug (not directly hit here since this config runs offload mode,
# but no reason to stay on an old alpha build once a stable one is available).
#
#SBATCH --job-name=ctrl-prod
#SBATCH --time=36:00:00
#SBATCH --qos=beagle3-prio
#SBATCH --partition=beagle3
#SBATCH --nodes=1
#SBATCH --account=beagle3-exusers
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:4
#SBATCH --exclude=beagle3-0028
#SBATCH --output=prod_%j.out
#SBATCH --error=prod_%j.err

module load namd/3.0.1-multicore-cuda

cd "$SLURM_SUBMIT_DIR" || exit 1
set -e

./run_prod_gpu.sh
