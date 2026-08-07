# Load v4 + v5 Martini Go trajectories side by side.
#   source /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories/martini_sweep/load_v4_v5.tcl
#
# v4 = Go, intra-chain contacts only (inter-chain deleted)
# v5 = Go, all contacts, epsilon 9.414 -> 5.0
# Both: 185,885 atoms, 51 frames = 0-50 ns, already PBC-corrected.

set B /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories/martini_sweep

# Real protein beads only. The Go build appends 8,040 massless virtual sites
# named CA that sit exactly on the BB beads -- without "not name CA" every
# backbone bead renders twice.
set SEL_PROT "not resname DPPE POPG DOPG TOCL W NA CL and not name CA"
set SEL_BB   "name BB"
set SEL_PO4  "name PO4 PO41 PO42"

proc load_variant {dir xtc label bbcolor} {
    global B SEL_BB SEL_PO4
    mol new      $B/$dir/dome_go_membrane_system.gro type gro waitfor all
    mol addfile  $B/$dir/$xtc                        type xtc waitfor all
    set m [molinfo top]
    mol rename $m $label

    # The .gro is the build structure, not production frame 0 -- drop it so
    # frame N == N ns.
    animate delete beg 0 end 0 $m

    mol delrep 0 $m
    # dome backbone
    mol representation VDW 2.5 12
    mol color ColorID $bbcolor
    mol selection $SEL_BB
    mol addrep $m
    # membrane phosphates, thin -- marks the two leaflet planes
    mol representation Points 3
    mol color ColorID 6
    mol selection $SEL_PO4
    mol addrep $m
    return $m
}

set v4 [load_variant v4 v4_full_1nsframe.xtc "v4 Go intra-only"  0]   ;# blue
set v5 [load_variant v5 v5_full_1nsframe.xtc "v5 Go eps 5.0"     1]   ;# red

# Bond connectivity from the .top. Absolute paths are required: cg_bonds
# derives its #include search dir by splitting -top on "/", so a bare
# filename resolves includes to /martini_ff/ and errors out.
source $B/v4/cg_bonds.tcl
cg_bonds -molid $v4 -top $B/v4/dome_go_membrane_system.top -cutoff 6.2 -topoltype martini
cg_bonds -molid $v5 -top $B/v5/dome_go_membrane_system.top -cutoff 6.2 -topoltype martini

display projection Orthographic
axes location Off
color Display Background white
display resetview

puts ""
puts "v4 = molid $v4 (blue)   v5 = molid $v5 (red)"
puts "toggle:   mol off $v5     /  mol on $v5"
puts "frame 0 is 0 ns; frame 50 is 50 ns"
puts ""
puts "The AA reference contracts 79.65 -> 76.25 A ring radius over 32 ns."
puts "Both of these START near 76 A and end BELOW it -- so check frame 0"
puts "against v2, not the motion. The collapse happened in equilibration."
