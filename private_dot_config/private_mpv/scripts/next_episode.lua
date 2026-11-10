-- When the last playlist entry starts, queue what comes after it on disk: the next video in the same
-- folder, else the first video of the next season's folder, a sibling whose name matches this one's
-- apart from its numbers ("Show S01" -> "Show S02"). autocreate-playlist only covers the opened folder.
local utils = require "mp.utils"
local VIDEO = {mkv = true, mp4 = true, avi = true, webm = true, mov = true, m4v = true, ts = true}

local function key(s)  -- natural sort: "Ep 2" before "Ep 10"
    return (s:lower():gsub("%d+", function(d) return ("%012d"):format(tonumber(d)) end))
end

local function sorted(list)
    table.sort(list, function(a, b) return key(a) < key(b) end)
    return list
end

local function videos(dir)
    local out = {}
    for _, f in ipairs(utils.readdir(dir, "files") or {}) do
        local ext = f:match("%.([^.]+)$")
        if ext and VIDEO[ext:lower()] then out[#out + 1] = f end
    end
    return sorted(out)
end

local function skeleton(name) return (name:gsub("%d+", "#")) end

local function after(path)
    local dir, file = utils.split_path(path)
    local list = videos(dir)
    for i, f in ipairs(list) do
        if f == file and list[i + 1] then return utils.join_path(dir, list[i + 1]) end
    end
    local parent, name = utils.split_path((dir:gsub("/$", "")))
    local found = false
    for _, d in ipairs(sorted(utils.readdir(parent, "dirs") or {})) do
        if found and skeleton(d) == skeleton(name) then
            local first = videos(utils.join_path(parent, d))[1]
            if first then return utils.join_path(utils.join_path(parent, d), first) end
        end
        if d == name then found = true end
    end
end

mp.register_event("file-loaded", function()
    if mp.get_property_number("playlist-pos", 0) ~= mp.get_property_number("playlist-count", 0) - 1 then return end
    local path = utils.join_path(mp.get_property("working-directory", ""), mp.get_property("path", ""))
    if not utils.file_info(path) then return end  -- streams and URLs
    local nxt = after(path)
    if nxt then mp.commandv("loadfile", nxt, "append") end
end)
