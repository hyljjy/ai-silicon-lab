#!/bin/bash -l
# Environment snapshot for the open-source EDA flow (WSL Ubuntu-24.04, user eda).
# Keeps project copies of the helper scripts that live under $HOME, and checks the live environment against them.
#
# Usage (from Windows; needs a login shell for $SKY130_HD / $PDK_ROOT):
#   wsl -d Ubuntu-24.04 --exec bash -l /mnt/d/study/ai_native_design/env/snapshot.sh [check|update]
# check (default): snapshot files match SHA256SUMS; each snapshot file equals its source under $HOME;
#                  liberty files and synth_excluded.cells match sky130hd_kit/MANIFEST.txt; tool binaries match tools.sha256.
#                  Prints SNAPSHOT OK and exits 0, or prints FAIL/DRIFT lines and exits 1.
# update         : copy the sources over the snapshot, rewrite tools.sha256 and SHA256SUMS.
#                  Run only after the environment change has been reviewed, then run check.
set -euo pipefail
cd "$(dirname "$0")"
here=$(pwd)

# snapshot path               source, relative to $HOME
MAP="
open_eda_env.sh               tools/open_eda_env.sh
sky130hd_kit/MANIFEST.txt     pdk/sky130hd_kit/MANIFEST.txt
sky130hd_kit/synth.tcl        pdk/sky130hd_kit/synth.tcl
sky130hd_kit/corners.tcl      pdk/sky130hd_kit/corners.tcl
smoke/sky130/run.sh           smoke/sky130/run.sh
smoke/sky130/sta.tcl          smoke/sky130/sta.tcl
smoke/sky130/mac.v            smoke/sky130/mac.v
smoke/sky130/tb.v             smoke/sky130/tb.v
"
# Relative to $HOME/tools. bin/yosys etc. in oss-cad-suite are wrapper scripts; the real binaries are in libexec/.
TOOLS="opensta/bin/sta oss-cad-suite/libexec/yosys oss-cad-suite/libexec/yosys-abc oss-cad-suite/libexec/iverilog oss-cad-suite/libexec/vvp oss-cad-suite/libexec/verilator_bin"
LICENSES="licenses/sky130_fd_sc_hd.LICENSE licenses/open_pdks.LICENSE"

case ${1:-check} in
  update)
    while read -r dst src; do
      [ -n "$dst" ] || continue
      mkdir -p "$(dirname "$dst")"
      cp "$HOME/$src" "$dst"
    done <<< "$MAP"
    (cd "$HOME/tools" && sha256sum $TOOLS) > tools.sha256
    sha256sum $(awk 'NF {print $1}' <<< "$MAP") tools.sha256 $LICENSES > SHA256SUMS
    echo "UPDATED: $(wc -l < SHA256SUMS) files listed in SHA256SUMS; now run: $0 check"
    ;;
  check)
    : "${SKY130_HD:?not set - run this script with bash -l}" "${PDK_ROOT:?}" "${PDK:?}"
    sha256sum -c --quiet SHA256SUMS || { echo "FAIL: snapshot files do not match SHA256SUMS"; exit 1; }
    bad=0
    while read -r dst src; do
      [ -n "$dst" ] || continue
      cmp -s "$dst" "$HOME/$src" || { echo "DRIFT: $dst differs from ~/$src"; bad=1; }
    done <<< "$MAP"
    (cd "$SKY130_HD/lib" && sha256sum -c --quiet <(grep -E '^[0-9a-f]{64}  .*\.lib$' "$here/sky130hd_kit/MANIFEST.txt")) \
      || { echo "DRIFT: liberty files differ from sky130hd_kit/MANIFEST.txt"; bad=1; }
    (cd "$PDK_ROOT/$PDK/libs.tech/librelane/sky130_fd_sc_hd" \
      && sha256sum -c --quiet <(grep -E '^[0-9a-f]{64}  synth_excluded\.cells$' "$here/sky130hd_kit/MANIFEST.txt")) \
      || { echo "DRIFT: synth_excluded.cells differs from sky130hd_kit/MANIFEST.txt"; bad=1; }
    (cd "$HOME/tools" && sha256sum -c --quiet "$here/tools.sha256") \
      || { echo "DRIFT: tool binaries differ from tools.sha256"; bad=1; }
    [ "$bad" -eq 0 ] || { echo "FAIL: live environment differs from the snapshot"; exit 1; }
    echo "SNAPSHOT OK"
    ;;
  *) echo "usage: $0 [check|update]"; exit 2 ;;
esac
