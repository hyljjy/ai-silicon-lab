#!/usr/bin/env bash
# Run a command in the WSL Ubuntu-24.04 login shell, from tasks/CASE-01, with pipefail. From Git Bash:
#   bash tasks/CASE-01/diag/scripts/wsl.sh '<command>'
#   bash tasks/CASE-01/diag/scripts/wsl.sh <<'EOF'
#   <several lines>
#   EOF
# The command text is piped to `bash -l -s`, so nothing is written to disk and no quoting is re-parsed by Windows.
# Commands run this way must not read stdin themselves. WSL may clear /tmp between calls (SYS-008): keep state that a
# later call needs in files under the repository, never in /tmp.
set -u
CASE=/mnt/d/study/ai_native_design/tasks/CASE-01
if [ $# -gt 0 ]; then cmd="$*"; else cmd=$(cat); fi
printf '%s\n' 'set -o pipefail' "cd $CASE || exit 99" "$cmd" | MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 --exec bash -l -s
