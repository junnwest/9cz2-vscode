#!/bin/bash
set -e

init=step5_input

for cnt in 1 2 3 4 5 6; do
    pcnt=$((cnt - 1))
    istep=$(printf "step6.%d_equilibration" "$cnt")
    pstep=$(printf "step6.%d_equilibration" "$pcnt")

    input_param="-t toppar.str -p ${init}.psf -c ${init}.crd"
    if [ "$cnt" -eq 1 ]; then
        input_param="${input_param} -b sysinfo.dat"
    else
        input_param="${input_param} -irst ${pstep}.rst"
    fi

    echo "$(date): starting ${istep}"
    python -u openmm_run.py -i "${istep}.inp" ${input_param} -orst "${istep}.rst" -odcd "${istep}.dcd" > "${istep}.out"
    echo "$(date): completed ${istep}"
done
