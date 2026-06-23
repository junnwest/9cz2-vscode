# Solvate and ionize the dome+M3 system (no membrane)
# Run with: vmd -dispdev none -e 03_solvate.tcl

package require solvate
package require autoionize

set OUTDIR /scratch/midway3/junseo/26summer-research/minimize_m3

# Solvate with 15 A padding, TIP3P water
solvate $OUTDIR/dome_m3.psf $OUTDIR/dome_m3_H.pdb \
    -t 15 \
    -o $OUTDIR/dome_m3_solv

# Ionize to 0.15 M NaCl
autoionize -psf $OUTDIR/dome_m3_solv.psf \
           -pdb $OUTDIR/dome_m3_solv.pdb \
           -sc 0.15 \
           -o $OUTDIR/dome_m3_ionized

puts "Solvated and ionized system written to $OUTDIR/dome_m3_ionized.*"
quit
