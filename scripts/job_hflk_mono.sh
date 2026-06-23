#!/bin/bash
#SBATCH --job-name=af2_hflk_mono
#SBATCH --account=pi-haddadian
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=06:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --mem=128G
#SBATCH --output=af2_hflk_mono_%j.out
#SBATCH --error=af2_hflk_mono_%j.err

WORK_DIR=/scratch/midway3/junseo/26summer-research/alphafold/9cz2
FASTA=$WORK_DIR/hflk_monomer.fasta
OUTPUT_DIR=$WORK_DIR/af2_hflk_mono_output
DOWNLOAD_DATA_DIR=/software/alphafold-data-2.3

mkdir -p $OUTPUT_DIR

module load alphafold/2.3.2 cuda/11.3

echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "GPU: $CUDA_VISIBLE_DEVICES"

# max_template_date set to include 9CZ2 (deposited 2024) as structural template.
# AF2 will scaffold residues 96-355 from the known structure and predict
# the missing M3 region (355-419) and TM helix (1-95) de novo.
python /software/alphafold-2.3.2-el8-x86_64/run_alphafold.py \
  --fasta_paths=$FASTA \
  --model_preset=monomer_ptm \
  --data_dir=$DOWNLOAD_DATA_DIR \
  --uniref90_database_path=$DOWNLOAD_DATA_DIR/uniref90/uniref90.fasta \
  --mgnify_database_path=$DOWNLOAD_DATA_DIR/mgnify/mgy_clusters_2022_05.fa \
  --bfd_database_path=$DOWNLOAD_DATA_DIR/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
  --uniref30_database_path=$DOWNLOAD_DATA_DIR/uniref30/UniRef30_2021_03 \
  --pdb70_database_path=$DOWNLOAD_DATA_DIR/pdb70/pdb70 \
  --template_mmcif_dir=$DOWNLOAD_DATA_DIR/pdb_mmcif/mmcif_files \
  --obsolete_pdbs_path=$DOWNLOAD_DATA_DIR/pdb_mmcif/obsolete.dat \
  --output_dir=$OUTPUT_DIR \
  --max_template_date=2026-06-15 \
  --models_to_relax=best \
  --use_gpu_relax=true \
  --logtostderr

echo "Job finished: $(date)"
