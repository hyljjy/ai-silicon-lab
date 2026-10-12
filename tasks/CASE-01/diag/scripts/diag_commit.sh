#!/usr/bin/env bash
# Commit diag files only after the privacy check passes (protocol v0.5 section 10). From Git Bash, repository root:
#   bash tasks/CASE-01/diag/scripts/diag_commit.sh "<commit message>" <path>...
# Stages the given paths, then runs privacy_check.py --staged: it scans the staged content of EVERY staged file (not
# only the given ones, and not the working-tree copies) plus the commit message, and the commit happens only when it
# passes. On failure nothing is committed and the files stay staged for inspection.
set -u
[ $# -ge 2 ] || { echo "usage: diag_commit.sh <message> <path>..."; exit 2; }
msg=$1; shift
git add -- "$@" || exit 1
python -B tasks/CASE-01/diag/scripts/privacy_check.py --staged --message "$msg" || {
  echo "COMMIT FAIL: privacy check failed; nothing committed (files stay staged)"; exit 1; }
git diff --cached --stat
git commit -q -m "$msg" && git log --oneline -1
