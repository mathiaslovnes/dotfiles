-- Cleans Japanese subtitle files as they're loaded, the way the old clean-up script did by hand:
-- removes (), [], {}, （） and what's inside, ＜＞《》 (keeps the text), arrows, periods (。．.),
-- left-to-right marks, and turns full-width spaces into normal ones.
-- The cleaned copy goes to ~/.cache/mpv-sub-clean and replaces the original track, so the
-- mining script (sub-text) gets the clean text too. The file on disk is never changed.
-- Only subtitle files (.srt, .vtt, .ass, .ssa) with Japanese text; built-in subs and English
-- files are left alone. In .ass files only the dialogue text is touched, not the headers.
-- Work per subtitle line: a bracket that's never closed can't eat the next line's timing.

local ok, mp = pcall(require, "mp")
if not ok then mp = nil end

local CACHE = (os.getenv("HOME") or "/tmp") .. "/.cache/mpv-sub-clean"

-- UTF-8 byte sequences (decimal escapes: plain Lua 5.1 has no \x)
local FW_OPEN, FW_CLOSE = "\239\188\136", "\239\188\137"             -- （ ）
local DROP = {
    "\239\188\156", "\239\188\158", "\227\128\138", "\227\128\139",      -- ＜ ＞ 《 》
    "\227\128\130", "\239\188\142",                                      -- 。 ．
    "\226\128\142",                                                      -- U+200E left-to-right mark
}
local ARROWS = {
    "\226\134[\144-\191]", "\226\135[\128-\191]",                        -- U+2190–21FF
    "\226\158[\148-\191]",                                               -- U+2794–27BF
    "\226\172[\133-\135]", "\226\174\149",                               -- U+2B05–2B07, U+2B95
    "\239\184\143",                                                      -- U+FE0F
    "\240\159[\160-\163][\128-\191]",                                    -- U+1F800–1F8FF
}

local function clean(s)
    local tags = {}  -- keep ASS override tags ({\an8} puts a line at the top); sub-text hides them anyway
    s = s:gsub("{\\[^}]*}", function(t) tags[#tags + 1] = t; return "\1" .. #tags .. "\2" end)
    s = s:gsub("(%d)%.%f[%d]", "%1\3")                                   -- keep decimals (3.5, 1.2.3)
    s = s:gsub("(\239\188[\144-\153])\239\188\142(\239\188[\144-\153])", "%1\4%2")  -- and ３．５
    s = s:gsub("%(.-%)", "")
    s = s:gsub("%[.-%]", "")
    s = s:gsub("{.-}", "")
    s = s:gsub(FW_OPEN .. ".-" .. FW_CLOSE, "")
    for _, d in ipairs(DROP) do s = s:gsub(d, "") end
    for _, a in ipairs(ARROWS) do s = s:gsub(a, "") end
    s = s:gsub("&lrm;?", "")
    s = s:gsub("%.", "")
    s = s:gsub("\227\128\128", " ")                                      -- full-width space
    s = s:gsub("\3", ".")
    s = s:gsub("\4", "\239\188\142")
    s = s:gsub("\1(%d+)\2", function(i) return tags[tonumber(i)] end)
    return s
end

-- lines of one subtitle: cleaned, trimmed, empty ones dropped
local function clean_lines(text)
    local out = {}
    for line in (clean(text) .. "\n"):gmatch("(.-)\n") do
        line = line:gsub("^%s+", ""):gsub("%s+$", "")
        if line:gsub("{\\[^}]*}", ""):match("%S") then out[#out + 1] = line end  -- tags alone count as empty
    end
    return out
end

local function japanese(text)
    local n = 0
    for _ in text:gmatch("\227[\129\130\131][\128-\191]") do               -- hiragana / katakana
        n = n + 1
        if n >= 30 then return true end
    end
    return false
end

-- .srt / .vtt: blocks separated by blank lines; the lines after the timing line are the text
local function clean_srt(text)
    local blocks = {}
    for block in (text .. "\n\n"):gmatch("(.-)\n\n+") do
        local head, body, seen = {}, {}, false
        for line in (block .. "\n"):gmatch("(.-)\n") do
            if seen then body[#body + 1] = line else head[#head + 1] = line end
            if line:find("-->", 1, true) then seen = true end
        end
        if not seen then
            if block:match("%S") then blocks[#blocks + 1] = block end     -- WEBVTT header, notes
        else
            local lines = clean_lines(table.concat(body, "\n"))
            if #lines > 0 then                                              -- nothing left: drop it
                blocks[#blocks + 1] = table.concat(head, "\n") .. "\n" .. table.concat(lines, "\n")
            end
        end
    end
    return table.concat(blocks, "\n\n") .. "\n"
end

-- .ass / .ssa: only the text of Dialogue lines (after the 9th comma); \N line breaks kept
local function clean_ass(text)
    local out = {}
    for line in (text .. "\n"):gmatch("(.-)\n") do
        local prefix, body = line:match("^(Dialogue:[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,)(.*)$")
        if prefix and not body:find("\\p[1-9]") then                     -- vector drawings: leave alone
            local parts = {}
            for _, piece in ipairs(clean_lines((body:gsub("\\[Nn]", "\n")))) do parts[#parts + 1] = piece end
            if #parts > 0 then out[#out + 1] = prefix .. table.concat(parts, "\\N") end
        else
            out[#out + 1] = line
        end
    end
    return table.concat(out, "\n")
end

local function clean_file(text, ext)
    text = text:gsub("^\239\187\191", ""):gsub("\r\n", "\n"):gsub("\r", "\n")   -- BOM, Windows line ends
    if ext == "ass" or ext == "ssa" then return clean_ass(text) end
    return clean_srt(text)
end

if not mp then  -- loaded outside mpv (tests)
    return { clean = clean, clean_file = clean_file, japanese = japanese }
end

local utils = require("mp.utils")
local done = {}  -- original file -> cleaned copy

local function read(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local s = f:read("*a")
    f:close()
    return s
end

local function process()
    for _, t in ipairs(mp.get_property_native("track-list", {})) do
        local path = t["external-filename"]
        local ext = path and path:match("%.(%w+)$")
        ext = ext and ext:lower()
        if t.type == "sub" and t.external and path and not path:find(CACHE, 1, true) and not done[path]
                and (ext == "srt" or ext == "vtt" or ext == "ass" or ext == "ssa")
                and not (t.lang or ""):lower():match("^en") then
            local text = read(path)
            if text and japanese(text) then
                os.execute('mkdir -p "' .. CACHE .. '"')
                local _, name = utils.split_path(path)
                local out = utils.join_path(CACHE, name)
                local f = io.open(out, "wb")
                if f then
                    f:write(clean_file(text, ext))
                    f:close()
                    done[path] = out
                    mp.commandv("sub-add", out, t.selected and "select" or "auto", t.title or name, t.lang or "ja")
                    mp.commandv("sub-remove", tostring(t.id))
                    mp.msg.info("cleaned " .. name)
                end
            end
        end
    end
end

mp.register_event("start-file", function() done = {} end)
mp.register_event("file-loaded", process)
-- subtitle files dropped onto the window or added later
mp.observe_property("track-list/count", "number", function()
    mp.add_timeout(0.1, process)
end)
