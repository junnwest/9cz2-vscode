#!/bin/bash
# AF2 dome-24 inference on Beagle3 bigmem (CPU-only, 512 GB RAM)
# 24-chain HflK/HflC multimer, precomputed MSAs reused from Midway3 run.
# Submit from any directory: sbatch job-submit-beagle3.sbatch
#
# BEFORE SUBMITTING — verify on a Beagle3 login node:
#   ls /software/alphafold-data-2.3          (database must be accessible)
#   module avail alphafold                   (module must exist)
#   If either fails, the job cannot run on Beagle3.
#
#SBATCH --job-name=af2_dome24
#SBATCH --account=beagle3-exusers
#SBATCH --partition=beagle3-bigmem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=0
#SBATCH --time=36:00:00
#SBATCH --output=af2_dome24_%j.out
#SBATCH --error=af2_dome24_%j.err

set -euo pipefail

BASE=/project2/haddadian/junseo/beagle3-jobs/af2_dome24
FASTA=$BASE/dome_24chain_input.fasta
OUTPUT_DIR=$BASE/output
DOWNLOAD_DATA_DIR=/software/alphafold-data-2.3

mkdir -p $OUTPUT_DIR

module load alphafold/2.3.2

export JAX_PLATFORM_NAME=cpu
export XLA_FLAGS="--xla_force_host_platform_device_count=32"

echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"

python /software/alphafold-2.3.2-el8-x86_64/run_alphafold.py \
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
  --max_template_date=2026-06-15 \
  --use_precomputed_msas=True \
  --models_to_relax=none \
  --use_gpu_relax=False \
  --num_multimer_predictions_per_model=1 \
  --logtostderr

echo "Job finished: $(date)"
