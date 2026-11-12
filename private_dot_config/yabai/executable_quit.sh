#!/bin/sh
# skhd runs this on Cmd+Q in place of passing the key on (skhdrc lists the apps it leaves alone). It hides the
# frontmost app, as Cmd+H does, so its windows leave the layout at once instead of when the app gets round to
# closing them (half a second or more for Electron apps like Slack), then sends it Cmd+Q. If the app is still
# running 2 s later (it asks to confirm, is saving or syncing, or the quit was canceled), it's shown again.
pid=$(osascript -l JavaScript -e 'ObjC.import("AppKit"); ObjC.import("CoreGraphics");
  const app = $.NSWorkspace.sharedWorkspace.frontmostApplication;
  app.hide;
  for (const down of [true, false]) {
    const e = $.CGEventCreateKeyboardEvent(null, 12, down);   // 12: the Q key
    $.CGEventSetFlags(e, $.kCGEventFlagMaskCommand);
    $.CGEventPostToPid(app.processIdentifier, e);
  }
  app.processIdentifier')
sleep 2
kill -0 "$pid" 2>/dev/null &&
  osascript -l JavaScript -e "ObjC.import('AppKit'); \$.NSRunningApplication.runningApplicationWithProcessIdentifier($pid).unhide" >/dev/null
