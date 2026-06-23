#!/usr/bin/env vmd -dispdev text -e
# Rotate M3 tail (resid 356-419) on each HflK chain to minimize CA-CA clashes.
# Rotation axis: CA(355) -> CA(356) bond at the known/predicted junction.
# Tries 24 angles in 15-degree steps, picks angle with fewest clashes < 3.8 A.
#
# Run:
#   /Applications/VMD\ 1.9.4a57-arm64-Rev12.app/Contents/MacOS/startup.command \
#     -dispdev text -e /Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode/scripts/declash_m3.tcl

# --- Rodrigues rotation matrix about axis through pivot point ---
proc rot_about_axis {pivot axis angle_deg} {
    set pi 3.14159265358979
    set theta [expr {$angle_deg * $pi / 180.0}]
    set c [expr {cos($theta)}]
    set s [expr {sin($theta)}]
    set t [expr {1.0 - $c}]

    set len [expr {sqrt([lindex $axis 0]**2 + [lindex $axis 1]**2 + [lindex $axis 2]**2)}]
    set ux [expr {[lindex $axis 0] / $len}]
    set uy [expr {[lindex $axis 1] / $len}]
    set uz [expr {[lindex $axis 2] / $len}]

    set px [lindex $pivot 0]; set py [lindex $pivot 1]; set pz [lindex $pivot 2]

    # 3x3 rotation (Rodrigues)
    set r00 [expr {$t*$ux*$ux + $c}];     set r01 [expr {$t*$ux*$uy - $s*$uz}]; set r02 [expr {$t*$ux*$uz + $s*$uy}]
    set r10 [expr {$t*$ux*$uy + $s*$uz}]; set r11 [expr {$t*$uy*$uy + $c}];     set r12 [expr {$t*$uy*$uz - $s*$ux}]
    set r20 [expr {$t*$ux*$uz - $s*$uy}]; set r21 [expr {$t*$uy*$uz + $s*$ux}]; set r22 [expr {$t*$uz*$uz + $c}]

    # Translation to rotate about pivot (not origin)
    set tx [expr {$px - $r00*$px - $r01*$py - $r02*$pz}]
    set ty [expr {$py - $r10*$px - $r11*$py - $r12*$pz}]
    set tz [expr {$pz - $r20*$px - $r21*$py - $r22*$pz}]

    # VMD 4x4 matrix: nested list of 4 rows {{r00 r01 r02 tx} ...}
    # p' = M * p  (column vector convention, translation in last column)
    return [list \
        [list $r00 $r01 $r02 $tx] \
        [list $r10 $r11 $r12 $ty] \
        [list $r20 $r21 $r22 $tz] \
        [list 0    0    0    1  ]]
}

set base "/Users/jun-seoyang/Desktop/Grind/UChicago/26-summer-research/9cz2-vscode"
set inp  "$base/9cz2_with_hflk_m3.pdb"
set out  "$base/9cz2_m3_deClashed.pdb"

mol load pdb $inp
set mol [molinfo top get id]
puts "Loaded mol $mol"

set hflk_chains {A C E G I K M O Q S U X}

foreach chain $hflk_chains {
    set sel355 [atomselect $mol "chain $chain and resid 355 and name CA"]
    set sel356 [atomselect $mol "chain $chain and resid 356 and name CA"]

    if {[$sel355 num] == 0 || [$sel356 num] == 0} {
        puts "Chain $chain: missing CA at res 355 or 356 — skipping"
        $sel355 delete; $sel356 delete
        continue
    }

    # Pivot = CA(355), second point for axis = CA(356) at original position
    set pivot [lindex [$sel355 get {x y z}] 0]
    set p356  [lindex [$sel356 get {x y z}] 0]
    set axis  [list \
        [expr {[lindex $p356 0] - [lindex $pivot 0]}] \
        [expr {[lindex $p356 1] - [lindex $pivot 1]}] \
        [expr {[lindex $p356 2] - [lindex $pivot 2]}]]
    $sel355 delete; $sel356 delete

    set m3    [atomselect $mol "chain $chain and resid 356 to 419"]
    set m3_ca [atomselect $mol "chain $chain and resid 356 to 419 and name CA"]
    set other [atomselect $mol "not (chain $chain and resid 356 to 419) and name CA"]

    set orig [$m3 get {x y z}]

    set best_angle   0
    set best_clashes 999999

    for {set angle 0} {$angle < 360} {incr angle 15} {
        $m3 set {x y z} $orig

        if {$angle > 0} {
            set M [rot_about_axis $pivot $axis $angle]
            $m3 move $M
        }

        set contacts [measure contacts 3.8 $m3_ca $other]
        set nclash [llength [lindex $contacts 0]]

        if {$nclash < $best_clashes} {
            set best_clashes $nclash
            set best_angle $angle
        }
    }

    # Apply best rotation permanently
    $m3 set {x y z} $orig
    if {$best_angle > 0} {
        set M [rot_about_axis $pivot $axis $best_angle]
        $m3 move $M
    }

    puts "Chain $chain: best = ${best_angle} deg, CA clashes remaining = $best_clashes"

    $m3 delete; $m3_ca delete; $other delete
}

set all [atomselect $mol "all"]
$all writepdb $out
$all delete
mol delete $mol

puts "\nDone. Output: $out"
quit
