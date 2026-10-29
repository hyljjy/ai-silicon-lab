set c ss_n40C_1v60
# Each find_timing_paths invalidates the PathEnd objects of the previous one (OpenSTA owns them), so every property is
# read right after the call that produced it.
proc c2_count_and_end {args} {
  set pes [find_timing_paths {*}$args]
  set n [llength $pes]
  set e "-"
  if {$n} { set e [get_full_name [get_property [lindex $pes 0] endpoint]] }
  return [list $n $e]
}
foreach p [get_ports {in_b[*]}] {
  set n [get_full_name $p]
  lassign [c2_count_and_end -from $p -path_delay max -scenes $c] mc -
  lassign [c2_count_and_end -from $p -path_delay max -scenes $c -unconstrained] mu me
  lassign [c2_count_and_end -from $p -path_delay min -scenes $c] nc -
  lassign [c2_count_and_end -from $p -path_delay min -scenes $c -unconstrained] nu ne
  puts "PAIR $n max_c=$mc max_u=$mu min_c=$nc min_u=$nu max_u_end=$me min_u_end=$ne scene=$c"
}
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  foreach p [get_ports {in_b[*]}] { puts -nonewline "ARR $c [get_full_name $p] "; flush stdout; report_arrival -scene $c $p }
}
