# Per-frame secondary structure caching for large all-atom systems (>99,999 protein atoms).
#
#   source .../trajectories/namd/stride_by_segment.tcl   ;# REQUIRED FIRST — defines stride_by_segment
#   source .../trajectories/namd/sscache_by_segment.tcl
#   start_sscache            ;# begin caching for the top molecule
#   stop_sscache              ;# stop (one stop per start)
#   reset_sscache             ;# clear all cached frames
#
# This is Andrew Dalke's sscache.tcl (ks.uiuc.edu/Research/vmd/script_library/sscache/)
# adapted for this project. The original computes secondary structure via VMD's built-in
# `vmd_calculate_structure`, which writes the whole protein to a temporary PDB for stride
# to read — the same 5-digit atom-serial overflow that made `mol ssrecalc` fail silently
# on this system (see stride_by_segment.tcl). Every recompute here would come back coil,
# same as before that fix existed.
#
# The only change from the original: the recompute step calls `stride_by_segment $index`
# (per-segment, ~5,300 atoms each, under the limit) instead of `vmd_calculate_structure`.
# Caching still matters here BECAUSE this is slower than the built-in call (it invokes
# stride once per segment, ~24-37 external processes per frame) -- exactly why you want
# each frame computed once and replayed instantly afterward, not recomputed on every scrub.

proc start_sscache {{molid top}} {
    global sscache_data
    if {! [string compare $molid top]} {
        set molid [molinfo top]
    }
    global vmd_frame
    trace variable vmd_frame($molid) w sscache
    return
}

proc stop_sscache {{molid top}} {
    if {! [string compare $molid top]} {
        set molid [molinfo top]
    }
    global vmd_frame
    trace vdelete vmd_frame($molid) w sscache
    return
}

proc reset_sscache {} {
    global sscache_data
    if [info exists sscache_data] {
        unset sscache_data
    }
    return
}

proc sscache {name index op} {
    global sscache_data

    set sel [atomselect $index "protein name CA"]
    set frame [molinfo $index get frame]

    if [info exists sscache_data($index,$frame)] {
        $sel set structure $sscache_data($index,$frame)
        $sel delete
        return
    }

    # stride_by_segment must already be defined (source stride_by_segment.tcl first)
    stride_by_segment $index
    set sscache_data($index,$frame) [$sel get structure]
    $sel delete

    return
}
