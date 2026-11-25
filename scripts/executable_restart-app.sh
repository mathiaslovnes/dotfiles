#!/bin/bash
# Quit the frontmost app the way Cmd+Q does and open it again once it has exited (Karabiner Right Cmd+Shift+Q).
# The app can still ask to save; if the quit is canceled, the script gives up after 30 seconds.

read -r pid app <<< "$(osascript -l JavaScript -e '
  ObjC.import("AppKit");
  const front = $.NSWorkspace.sharedWorkspace.frontmostApplication;
  front.terminate;
  `${front.processIdentifier} ${front.bundleURL.path.js}`')"

for _ in $(seq 150); do
  kill -0 "$pid" 2>/dev/null || exec open "$app"
  sleep 0.2
done
