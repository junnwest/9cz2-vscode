#!/bin/bash
set -e

for i in {1..6}; do
    input="step6.${i}_equilibration.inp"
    output="step6.${i}_equilibration.out"

    echo "$(date): starting ${input}"
    mpiexec.hydra -bootstrap slurm -np ${SLURM_NTASKS} namd2 "${input}" > "${output}"
    echo "$(date): completed ${input}"
done
