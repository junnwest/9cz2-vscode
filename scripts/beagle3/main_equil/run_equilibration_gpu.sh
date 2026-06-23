#!/bin/bash
set -e

for i in {1..6}; do
    input="step6.${i}_equilibration.inp"
    output="step6.${i}_equilibration.out"

    echo "$(date): starting ${input}"
    namd3 +p${SLURM_NTASKS_PER_NODE} +devices 0,1,2,3 "${input}" > "${output}"
    echo "$(date): completed ${input}"
done
