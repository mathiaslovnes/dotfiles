#!/bin/sh
# Some apps (Activity Monitor, Skim's release notes) only hide a window when you close it, and yabai gets no event
# for that, so the window keeps its tile and leaves a hole. Twice a second this floats such a window out of the
# layout (and refocuses, as yabairc's signals do after a real close), and tiles it again once the app shows it
# again. It must look closed on two checks in a row, so the moment of a space switch, when yabai already reports
# the space as visible but its windows aren't shown yet, doesn't count. yabairc starts this.
mem=/tmp/yabai-closed-$(id -u)   # the windows this floated
touch "$mem"
seen=""
while sleep 0.5; do
  spaces=$(yabai -m query --spaces 2>/dev/null | jq -c 'map(select(."is-visible" and .type != "float") | .index)')
  [ -n "$spaces" ] || continue   # yabai isn't running
  now=$(yabai -m query --windows 2>/dev/null | jq -r --argjson s "$spaces" --rawfile m "$mem" '
    ($m | split("\n")) as $ids | .[]
    | select(."has-ax-reference" and (.space | IN($s[])) and (."is-minimized" or ."is-hidden" | not))
    | if (."is-floating" | not) and (."is-visible" | not) then "closed:\(.id)"
      elif ."is-floating" and ."is-visible" and ("\(.id)" | IN($ids[])) then "back:\(.id)"
      else empty end')
  for e in $now; do
    id=${e#*:}
    case $e in
      closed:*)
        case " $seen " in *" $e "*) ;; *) continue ;; esac
        yabai -m window "$id" --toggle float || continue
        echo "$id" >> "$mem"
        sh "$HOME/.config/yabai/refocus.sh" ;;
      back:*)
        yabai -m window "$id" --toggle float || continue
        grep -vx "$id" "$mem" > "$mem.tmp"; mv "$mem.tmp" "$mem" ;;
    esac
  done
  seen=$(echo $now)
done
