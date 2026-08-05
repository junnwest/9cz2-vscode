#!/bin/bash
# Martini CG conversion workflow setup for dome system
# Run this after CHARMM-GUI job 8458753726 downloads
# Usage: bash martini_conversion_setup.sh

set -e

WORK_DIR="/scratch/beagle3/junseo/martini-dome-conversion"

echo "=== Setting up Martini conversion workflow on Beagle3 ==="

ssh beagle3 "
set -e
mkdir -p $WORK_DIR
cd $WORK_DIR

# Download martinize-tools repo as zip (avoids git auth issues)
if [ ! -f martinize-tools-main.zip ]; then
  echo 'Downloading martinize-tools...'
  wget -q https://github.com/marrink-lab/martinize-tools/archive/refs/heads/main.zip -O martinize-tools-main.zip 2>/dev/null || curl -L -o martinize-tools-main.zip https://github.com/marrink-lab/martinize-tools/archive/refs/heads/main.zip
fi

# Extract if not already done
if [ ! -d martinize-tools-main ]; then
  echo 'Extracting martinize-tools...'
  unzip -q martinize-tools-main.zip
fi

echo '✓ martinize-tools ready at: $WORK_DIR'
"

# Create local conversion script template
cat > /tmp/convert_to_martini_template.sh << 'CONVERT'
#!/bin/bash
# Martini CG conversion — run after downloading CHARMM-GUI outputs
# Usage: ./convert_to_martini.sh <input.pdb> <input.psf>

if [ $# -lt 2 ]; then
  echo "Usage: $0 <step5_input.pdb> <step5_input.psf>"
  exit 1
fi

INPUT_PDB="$1"
INPUT_PSF="$2"
OUTPUT_PREFIX="${INPUT_PDB%.pdb}_martini"

echo "Converting $INPUT_PDB to Martini 3 CG..."
cd /scratch/beagle3/junseo/martini-dome-conversion

python3 martinize-tools-main/martinize/martinize.py \
  -f "$INPUT_PDB" \
  -o "${OUTPUT_PREFIX}.gro" \
  -x "${OUTPUT_PREFIX}-cg.pdb" \
  -p "${OUTPUT_PREFIX}-top.top" \
  -ff martini3001 \
  -posres \
  -v 2>&1 | tail -30

if [ -f "${OUTPUT_PREFIX}.gro" ]; then
  echo ""
  echo "✓✓✓ Conversion successful ✓✓✓"
  echo "Outputs:"
  echo "  - ${OUTPUT_PREFIX}.gro        (GROMACS coordinates)"
  echo "  - ${OUTPUT_PREFIX}-cg.pdb    (PDB format)"
  echo "  - ${OUTPUT_PREFIX}-top.top   (GROMACS topology, Martini 3)"
  echo ""
  echo "Next: prepare GROMACS job with these files"
else
  echo "✗ Conversion failed — check output above"
  exit 1
fi
CONVERT

echo ""
echo "✓ Workflow setup complete"
echo ""
echo "NEXT STEPS (when CHARMM-GUI job 8458753726 finishes):"
echo "  1. Download outputs from CHARMM-GUI:"
echo "     - step5_input.pdb"
echo "     - step5_input.psf"
echo "  2. Run conversion:"
echo "     bash $WORK_DIR/convert_to_martini.sh step5_input.pdb step5_input.psf"
echo "  3. GROMACS will run on the resulting .gro + .top files"
echo ""
echo "Conversion template script location: $WORK_DIR/convert_to_martini.sh"
echo "Beagle3 work directory: $WORK_DIR"
