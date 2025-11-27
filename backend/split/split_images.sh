#!/usr/bin/env bash
set -e
D="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$D/new-imgs"
shopt -s nullglob nocaseglob
for f in "$D/imgs"/*.{png,jpg,jpeg,gif,bmp,webp,tiff}; do
  b=$(basename "$f" | sed 's/\.[^.]*$//')
  convert "$f" -crop 2x2@ +repage "$D/imgs/${b}_%d.png" 2>/dev/null && \
  for i in 0 1 2 3; do mv "$D/imgs/${b}_$i.png" "$D/new-imgs/${b}_$((i+1)).png" 2>/dev/null; done
done
