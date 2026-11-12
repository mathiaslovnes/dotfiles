#!/bin/sh
# skhd runs this on Cmd+Q and passes the key on to the app. The app's tiled windows leave the layout at once
# (floating), instead of when the app gets round to closing them, which takes Electron apps like Slack half a
# second or more. If the app is still running 2 s later (it asked to confirm, or the quit was canceled), they're
# tiled again. Browsers are left alone: a short Cmd+Q there only shows "Hold ⌘Q to quit".
w=$(yabai -m query --windows --window) || exit 0
case $(echo "$w" | jq -r .app) in "Brave Browser"|"Google Chrome") exit 0 ;; esac
pid=$(echo "$w" | jq .pid)
ids=$(yabai -m query --windows | jq --argjson p "$pid" '.[] | select(.pid == $p and ."is-visible" and (."is-floating" | not)) | .id')
[ -n "$ids" ] || exit 0
for id in $ids; do yabai -m window "$id" --toggle float; done
sleep 2
kill -0 "$pid" 2>/dev/null || exit 0
for id in $ids; do
  [ "$(yabai -m query --windows --window "$id" 2>/dev/null | jq '."is-floating" and ."is-visible"')" = true ] &&
    yabai -m window "$id" --toggle float
done
