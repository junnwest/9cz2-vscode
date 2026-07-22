#!/bin/bash
# Convert CHARMM-GUI AA dome system → Martini 3 CG
# Usage: bash convert_charmm_to_martini.sh <step5_input.pdb>

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <step5_input.pdb>"
  echo ""
  echo "Expected: CHARMM-GUI outputs (step5_input.pdb + step5_input.psf)"
  echo "Output: dome_martini.gro, dome_martini.top (ready for GROMACS)"
  exit 1
fi

INPUT_PDB="$1"
INPUT_PSF="${INPUT_PDB%.pdb}.psf"
OUTPUT_GRO="dome_martini.gro"
OUTPUT_TOP="dome_martini.top"

if [ ! -f "$INPUT_PDB" ] || [ ! -f "$INPUT_PSF" ]; then
  echo "Error: cannot find $INPUT_PDB or $INPUT_PSF"
  exit 1
fi

echo "=== Converting dome from CHARMM-GUI (AA) → Martini 3 CG ==="
echo "Input:  $INPUT_PDB"
echo "Output: $OUTPUT_GRO, $OUTPUT_TOP"
echo ""

# Check if martinize2 is available
if command -v martinize2 &> /dev/null; then
  echo "✓ Using martinize2 (automatic conversion)"
  martinize2 \
    -f "$INPUT_PDB" \
    -ff martini3001 \
    -o "$OUTPUT_GRO" \
    -p "$OUTPUT_TOP" \
    -posres \
    -v 2>&1 | tail -20
elif python3 -c "import martinize2" 2>/dev/null; then
  echo "✓ Using martinize2 (via Python import)"
  python3 -m martinize2 \
    -f "$INPUT_PDB" \
    -ff martini3001 \
    -o "$OUTPUT_GRO" \
    -p "$OUTPUT_TOP" \
    -posres \
    -v 2>&1 | tail -20
else
  echo "⚠ martinize2 not found locally"
  echo ""
  echo "FALLBACK OPTION 1: Use Martini online server"
  echo "  → Visit: https://cgmartini.nl/index.php/online-martini-structure-converter"
  echo "  → Upload: $INPUT_PDB"
  echo "  → Download output → use in GROMACS (step below)"
  echo ""
  echo "FALLBACK OPTION 2: Install martinize2 on Beagle3"
  echo "  ssh beagle3"
  echo "  module load python/anaconda-2021.05"
  echo "  pip install --user martinize2"
  echo "  # then re-run this script on Beagle3"
  echo ""
  echo "FALLBACK OPTION 3: Manual setup (use GROMACS editconf + hand topology)"
  echo "  See MARTINI_WORKFLOW.md for details"
  exit 1
fi

if [ -f "$OUTPUT_GRO" ] && [ -f "$OUTPUT_TOP" ]; then
  echo ""
  echo "✓✓✓ Conversion successful ✓✓✓"
  echo ""
  echo "Generated files:"
  echo "  1. $OUTPUT_GRO         (GROMACS coordinates, CG beads)"
  echo "  2. $OUTPUT_TOP         (Martini 3 topology)"
  echo ""
  echo "NEXT: Prepare GROMACS job"
  echo "  → See MARTINI_WORKFLOW.md step 3 for MDP template + sbatch"
  echo "  → Quick start:"
  echo "      gmx grompp -f md.mdp -c $OUTPUT_GRO -p $OUTPUT_TOP -o dome.tpr"
  echo "      sbatch run_martini_gromacs.sbatch"
else
  echo "✗ Conversion failed"
  exit 1
fi
