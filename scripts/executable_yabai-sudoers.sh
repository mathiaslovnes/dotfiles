#!/bin/bash
# Let yabai load its scripting addition as root without a password, for this exact build only: the sudoers
# rule carries the binary's sha256, so a swapped /opt/homebrew/bin/yabai doesn't get root.
# Run after every yabai upgrade (otherwise --load-sa stops matching and the scripting addition doesn't load).
set -e
Y=/opt/homebrew/bin/yabai
T=$(mktemp)
trap 'rm -f "$T"' EXIT
echo "$(whoami) ALL=(root) NOPASSWD: sha256:$(shasum -a 256 "$(readlink -f "$Y")" | cut -d' ' -f1) $Y --load-sa" > "$T"
visudo -c -f "$T"   # a malformed sudoers file would stop sudo working at all
sudo install -m 0440 -o root -g wheel "$T" /private/etc/sudoers.d/yabai
sudo -n -l | grep load-sa
