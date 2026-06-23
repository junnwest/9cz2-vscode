#!/bin/bash
# Production runner for caslake CPU runs (NAMD 2.14 MPI).
# Called by job-submit-step7-cpu.sbatch.
#
# Auto-detects the last completed or partial step and continues from there.
# Re-submit job-submit-step7-cpu.sbatch each time you want another block.
#
# STEPS_PER_RUN: steps per job submission (2 fs/step).
#   4,000,000 =  8 ns  (fits ~36h at 6 nodes for control system)
#   2,500,000 =  5 ns
#   1,000,000 =  2 ns  (use if full protein system is slow)

set -e

STEPS_PER_RUN=4000000

# Find the latest state to resume from.
# Prefer .restart.coor (most recent checkpoint) over .coor (end of last full run),
# since jobs may be killed by wall time before writing the final .coor.
last_coor_file=$(ls step7_*.coor 2>/dev/null | grep -v restart | sort -t_ -k2 -n | tail -1)
last_restart_file=$(ls step7_*.restart.coor 2>/dev/null | grep -v '\.old$' | sort -t_ -k2 -n | tail -1)

if [[ -z "$last_coor_file" && -z "$last_restart_file" ]]; then
    PREV="step6.6_equilibration"
    NEXT=1
else
    last_coor_n=0
    last_restart_n=0
    [[ -n "$last_coor_file" ]]    && last_coor_n=$(basename "$last_coor_file" .coor | sed 's/step7_//')
    [[ -n "$last_restart_file" ]] && last_restart_n=$(basename "$last_restart_file" .restart.coor | sed 's/step7_//')

    if [[ $last_restart_n -ge $last_coor_n ]]; then
        PREV="step7_${last_restart_n}.restart"
        NEXT=$((last_restart_n + 1))
    else
        PREV="step7_${last_coor_n}.restart"
        NEXT=$((last_coor_n + 1))
    fi
fi

OUT="step7_${NEXT}"
NS=$(echo "scale=0; ${STEPS_PER_RUN} * 2 / 1000000" | bc)
echo "$(date): running ${OUT} from ${PREV} (${STEPS_PER_RUN} steps = ${NS} ns)"

sed "s/^set inputname.*/set inputname           ${PREV};/"  step7_production.inp | \
sed "s/^outputName.*/outputName              ${OUT};/"      | \
sed "s/^numsteps.*/numsteps                ${STEPS_PER_RUN};/" | \
sed "s/^run .*/run                     ${STEPS_PER_RUN};/" \
> step7_run.inp

mpiexec.hydra -bootstrap slurm -np ${SLURM_NTASKS} namd2 step7_run.inp > "${OUT}.out"
echo "$(date): completed ${OUT}"
