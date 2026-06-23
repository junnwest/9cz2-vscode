# Build PSF and PDB (with H atoms) for dome_with_m3_grafted using psfgen
# Run with: vmd -dispdev none -e 02_build_psf.tcl

package require psfgen
resetpsf

set TOPPAR /scratch/midway3/junseo/26summer-research/charmm-gui-9cz2fulldome-8119908655/toppar
set SEGDIR /scratch/midway3/junseo/26summer-research/minimize_m3/segments
set OUTDIR /scratch/midway3/junseo/26summer-research/minimize_m3

topology $TOPPAR/top_all36_prot.rtf

# Chains A-Z -> XP1 segments
foreach ch {A B C D E F G H I J K L M N O P Q R S T U V W X Y Z} {
    set seg "${ch}P1"
    set pdb "$SEGDIR/${seg}.pdb"
    segment $seg {
        first NTER
        last CTER
        pdb $pdb
    }
    coordpdb $pdb $seg
}

# FtsH TM chains 1-9,0 -> XP2 segments
foreach ch {1 2 3 4 5 6 7 8 9 0} {
    set seg "${ch}P2"
    set pdb "$SEGDIR/${seg}.pdb"
    segment $seg {
        first NTER
        last CTER
        pdb $pdb
    }
    coordpdb $pdb $seg
}

guesscoord

writepsf $OUTDIR/dome_m3.psf
writepdb $OUTDIR/dome_m3_H.pdb

puts "PSF and PDB written to $OUTDIR"
quit
