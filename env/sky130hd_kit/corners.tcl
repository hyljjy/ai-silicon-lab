# OpenSTA 3.x: multi-corner (scene) setup for sky130_fd_sc_hd.
# Usage:
#   source $::env(SKY130_KIT)/corners.tcl
#   sky130_read_libs std            ;# std (default) | sweep | all | {tt_025C_1v80 ss_n40C_1v60 ...}
#   read_verilog ...; link_design ...; create_clock ... (SDC)
#   sky130_define_scenes            ;# one scene per corner, named like tt_025C_1v80
#   report_checks -scene ss_n40C_1v60 ; worst_slack -scene ff_100C_1v95 -min
# Corner sets (project rule, PLAN_v1.0 revision R1):
#   std   = 6 PVT check points (tt 1.80V / ss 1.60V / ff 1.95V, each at two temperatures)
#           -> main text of reports; a project grouping, not a signoff set
#   sweep = the other 10 NLDM PVT points (non-standard supply voltages, mixed process/temperature)
#           -> appendix supplementary scan only; only same process+temperature points form a voltage series
#   all   = std + sweep (16); *_ccsnoise variants are never included
# tt_025C_1v80 is always read first: the first library read sets units for SDC/reports.

proc sky130_corner_list {{set std}} {
  set std {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95}
  switch -- $set {
    std { return $std }
    sweep - all {
      set sweep {}
      foreach f [lsort [glob $::env(SKY130_HD)/lib/sky130_fd_sc_hd__*.lib]] {
        set c [string map {sky130_fd_sc_hd__ "" .lib ""} [file tail $f]]
        if {![string match *ccsnoise* $c] && [lsearch -exact $std $c] < 0} { lappend sweep $c }
      }
      if {$set eq "sweep"} { return $sweep }
      return [concat $std $sweep]
    }
    default { return $set }
  }
}

proc sky130_read_libs {{set std}} {
  global sky130_corners
  set sky130_corners [sky130_corner_list $set]
  if {[lindex $sky130_corners 0] ne "tt_025C_1v80"} {
    # keep units anchored to tt; the extra library is read but gets no scene
    read_liberty $::env(SKY130_HD)/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
  }
  foreach c $sky130_corners {
    read_liberty $::env(SKY130_HD)/lib/sky130_fd_sc_hd__$c.lib
  }
  return $sky130_corners
}

proc sky130_define_scenes {} {
  global sky130_corners
  foreach c $sky130_corners {
    define_scene $c -liberty sky130_fd_sc_hd__$c
  }
}
