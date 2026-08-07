# Per-segment secondary structure for large all-atom systems.
#
#   source .../trajectories/namd/stride_by_segment.tcl
#   stride_by_segment            ;# operates on top molecule
#   stride_by_segment 0          ;# or a specific molid
#
# WHY THIS IS NEEDED
# VMD computes secondary structure by writing the protein to a temporary PDB and
# calling the stride binary. The PDB atom-serial field is 5 characters, so that
# breaks above 99,999 atoms. The 24-chain dome has 126,696 protein atoms, so
# `mol ssrecalc` fails with:
#     ERROR) Unable to find Stride output file: /var/tmp/tmp.N.xxxxxx
#     ERROR) Call to Stride program failed.
# VMD then leaves every residue as coil, which looks like "STRIDE isn't working"
# rather than an error. Verified: stride succeeds on a single 5,313-atom chain
# from this very system and fails on the whole protein.
#
# This runs stride once per segname (each ~5,300 atoms, comfortably under the
# limit) and writes the results back into the `structure` field, so New Cartoon
# and `helix`/`sheet`/`coil` selections work normally afterwards.
#
# Display-only: touches nothing but the in-memory `structure` field.

proc stride_by_segment {{molid top}} {
    if {$molid eq "top"} { set molid [molinfo top] }

    if {![info exists ::env(STRIDE_BIN)]} {
        error "STRIDE_BIN not set -- cannot locate the stride binary"
    }
    set stride $::env(STRIDE_BIN)
    if {![file executable $stride]} {
        error "stride binary not executable: $stride"
    }

    set all [atomselect $molid "protein"]
    set segs [lsort -unique [$all get segname]]
    $all delete
    if {[llength $segs] == 0} { error "no protein atoms in molid $molid" }

    set tmp [file join /tmp vmd_stride_seg_[pid].pdb]
    set nseg 0
    set nres 0

    foreach seg $segs {
        set sel [atomselect $molid "protein and segname $seg"]
        if {[$sel num] == 0} { $sel delete; continue }
        $sel writepdb $tmp

        if {[catch {exec $stride $tmp} out]} {
            # stride returns nonzero on some inputs but still prints ASG records
            if {![string match "*ASG*" $out]} {
                puts "  $seg: stride FAILED -- left as coil"
                $sel delete
                continue
            }
        }

        # Fixed-column ASG format:
        #   ASG  ARG P   79    1    H    AlphaHelix   360.00  -40.21  260.9
        #        ^resname  ^resid    ^ss-code(col 24)
        set ss [dict create]
        foreach line [split $out "\n"] {
            if {![string match "ASG *" $line]} { continue }
            set resid [string trim [string range $line 11 15]]
            set code  [string trim [string range $line 24 24]]
            if {$resid ne "" && $code ne ""} { dict set ss $resid $code }
        }

        # One `set structure` per segment, ordered to match the selection --
        # far faster than a per-residue atomselect (8,040 residues here).
        set codes {}
        foreach r [$sel get resid] {
            if {[dict exists $ss $r]} {
                lappend codes [dict get $ss $r]
            } else {
                lappend codes "C"   ;# stride skips chain termini
            }
        }
        $sel set structure $codes

        incr nseg
        incr nres [dict size $ss]
        $sel delete
    }
    file delete -force $tmp

    set chk [atomselect $molid "protein"]
    set found [lsort -unique [$chk get structure]]
    $chk delete
    puts "stride_by_segment: $nseg segments, $nres residues assigned"
    puts "  secondary structure codes present: $found"
    if {[llength $found] <= 1} {
        puts "  WARNING: still only one code -- assignment did not take"
    }
    return
}
