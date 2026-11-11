#!/bin/sh
# skhd's resize keys: yabai -m window --resize $1:$2:$3 on the focused window. If the window that should get
# smaller doesn't (its app has a minimum size, so yabai would push it over its neighbor instead), the step is
# undone and that size is remembered, so the next press does nothing.

# key repeats arrive faster than a run finishes; one that arrives during a run is skipped
lock=/tmp/yabai-resize-$(id -u).lock
if ! mkdir "$lock" 2>/dev/null; then
  # a lock older than 2 s was left by a run that died
  [ $(( $(date +%s) - $(stat -f %m "$lock" 2>/dev/null || echo 0) )) -ge 2 ] || exit 0
fi
trap 'rmdir "$lock" 2>/dev/null' EXIT

edge=$1 dx=$2 dy=$3
case $edge in left|right) d=$dx l=w ;; *) d=$dy l=h ;; esac
case $edge in left) dir=west ;; right) dir=east ;; top) dir=north ;; bottom) dir=south ;; esac

x=$(yabai -m query --windows --window | jq '.id // empty')
[ -n "$x" ] || exit 0
if [ "$(yabai -m query --windows --window "$x" | jq '."is-floating"')" = true ]; then
  yabai -m window "$x" --resize "$edge:$dx:$dy"
  exit 0
fi

# the window that gets smaller: the neighbor on that side when this one grows, else this one
case $edge:$d in
  right:[0-9]*|bottom:[0-9]*|left:-*|top:-*) s=$(yabai -m query --windows --window "$dir" 2>/dev/null | jq '.id // empty') ;;
  *) s=$x ;;
esac
len() { yabai -m query --windows --window "$1" | jq --arg l "$l" '.frame[$l] | round'; }
mem=/tmp/yabai-resize-min-$(id -u)-$s-$l

before=$(len "${s:-$x}")
[ -n "$s" ] && [ "$(cat "$mem" 2>/dev/null)" = "$before" ] && exit 0   # still at the minimum it stopped at
yabai -m window "$x" --resize "$edge:$dx:$dy" || exit 0
if [ -n "$s" ] && [ "$(len "$s")" -ge "$before" ]; then
  yabai -m window "$x" --resize "$edge:$((-dx)):$((-dy))"
  echo "$before" > "$mem"
fi
exit 0
