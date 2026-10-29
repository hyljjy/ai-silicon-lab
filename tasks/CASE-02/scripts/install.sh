#!/usr/bin/env bash
# Install one task's files from the scratch implementation directory into their final places (impl_plan Task 0).
#   bash tasks/CASE-02/scripts/install.sh <task>
# Reads tasks/CASE-02/runs/impl/<task>/INSTALL.txt: one "<source relative to that dir> <target relative to repo root>"
# per line. Refuses to overwrite a target that exists with different content; prints both sha256 and exits 1 when
# the copy does not match.
set -u
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
task=${1:?usage: install.sh <task>}
src=$ROOT/tasks/CASE-02/runs/impl/$task
list=$src/INSTALL.txt
[ -f "$list" ] || { echo "INSTALL FAIL: no $list"; exit 1; }
rc=0
while read -r from to; do
  [ -z "${from:-}" ] && continue
  case "$from" in \#*) continue;; esac
  s=$src/$from; t=$ROOT/$to
  [ -f "$s" ] || { echo "INSTALL FAIL: missing source $from"; rc=1; continue; }
  if [ -f "$t" ] && ! cmp -s "$s" "$t"; then echo "INSTALL FAIL: target exists and differs: $to"; rc=1; continue; fi
  mkdir -p "$(dirname "$t")"; cp "$s" "$t"
  a=$(sha256sum "$s" | cut -c1-64); b=$(sha256sum "$t" | cut -c1-64)
  if [ "$a" = "$b" ]; then echo "INSTALLED $to $a"; else echo "INSTALL FAIL: hash mismatch $to"; rc=1; fi
done < "$list"
exit $rc
