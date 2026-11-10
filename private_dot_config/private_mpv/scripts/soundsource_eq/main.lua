-- Your SoundSource Output EQ, applied by mpv itself.
--
-- SoundSource's capture crackles when you switch from mpv to Brave/Claude, so mpv is meant to
-- be in SoundSource's exclusion list (mpv then plays straight to the DAC). This puts the same
-- EQ back: eq.py reads it from SoundSource's settings each time mpv starts. If mpv isn't
-- excluded, eq.py returns nothing and SoundSource applies the EQ as before (never twice).
local utils = require "mp.utils"

local res = utils.subprocess({
    args = {"/usr/bin/python3", mp.get_script_directory() .. "/eq.py"},
    capture_stdout = true, playback_only = false,
})
local chain = (res.stdout or ""):gsub("%s+$", "")
if res.status == 0 and chain ~= "" then
    mp.commandv("af", "add", "@soundsource-eq:lavfi=[" .. chain .. "]")
    mp.msg.info("SoundSource EQ: " .. chain)
end
