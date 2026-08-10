# Load and visualize all 11 Martini restraint-scheme variants (v1-v11) in one
# fresh VMD session, 0-32 ns matched window, each drawing bonds from its OWN
# topology (never a borrowed one -- see the v6/v11 mixup this project already
# made once).
#
#   source .../trajectories/load_all_martini.tcl
#
# TWO TOPOLOGY FAMILIES -- do not cross them:
#   shared (177,845 atoms): v1, v2, v6, v7, v8, v9, v10, v11
#   Go     (185,885 atoms, +8,040 CA virtual sites): v3, v4, v5
# Loading a Go .xtc against the shared .gro (or vice versa) fails on atom count.

set B /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories

proc load_martini_variant {dir gro top xtc label color {first_frame 0} {last_frame 32}} {
    mol new $dir/$gro type gro waitfor all
    set m [molinfo top]
    mol addfile $dir/$xtc type xtc first $first_frame last $last_frame waitfor all
    animate delete beg 0 end 0 $m      ;# .gro is the build frame, not production frame 0
    mol rename $m $label

    mol delrep 0 $m
    mol representation VDW 2.5 12
    mol color ColorID $color
    mol selection "name BB and not name CA"   ;# "not name CA" strips the 8,040 Go virtual
    mol addrep $m                              ;# sites in v3/v4/v5; harmless no-op elsewhere
    mol representation Points 3
    mol color ColorID 6
    mol selection "name PO4 PO41 PO42"
    mol addrep $m

    # cg_bonds needs cd into the topology's own dir + a bare ./ relative path --
    # it derives the #include search dir by splitting on "/", which breaks on
    # an absolute path. Drawing from $dir's own $top, never another variant's.
    set cwd [pwd]
    cd $dir
    cg_bonds -molid $m -top ./$top -cutoff 6.2 -topoltype martini
    cd $cwd

    puts [format "loaded %-4s molid %-3s frames %-4s  %s" [file tail $dir] $m [molinfo $m get numframes] $label]
    return $m
}

source $B/martini/v2_flatbottom/cg_bonds.tcl

# key: dir  gro  top  xtc  label  color  [first last]  -- last two omitted where
# the xtc is already the pre-extracted 0-32 ns window (no re-trimming needed)
set VARIANTS {
  {v1  martini/v1_elastic        dome_martini_system.gro     dome_martini_system.top     production_1228ns.xtc  "v1 elastic (no inter)"    2   0 32}
  {v2  martini/v2_flatbottom     dome_martini_system.gro     dome_martini_system.top     production_1084ns.xtc  "v2 flat-bottom"           0   0 32}
  {v3  martini/v3_go             dome_go_membrane_system.gro dome_go_membrane_system.top production_1703ns.xtc  "v3 Go"                    1   0 32}
  {v4  martini_sweep/v4          dome_go_membrane_system.gro dome_go_membrane_system.top prod_v.xtc              "v4 Go intra-only"         3   0 32}
  {v5  martini_sweep/v5          dome_go_membrane_system.gro dome_go_membrane_system.top prod_v.xtc              "v5 Go weak eps5.0"       11   0 32}
  {v6  martini_sweep/v6          dome_martini_system.gro     dome_martini_system.top     v6_0-32ns.xtc           "v6 elastic ef300"        10   0 32}
  {v7  martini_sweep/v7          dome_martini_system.gro     dome_martini_system.top     v7_0-32ns.xtc           "v7 elastic ef1500"        9   0 32}
  {v8  martini_sweep/v8          dome_martini_system.gro     dome_martini_system.top     v8_0-32ns.xtc           "v8 elastic ef3000"       12   0 32}
  {v9  martini_sweep/v9          dome_martini_system.gro     dome_martini_system.top     v9_0-32ns.xtc           "v9 ef700 corrected-EM"   14   0 32}
  {v10 martini_sweep/v10         dome_martini_system.gro     dome_martini_system.top     v10_0-32ns.xtc          "v10 no-elastic real-SS"   4   0 32}
  {v11 martini_sweep/v11         dome_martini_system.gro     dome_martini_system.top     v11_0-32ns.xtc          "v11 elastic ef700 real-SS" 5  0 32}
}

array set MOLID {}
foreach v $VARIANTS {
    set key   [lindex $v 0]
    set dir   $B/[lindex $v 1]
    set gro   [lindex $v 2]
    set top   [lindex $v 3]
    set xtc   [lindex $v 4]
    set label [lindex $v 5]
    set color [lindex $v 6]
    set f0    [lindex $v 7]
    set f1    [lindex $v 8]
    set MOLID($key) [load_martini_variant $dir $gro $top $xtc "$key $label" $color $f0 $f1]
}

display projection Orthographic
axes location Off
color Display Background white
display resetview

proc only {keys} {
    global MOLID
    foreach k [array names MOLID] { mol off $MOLID($k) }
    foreach k $keys {
        if {[info exists MOLID($k)]} { mol on $MOLID($k) } else { puts "no such variant: $k" }
    }
}
proc showall {} { global MOLID; foreach k [array names MOLID] { mol on $MOLID($k) } }

# 11 molecules at once is unreadable -- start on the comparison that matters
only {v2 v10 v11}

puts ""
puts "All 11 loaded, hidden except v2/v10/v11. 0-32 ns, frame N = N ns."
puts "  only v6              -- show one"
puts "  only {v1 v2 v6 v9}   -- show several (the elastic family)"
puts "  only {v3 v4 v5}      -- the Go family (pre-collapsed, see CLAUDE.md)"
puts "  showall"
puts ""
puts "Elastic family (comparable to AA at frame 0): v1,v2,v6,v7,v8,v9 gray/blue/tan tones"
puts "Go family (pre-collapsed, NOT comparable to AA motion): v3,v4,v5"
puts "Real secondary structure (the open question): v10 (no elastic) vs v11 (elastic ef700)"
