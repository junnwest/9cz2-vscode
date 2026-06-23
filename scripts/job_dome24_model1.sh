#!/bin/bash
#SBATCH --job-name=af2_dome24_m1
#SBATCH --account=pi-haddadian
#SBATCH --partition=bigmem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=0
#SBATCH --time=1-12:00:00
#SBATCH --output=af2_dome24_m1_%j.out
#SBATCH --error=af2_dome24_m1_%j.err

# Runs only model_1_multimer_v3. Job 2 (job_dome24_bigmem.sh, all 5 models)
# should be queued behind this one. Cancel job 2 if this succeeds.

set -euo pipefail

WORK_DIR=/scratch/midway3/junseo/26summer-research/alphafold/9cz2
FASTA=$WORK_DIR/dome_24chain_input.fasta
OUTPUT_DIR=$WORK_DIR/af2_dome24_output
DOWNLOAD_DATA_DIR=/software/alphafold-data-2.3
MONITOR_LOG=$WORK_DIR/af2_monitor_${SLURM_JOB_ID}.log
MODEL_OUT=$OUTPUT_DIR/dome_24chain_input

echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Target: model_1_multimer_v3 only"

module load alphafold/2.3.2

export JAX_PLATFORM_NAME=cpu
export XLA_FLAGS="--xla_force_host_platform_device_count=48"

# Launch AF2 (model_1 only via wrapper) in background to enable monitoring
python $WORK_DIR/run_af2_model1_only.py \
  --fasta_paths=$FASTA \
  --model_preset=multimer \
  --data_dir=$DOWNLOAD_DATA_DIR \
  --uniref90_database_path=$DOWNLOAD_DATA_DIR/uniref90/uniref90.fasta \
  --mgnify_database_path=$DOWNLOAD_DATA_DIR/mgnify/mgy_clusters_2022_05.fa \
  --bfd_database_path=$DOWNLOAD_DATA_DIR/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
  --uniref30_database_path=$DOWNLOAD_DATA_DIR/uniref30/UniRef30_2021_03 \
  --pdb_seqres_database_path=$DOWNLOAD_DATA_DIR/pdb_seqres/pdb_seqres.txt \
  --uniprot_database_path=$DOWNLOAD_DATA_DIR/uniprot/uniprot.fasta \
  --template_mmcif_dir=$DOWNLOAD_DATA_DIR/pdb_mmcif/mmcif_files \
  --obsolete_pdbs_path=$DOWNLOAD_DATA_DIR/pdb_mmcif/obsolete.dat \
  --output_dir=$OUTPUT_DIR \
  --max_template_date=2026-06-10 \
  --use_precomputed_msas=True \
  --models_to_relax=none \
  --use_gpu_relax=False \
  --num_multimer_predictions_per_model=1 \
  --logtostderr &
AF2_PID=$!
echo "AF2 PID: $AF2_PID"

# Background monitor: logs every 10 min
(
  MONITOR_START=$SECONDS
  echo "$(date '+%Y-%m-%d %H:%M:%S') | monitor start | AF2 PID: $AF2_PID" > "$MONITOR_LOG"
  echo "timestamp | elapsed | cpu% | rss_gb | models_done/1 | unrelaxed_pdbs" >> "$MONITOR_LOG"
  while kill -0 "$AF2_PID" 2>/dev/null; do
    sleep 600
    ELAPSED=$(( SECONDS - MONITOR_START ))
    H=$(( ELAPSED / 3600 ))
    M=$(( (ELAPSED % 3600) / 60 ))
    CPU=$(ps -p "$AF2_PID" -o pcpu= 2>/dev/null | tr -d ' ' || echo "N/A")
    RSS_GB=$(ps -p "$AF2_PID" -o rss= 2>/dev/null | awk '{printf "%.1f", $1/1048576}' 2>/dev/null || echo "N/A")
    PKLS=$(find "$MODEL_OUT" -name 'result_model_1_multimer_v3_pred_0.pkl' 2>/dev/null | wc -l)
    PDBS=$(find "$MODEL_OUT" -name 'unrelaxed_model_1_multimer_v3_pred_0.pdb' 2>/dev/null | wc -l)
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ${H}h${M}m | ${CPU}% | ${RSS_GB}GB | ${PKLS}/1 | ${PDBS}" >> "$MONITOR_LOG"
  done
  echo "$(date '+%Y-%m-%d %H:%M:%S') | AF2 PID $AF2_PID exited" >> "$MONITOR_LOG"
) &
MONITOR_PID=$!

wait "$AF2_PID" && AF2_EXIT=0 || AF2_EXIT=$?

kill "$MONITOR_PID" 2>/dev/null || true
wait "$MONITOR_PID" 2>/dev/null || true

echo "Job finished: $(date)"
echo "AF2 exit code: $AF2_EXIT"
exit "$AF2_EXIT"
