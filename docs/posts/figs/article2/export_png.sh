#!/usr/bin/env bash
# 把同目录的 *.svg 用本机 Chrome 无头模式导出为 2 倍 PNG（1440 px 宽）。用法：bash docs/posts/figs/article2/export_png.sh
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
for f in *.svg; do
  h=$(grep -o 'height="[0-9]*"' "$f" | head -1 | grep -o '[0-9]*')
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=720,"$h" --screenshot="$(cygpath -w "$PWD/${f%.svg}.png")" "file:///$(cygpath -m "$PWD/$f")" >/dev/null 2>&1
  echo "${f%.svg}.png"
done
