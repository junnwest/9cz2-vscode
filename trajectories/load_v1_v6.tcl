# =====================================================================
# Load all six Martini restraint variants (v1-v6) side by side in VMD.
#
#   source /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories/load_v1_v6.tcl
#
# v1 elastic      ef 700, NO inter-chain          (broken baseline)
# v2 flat-bottom  elastic ef 700 + 5,015 inter-chain flat-bottom
# v3 Go           10,612 intra + 4,663 inter Go contacts (replaces elastic)
# v4 Go intra     v3 with the 4,663 inter-chain contacts deleted
# v5 Go weak      v3 with epsilon 9.414 -> 5.0
# v6 ef300        v2 with elastic ef 700 -> 300   (added Aug 5, 2026)
#
# ---------------------------------------------------------------------
# TWO TOPOLOGIES. This is the thing that breaks naive loading:
#   dome_martini_system      177,845 atoms -> v1, v2, v6
#   dome_go_membrane_system  185,885 atoms -> v3, v4, v5
# The Go builds carry 8,040 extra massless virtual sites. Loading a Go
# trajectory against the shared topology fails on atom-count mismatch.
#
# MATCHED WINDOW. All six are 1 ns/frame starting at t=0 (verified), but
# they span wildly different times: v1 1228 ns, v2 1084 ns, v3 1703 ns,
# v4/v5/v6 50 ns. Scrubbing them together frame-by-frame compares
# 300 ns of v1 against a frame that does not exist in v6. With
# MATCHED=1 every molecule is truncated to 0-32 ns (33 frames) -- the
# window the all-atom reference covers -- so frame N is N ns in all six.
# =====================================================================

set B /Users/junnwest/Desktop/26-summer-research/9cz2-vscode/trajectories

# How many ns to load, from t=0. All six are 1 ns/frame, so you get
# WINDOW_NS+1 frames.
#   32  -> 33 frames. Matches the all-atom reference (dome-model is 32 ns).
#          Use this for any AA-vs-CG claim.
#   50  -> 51 frames. The largest window ALL SIX share (v4/v5/v6 end at 50).
#          Use this to compare the CG variants against each other.
#   -1  -> each variant's full length: v1 1228, v2 1084, v3 1703,
#          v4/v5/v6 50 ns. Frame index is then NOT comparable across
#          variants -- frame 300 is 300 ns in v1 and past the end in v6.
set WINDOW_NS 50

# cg_bonds is off by default: it reparses 31 #includes per molecule, and
# six molecules makes that slow for no gain -- the VDW-on-BB representation
# below does not need bond connectivity. Set to 1 if you switch to a
# licorice/cartoon style that does.
set DRAW_BONDS 0

# --- selections -------------------------------------------------------
# "not name CA" hides the 8,040 Go virtual sites, which sit exactly on the
# BB beads (without it every backbone bead in v3/v4/v5 renders twice).
# Harmless on v1/v2/v6 -- those topologies contain no atom named CA.
set SEL_PROT "not resname DPPE POPG DOPG TOCL W NA CL and not name CA"
set SEL_BB   "name BB"
set SEL_PO4  "name PO4 PO41 PO42"

# --- variant table ----------------------------------------------------
#            dir                        gro/top base              trajectory                 label                 color
set VARIANTS {
  {v1  martini/v1_elastic        dome_martini_system      production_1228ns.xtc   "v1 elastic (no inter)"   2}
  {v2  martini/v2_flatbottom     dome_martini_system      production_1084ns.xtc   "v2 flat-bottom"          0}
  {v6  martini_sweep/v6          dome_martini_system      v6_full_1nsframe.xtc    "v6 elastic ef300"       10}
  {v3  martini/v3_go             dome_go_membrane_system  production_1703ns.xtc   "v3 Go"                   1}
  {v4  martini_sweep/v4          dome_go_membrane_system  v4_full_1nsframe.xtc    "v4 Go intra-only"        3}
  {v5  martini_sweep/v5          dome_go_membrane_system  v5_full_1nsframe.xtc    "v5 Go weak eps5.0"      11}
}

