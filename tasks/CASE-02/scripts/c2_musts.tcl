# CASE-02 must-check items (protocol v0.3 sections 5.3, 5.4). Run by run_context.py in a fresh process:
#   sta -no_init -no_splash -exit c2_musts.tcl
# Env: the driver's variables plus DRIVER, MUSTS_DIR (rules/musts), CASE02_NONCE. Rebuilds the context by sourcing
# the driver (its records go to OUTDIR and are compared with the context run), then sources every MUSTS_DIR/M*.tcl
# in name order between nonce-tagged markers; run_context.py splits the output into musts/M<nn>.txt.
source $::env(DRIVER)
set M "CASE02-$::env(CASE02_NONCE)"
set scenes {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95}
foreach f [lsort [glob -directory $::env(MUSTS_DIR) M*.tcl]] {
  set id [string range [file tail $f] 0 2]
  puts "=== $M MUST $id BEGIN ==="
  flush stdout
  set rc [catch {source $f} res]
  if {$rc} { puts "MUST-ERROR: $res" }
  flush stdout
  puts "=== $M MUST $id END rc=$rc ==="
  flush stdout
}
