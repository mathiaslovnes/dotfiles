#!/bin/bash
# Let yabai load its scripting addition as root without a password (yabairc runs it through load-sa.sh).
# Run once per Mac: the rule names the path, not the build, so yabai upgrades keep working.
set -e
Y=/opt/homebrew/bin/yabai
T=$(mktemp)
trap 'rm -f "$T"' EXIT
echo "$(whoami) ALL=(root) NOPASSWD: $Y --load-sa" > "$T"
visudo -c -f "$T"   # a malformed sudoers file would stop sudo working at all
sudo install -m 0440 -o root -g wheel "$T" /private/etc/sudoers.d/yabai
sudo -n -l | grep load-sa
