#!/bin/bash
# Center the focused window on its screen if AeroSpace has it floating
# (AeroSpace has no command to move floating windows)

[ "$(aerospace list-windows --focused --format '%{window-layout}')" = floating ] || exit 0

osascript -l JavaScript <<'EOF'
ObjC.import('AppKit');
const win = Application('System Events').processes.whose({ frontmost: true })[0].windows[0];
const [x, y] = win.position();
const [w, h] = win.size();

// NSScreen frames start at the main screen's bottom left; System Events positions at its top left
const screens = $.NSScreen.screens;
const mainHeight = screens.objectAtIndex(0).frame.size.height;
let target = null;
for (let i = 0; i < screens.count; i++) {
  const f = screens.objectAtIndex(i).visibleFrame;
  const r = { x: f.origin.x, y: mainHeight - (f.origin.y + f.size.height), w: f.size.width, h: f.size.height };
  if (!target) target = r;
  const cx = x + w / 2, cy = y + h / 2;
  if (cx >= r.x && cx < r.x + r.w && cy >= r.y && cy < r.y + r.h) { target = r; break; }
}
win.position = [Math.round(target.x + (target.w - w) / 2), Math.round(target.y + (target.h - h) / 2)];
EOF
