#!/bin/bash
# Iterative step7 production runner for caslake CPU runs.
# Runs N iterations of 1 ns each (500,000 steps × 2 fs).
# Each iteration reads from the previous restart.
# Source: namd_caslake/run_step7_iter_cpu.sh (Rajiv), also in charmm-gui-7628525516/namd/
set -e

template="step7_production.inp"
prev="step6.6_equilibration"   # starting point for first iteration; change to step7_N.restart for restarts

START=1
END=10   # number of 1-ns iterations to run

for cnt in $(seq $START $END); do
    out="step7_${cnt}"

    sed "s/^set inputname.*/set inputname           ${prev};/" "$template" | \
    sed "s/^outputName.*/outputName              ${out}; # base name for output from this run/" \
    > step7_run.inp

    mpiexec.hydra -bootstrap slurm -np ${SLURM_NTASKS} namd2 step7_run.inp > ${out}.out

    prev="${out}.restart"
done
