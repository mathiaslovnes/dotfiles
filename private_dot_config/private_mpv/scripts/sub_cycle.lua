-- Turn Japanese (primary slot, bottom) and English (secondary slot, top) subtitles on and off,
-- and remove added subtitle files. Each action shows a message on screen.

local function track_id(prop)
    local v = mp.get_property_native(prop)
    if type(v) == "number" then return v end
end

local function describe(t)
    local parts = {}
    if t.lang then parts[#parts + 1] = t.lang end
    if t.title then parts[#parts + 1] = '"' .. t.title .. '"' end
    if #parts == 0 then parts[1] = t.codec or "" end
    return table.concat(parts, " ")
end

local function lang_starts_with(t, ...)
    local lang = (t.lang or ""):lower()
    for _, prefix in ipairs({...}) do
        if lang:sub(1, #prefix) == prefix then return true end
    end
    return false
end

-- English is anything tagged English. Japanese is anything tagged Japanese, or an added
-- subtitle file that isn't English, since added files rarely carry a language tag.
local function is_wanted(t, lang)
    if lang == "en" then return lang_starts_with(t, "en") end
    return lang_starts_with(t, "ja", "jp") or (t.external and not lang_starts_with(t, "en"))
end

-- Track last turned off per slot, so turning it back on brings back the same one
local last_off = {}

-- Keeps the preferred track (selected or last turned off); otherwise prefers a file you added over a built-in one.
local function find_track(lang, current)
    local found = {}
    for _, t in ipairs(mp.get_property_native("track-list", {})) do
        if t.type == "sub" and is_wanted(t, lang) then
            if t.id == current then return t end
            found[#found + 1] = t
        end
    end
    for _, t in ipairs(found) do
        if t.external then return t end
    end
    return found[1]
end

local function toggle(name, lang, prop, other_prop, visibility_prop)
    local current = track_id(prop)
    local t = find_track(lang, current or last_off[prop])
    if not t then
        mp.commandv("show-text", "no " .. name .. " subs found", 1500)
        return
    end
    if t.id == current and mp.get_property_bool(visibility_prop) then
        last_off[prop] = t.id
        mp.set_property(prop, "no")
        mp.commandv("show-text", name .. " subs: off", 1500)
        return
    end
    -- mpv won't show one track in both slots, so take it out of the other slot first
    if track_id(other_prop) == t.id then mp.set_property(other_prop, "no") end
    mp.set_property_number(prop, t.id)
    mp.set_property_bool(visibility_prop, true)
    mp.commandv("show-text", string.format("%s subs: on %s", name, describe(t)), 1500)
end

-- Removes the selected track from this session. mpv can only do that for added subtitle files.
local function remove(prop, label)
    local id = track_id(prop)
    if not id then
        mp.commandv("show-text", label .. ": no track selected", 1500)
        return
    end
    local all, track = {}, nil
    for _, t in ipairs(mp.get_property_native("track-list", {})) do
        if t.type == "sub" then
            all[#all + 1] = t
            t.pos = #all
            if t.id == id then track = t end
        end
    end
    if not (track and track.external) then
        mp.commandv("show-text", string.format("%s: %d/%d is built into the video, can't remove it", label, track and track.pos or 0, #all), 2500)
        return
    end
    mp.commandv("sub-remove", tostring(id))
    mp.commandv("show-text", string.format("removed %s: %s", label, describe(track)), 1500)
end

mp.add_key_binding(nil, "japanese", function()
    toggle("Japanese", "ja", "sid", "secondary-sid", "sub-visibility")
end)
mp.add_key_binding(nil, "english", function()
    toggle("English", "en", "secondary-sid", "sid", "secondary-sub-visibility")
end)
mp.add_key_binding(nil, "remove", function() remove("sid", "sub") end)
mp.add_key_binding(nil, "secondary-remove", function() remove("secondary-sid", "secondary sub") end)
