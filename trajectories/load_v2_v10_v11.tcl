# Load v2 (flat-bottom), v10 (no elastic, real SS), v11 (elastic ef700, real SS)
# side by side, 0-32 ns matched window, with bonds correctly drawn from EACH
# variant's own topology.
#
#   source .../trajectories/load_v2_v10_v11.tcl
#
# v2 and v11 both carry elastic bonds (ef 700 each) but different secondary
# structure (v2 all-coil, v11 real) -- NOT the same topology, do not reuse one
# for the other. v10 has no elastic bonds at all -- cg_bonds on it will only
# draw the SS-dependent bonded terms (real helices/sheets), nothing else.

set B /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories

proc load_variant {dir xtcfile label color {first_frame 0} {last_frame 32}} {
    global B
    set gro $dir/dome_martini_system.gro
    set top $dir/dome_martini_system.top
    set xtc $dir/$xtcfile

    mol new $gro type gro waitfor all
    set m [molinfo top]
    mol addfile $xtc type xtc first $first_frame last $last_frame waitfor all
    animate delete beg 0 end 0 $m      ;# the .gro is the build frame, not frame 0 of production
    mol rename $m $label

    mol delrep 0 $m
    mol representation VDW 2.5 12
    mol color ColorID $color
    mol selection "name BB"
    mol addrep $m
    mol representation Points 3
    mol color ColorID 6
    mol selection "name PO4 PO41 PO42"
    mol addrep $m

    # cg_bonds requires cd into the topology's own directory and a bare ./
    # relative -top path -- it derives the #include search dir by splitting
    # on "/", which breaks on an absolute path passed directly.
    set cwd [pwd]
    cd $dir
    cg_bonds -molid $m -top ./dome_martini_system.top -cutoff 6.2 -topoltype martini
    cd $cwd

    puts [format "loaded %-4s molid %-3s frames %-4s  %s" \
          [file tail $dir] $m [molinfo $m get numframes] $label]
    return $m
}

# cg_bonds.tcl only needs to be sourced once, reused for every load_variant call
source $B/martini/v2_flatbottom/cg_bonds.tcl

set v2  [load_variant $B/martini/v2_flatbottom production_1084ns.xtc "v2 flat-bottom (ef700, coil)"   0]
set v10 [load_variant $B/martini_sweep/v10     v10_0-32ns.xtc        "v10 no-elastic, real SS"        1]
set v11 [load_variant $B/martini_sweep/v11     v11_0-32ns.xtc        "v11 elastic ef700, real SS"     4]

display projection Orthographic
axes location Off
color Display Background white
display resetview

proc only {keys} {
    global v2 v10 v11
    foreach k {v2 v10 v11} { mol off [set $k] }
    foreach k $keys {
        if {[info exists ::$k]} { mol on [set ::$k] } else { puts "no such variant: $k" }
    }
}

puts ""
puts "v2 = molid $v2 (blue)   v10 = molid $v10 (red)   v11 = molid $v11 (yellow)"
puts "all three: 0-32 ns, frame N = N ns"
puts "toggle:  only {v2 v11}   /   only v10   /   only {v2 v10 v11}"
