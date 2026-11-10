-- yabai never tracks a window that first shows up in mpv's fullscreen, so mpv.conf starts mpv
-- windowed (fullscreen=no); this goes fullscreen once yabai has the window, so yabai can still
-- move and focus it. After 2 s (yabai not running) it goes fullscreen anyway.
local utils = require "mp.utils"
local YABAI = "/opt/homebrew/bin/yabai"
local PID = utils.getpid()

local function tracked()
    local r = mp.command_native({
        name = "subprocess", args = {YABAI, "-m", "query", "--windows"},
        capture_stdout = true, capture_stderr = true, playback_only = false,
    })
    if r.status ~= 0 then return false end
    for _, w in ipairs(utils.parse_json(r.stdout) or {}) do
        if w.pid == PID and w["has-ax-reference"] then return true end
    end
    return false
end

local started = false
mp.observe_property("vo-configured", "bool", function(_, configured)
    if not configured or started then return end
    started = true
    local tries = 0
    local timer
    timer = mp.add_periodic_timer(0.05, function()
        tries = tries + 1
        if tracked() or tries >= 40 then
            timer:kill()
            mp.set_property_bool("fullscreen", true)
        end
    end)
end)