array set MOLID {}

foreach v $VARIANTS {
    set key   [lindex $v 0]
    set dir   [lindex $v 1]
    set base  [lindex $v 2]
    set xtc   [lindex $v 3]
    set label [lindex $v 4]
    set col   [lindex $v 5]

    set gro  $B/$dir/$base.gro
    set top  $B/$dir/$base.top
    set traj $B/$dir/$xtc

    if {![file exists $gro]}  { puts "SKIP $key -- missing $gro";  continue }
    if {![file exists $traj]} { puts "SKIP $key -- missing $traj"; continue }

    mol new $gro type gro waitfor all
    set m [molinfo top]

    if {$WINDOW_NS >= 0} {
        mol addfile $traj type xtc first 0 last $WINDOW_NS waitfor all
    } else {
        mol addfile $traj type xtc waitfor all
    }

    # The .gro is the build structure, not production frame 0. Drop it so
    # frame N == N ns.
    animate delete beg 0 end 0 $m
    mol rename $m "$key $label"

    mol delrep 0 $m
    # dome backbone
    mol representation VDW 2.5 12
    mol color ColorID $col
    mol selection $SEL_BB
    mol addrep $m
    # membrane phosphates -- marks the two leaflet planes
    mol representation Points 3
    mol color ColorID 6
    mol selection $SEL_PO4
    mol addrep $m

    if {$DRAW_BONDS} {
        # Absolute path is required: cg_bonds derives its #include search
        # directory by splitting -top on "/", so a bare filename resolves
        # includes to /martini_ff/... and errors out.
        cg_bonds -molid $m -top $top -cutoff 6.2 -topoltype martini
    }

    set MOLID($key) $m
    puts [format "loaded %-3s molid %-3s frames %-5s %s" \
          $key $m [molinfo $m get numframes] $label]
}

if {$DRAW_BONDS} { source $B/martini_sweep/v4/cg_bonds.tcl }

# --- helpers ----------------------------------------------------------
# only v6      -> show just v6
# only {v2 v6} -> show v2 and v6
# showall      -> show everything
proc only {keys} {
    global MOLID
    foreach k [array names MOLID] { mol off $MOLID($k) }
    foreach k $keys {
        if {[info exists MOLID($k)]} { mol on $MOLID($k) } \
        else { puts "no such variant: $k" }
    }
}
proc showall {} {
    global MOLID
    foreach k [array names MOLID] { mol on $MOLID($k) }
}

display projection Orthographic
axes location Off
color Display Background white
display resetview

# Six overlapping domes is unreadable. Start with the two that matter for
# the open question -- v2 (best on ring width so far) and v6 (the new run
# that tests whether softer elastic fixes the reversed vertical direction).
only {v2 v6}

puts ""
if {$WINDOW_NS >= 0} {
    puts "Window 0-$WINDOW_NS ns: [expr {$WINDOW_NS + 1}] frames each, frame N = N ns, comparable."
    if {$WINDOW_NS > 32} {
        puts "  NOTE: the all-atom reference is only 32 ns. Past frame 32 you are"
        puts "  comparing CG variants to each other, not to AA."
    }
} else {
    puts "FULL length: frame index is NOT comparable across variants."
    puts "  v1 1228 ns / v2 1084 / v3 1703 / v4,v5,v6 50 ns"
}
puts ""
puts "showing v2 + v6.   only {v1 v2 v6}   only v3   showall"
puts ""
puts "Elastic family (comparable to AA at frame 0):  v1 gray, v2 blue, v6 cyan"
puts "Go family (pre-compacted -- see below):        v3 red, v4 orange, v5 purple"
puts ""
puts "CAUTION: every Go variant starts production ALREADY collapsed"
puts "  (Rg_xy ~76 A = the all-atom ENDPOINT, vs AA's start of 79.65 A),"
puts "  so their frame-0-to-end motion is not comparable to AA's. v1/v2"
puts "  start at 79.00/79.51, where AA starts. Judge the Go variants on"
puts "  frame 0, not on how far they move."
