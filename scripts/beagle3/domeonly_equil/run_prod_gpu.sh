#!/bin/bash
# GPU production runner for Beagle3 (NAMD 3.0.1, dome-only system, 2 GPU).
# Called by job-submit-beagle3.sbatch.
#
# Config: resident mode (CUDASOAintegrate on), HMR OFF (standard PSF, 2fs
# timestep, standard piston 50/25fs) -- the physics-neutral optimal config
# benchmarked at 8.23 ns/day (job 52126502, see analysis/namd_vs_openmm_
# benchmark_plan.md / progress_log.md). HMR's 16.71 ns/day config is faster
# but was not adopted for this run -- see the accuracy-tradeoff discussion
# (kinetic/dynamical properties, incl. diffusion, are the documented caveat
# area, and this project's core question touches membrane/lipid dynamics).
#
# Naming convention: outputs are named step7_<N> where N is the CUMULATIVE
# nanoseconds of production simulated since step6.6, matching the control
# system's convention (see control_prod/run_prod_gpu.sh, Rajiv's
# /project2/haddadian/rajiv/namd/step7_run20/50/80.inp).
#
# cumulative_ns.txt is the ledger of truth: "<name> <cumulative_ns>" per line.
# Self-heals if the previous submission was truncated by wall time.
#
# BLOCK_STEPS: steps per submission (2 fs/step). 500,000 = 1 ns, matching
# Rajiv's original step7_1/step7_2/... convention (he later scaled to 10ns+
# blocks via step7_run20.inp once established, but this project is starting
# at the same granularity he did). Chunk size doesn't meaningfully affect
# throughput -- NAMD's per-step cost is independent of block length, and the
# fixed startup/toppar-parsing overhead (~1-2 min) is <1% of a 1ns block's
# ~2.9h runtime at the benchmarked 8.23 ns/day. The tradeoff is purely
# practical: more frequent manual resubmission (nothing auto-chains yet).

set -e

BLOCK_STEPS=500000
LEDGER="cumulative_ns.txt"

# Self-heal: if the most recent restart file on disk is newer than what the
# ledger last recorded, a run finished or was truncated since the ledger was
# updated. Read its true completed steps from its .out log and append the
# correct entry (and rename its output files if they don't already match).
#
# 2026-07-15 incident (control system): the glob below used to match
# step7_*.restart.coor unrestricted, which matched a leftover benchmark file
# left in the same directory. Self-heal treated it as "the latest completed
# production block" and renamed it onto step7_45.* with a plain mv --
# silently overwriting and destroying 8ns of real trajectory. Fixed two ways:
# (1) the glob now requires a pure step7_<digits> name, excluding anything
# with extra suffix text; (2) a hard check refuses to rename onto a target
# that already exists, instead of silently clobbering it. Also: archive
# benchmark files out of the production directory as soon as they're no
# longer needed (see benchmarks_archive/ convention) so they can't collide
# with this glob in the first place.
last_ledger_name=$(tail -1 "$LEDGER" | awk '{print $1}')
last_ledger_ns=$(tail -1 "$LEDGER" | awk '{print $2}')

latest_restart=$(ls -t step7_*.restart.coor 2>/dev/null | grep -E '^step7_[0-9]+\.restart\.coor$' | head -1)
latest_name=$(basename "$latest_restart" .restart.coor)

if [[ -n "$latest_name" && "$latest_name" != "$last_ledger_name" ]]; then
    actual_steps=$(grep '^TIMING' "${latest_name}.out" | tail -1 | awk '{print $2}')
    actual_ns=$(echo "scale=4; ${actual_steps} * 2 / 1000000" | bc)
    true_cumulative=$(echo "scale=4; ${last_ledger_ns} + ${actual_ns}" | bc)
    true_name="step7_$(echo "${true_cumulative}/1" | bc)"

    if [[ "$latest_name" != "$true_name" ]]; then
        if [[ -e "${true_name}.restart.coor" ]]; then
            echo "FATAL: self-heal would rename ${latest_name}.* to ${true_name}.*, but ${true_name}.restart.coor already exists -- refusing to overwrite. Investigate manually." >&2
            exit 1
        fi
        echo "$(date): ${latest_name} was truncated (${actual_ns} ns actual) -- renaming to ${true_name}"
        for f in "${latest_name}".*; do
            mv -v "$f" "${f/${latest_name}/${true_name}}"
        done
        latest_name="$true_name"
    fi

    echo "${latest_name} ${true_cumulative}" >> "$LEDGER"
fi

prev_name=$(tail -1 "$LEDGER" | awk '{print $1}')
prev_cumulative=$(tail -1 "$LEDGER" | awk '{print $2}')
PREV="${prev_name}.restart"

block_ns=$(echo "scale=4; ${BLOCK_STEPS} * 2 / 1000000" | bc)
target_cumulative=$(echo "scale=4; ${prev_cumulative} + ${block_ns}" | bc)
OUT="step7_$(echo "${target_cumulative}/1" | bc)"

echo "$(date): running ${OUT} from ${PREV} (${BLOCK_STEPS} steps = ${block_ns} ns, target cumulative ${target_cumulative} ns)"

sed "s/^set inputname.*/set inputname           ${PREV};/"  step7_production.inp | \
sed "s/^outputName.*/outputName              ${OUT};/"      | \
sed "s/^numsteps.*/numsteps                ${BLOCK_STEPS};/" | \
sed "s/^run .*/run                     ${BLOCK_STEPS};/" \
> step7_run.inp

namd3 +p${SLURM_NTASKS_PER_NODE} +devices 0,1 step7_run.inp > "${OUT}.out"

actual_steps=$(grep '^TIMING' "${OUT}.out" | tail -1 | awk '{print $2}')
actual_ns=$(echo "scale=4; ${actual_steps} * 2 / 1000000" | bc)
actual_cumulative=$(echo "scale=4; ${prev_cumulative} + ${actual_ns}" | bc)
echo "${OUT} ${actual_cumulative}" >> "$LEDGER"
echo "$(date): completed ${OUT} (actual cumulative: ${actual_cumulative} ns)"
