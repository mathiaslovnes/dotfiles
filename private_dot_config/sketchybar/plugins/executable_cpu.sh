#!/bin/sh
# Total CPU use as a percent of all cores (ps gives each process's percent of one core)
cpu=$(ps -A -o %cpu= | awk -v cores="$(sysctl -n hw.ncpu)" '{ s += $1 } END { printf "%.0f", s / cores }')
sketchybar --set "$NAME" label="$cpu%"
