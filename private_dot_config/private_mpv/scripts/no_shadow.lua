-- Fullscreen without the light 1px outline macOS 26 draws around windows, which is part of the
-- window shadow. yabai can turn a window's shadow off, but only for windows it tracks, and it never
-- tracks a window that first shows up fullscreen: mpv's fullscreen window reports the accessibility
-- subrole AXUnknown, which yabai drops on sight. So mpv.conf starts mpv windowed (fullscreen=no);
-- this script waits until yabai has picked up the window, removes its shadow, then goes fullscreen.
-- Each later fullscreen toggle checks the shadow again.

local utils = require "mp.utils"

-- Full path: mpv opened from Finder or `open` doesn't have Homebrew on its PATH
local YABAI = "/opt/homebrew/bin/yabai"
local PID = utils.getpid()

local function yabai(...)
    return mp.command_native({
        name = "subprocess", args = {YABAI, "-m", ...},
        capture_stdout = true, capture_stderr = true, playback_only = false,
    })
end

-- This mpv's window as yabai sees it, once yabai tracks it; nil until then
local function tracked_window()
    local r = yabai("query", "--windows")
    if r.status ~= 0 then return nil end
    for _, w in ipairs(utils.parse_json(r.stdout) or {}) do
        if w.pid == PID and w["has-ax-reference"] then return w end
    end
end

-- has-shadow is read live from macOS, but --toggle flips yabai's own record of the shadow, which is
-- out of date if macOS turned the shadow back on. So toggle until it's really gone, at most twice.
local function remove_shadow()
    for _ = 1, 2 do
        local w = tracked_window()
        if not (w and w["has-shadow"]) then return end
        yabai("window", string.format("%d", w.id), "--toggle", "shadow")
    end
end

local started = false

-- Checks every 50 ms; after 2 s (yabai not running) it goes fullscreen anyway
local function start()
    local tries = 0
    local timer
    timer = mp.add_periodic_timer(0.05, function()
        tries = tries + 1
        local found = tracked_window() ~= nil
        if found or tries >= 40 then
            timer:kill()
            if found then remove_shadow() end
            mp.set_property_bool("fullscreen", true)
        end
    end)
end

mp.observe_property("vo-configured", "bool", function(_, configured)
    if configured and not started then
        started = true
        start()
    end
end)

-- After the window has changed size, in case macOS put the shadow back
mp.observe_property("fullscreen", "bool", function()
    if started then mp.add_timeout(0.3, remove_shadow) end
end)
