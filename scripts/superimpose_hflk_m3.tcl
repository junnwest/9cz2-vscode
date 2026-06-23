#!/usr/bin/env vmd -dispdev text -e
# Superimpose AF2 HflK (1-419) onto each HflK chain in 9cz2minimized_ftsh_fixed.pdb.
# Alignment on CA atoms of residues 79-355 (the known cryo-EM region).
# Output: full original structure (all chains, all residues) + M3 tail (356-419)
#         appended to each HflK chain. HflC and FtsH are kept as-is.
#
# NOTE: M3 clash with neighboring chains is expected — this is a monomer AF2
#       prediction without dome context. The dome-24 AF2 run will give better results.
#
# Run:
#   /Applications/VMD\ 1.9.4a57-arm64-Rev12.app/Contents/MacOS/startup.command \
#     -dispdev text -e /Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode/scripts/superimpose_hflk_m3.tcl

set base     "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
set ref_pdb  "$base/9cz2minimized_ftsh_fixed.pdb"
set af2_pdb  "$base/hflk_mono_ranked_0.pdb"
set out_pdb  "$base/9cz2_with_hflk_m3.pdb"

mol load pdb $ref_pdb
set ref_mol [molinfo top get id]
puts "Loaded reference: mol $ref_mol"

# HflK chains in ftsh_fixed (start at res 79)
set hflk_chains {A C E G I K M O Q S U X}

set m3_files {}

foreach chain $hflk_chains {
    mol load pdb $af2_pdb
    set af2_mol [molinfo top get id]

    set ref_sel [atomselect $ref_mol  "chain $chain and name CA and resid 79 to 355"]
    set mob_sel [atomselect $af2_mol  "name CA and resid 79 to 355"]
    set mob_all [atomselect $af2_mol  "all"]

    if {[$ref_sel num] == 0 || [$mob_sel num] == 0} {
        puts "WARNING: skipping chain $chain (ref=[$ref_sel num] mob=[$mob_sel num])"
        $ref_sel delete; $mob_sel delete; $mob_all delete
        mol delete $af2_mol
        continue
    }

    set M [measure fit $mob_sel $ref_sel]
    $mob_all move $M

    # Extract only the M3 tail (356-419) after alignment
    set m3_sel [atomselect $af2_mol "resid 356 to 419"]
    $m3_sel set chain $chain
    set tmpfile "$base/tmp_m3_${chain}.pdb"
    $m3_sel writepdb $tmpfile
    lappend m3_files $tmpfile

    puts "Chain $chain: aligned on [$ref_sel num] CA pairs (79-355), extracted M3 (356-419)"

    $ref_sel delete; $mob_sel delete; $mob_all delete; $m3_sel delete
    mol delete $af2_mol
}

mol delete $ref_mol

# Build output: original structure + all M3 tails
set out [open $out_pdb w]

# Write original structure
set in [open $ref_pdb r]
while {[gets $in line] >= 0} {
    if {[string match "ATOM*" $line] || [string match "HETATM*" $line]} {
        puts $out $line
    }
}
close $in

# Append M3 tails for each HflK chain
foreach tmpfile $m3_files {
    set in [open $tmpfile r]
    while {[gets $in line] >= 0} {
        if {[string match "ATOM*" $line] || [string match "HETATM*" $line]} {
            puts $out $line
        }
    }
    close $in
    file delete $tmpfile
}

puts $out "END"
close $out

puts ""
puts "Done. Output: $out_pdb"
puts "Contains: all original chains (HflK 79-355, HflC, FtsH) + M3 tails (356-419) on chains A C E G I K M O Q S U X"
puts "NOTE: M3 clashes are expected from monomer AF2. Dome-24 run will give context-aware prediction."
quit
