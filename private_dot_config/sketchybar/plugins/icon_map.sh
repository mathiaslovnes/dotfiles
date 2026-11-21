# The sketchybar-app-font icon for an app (names from the font's own icon_map.sh); other apps get a generic icon
icon_map() {
  case "$1" in
    "Activity Monitor") echo ":activity_monitor:" ;;
    "Anki") echo ":anki:" ;;
    "Brain.fm") echo ":brainfm:" ;;
    "Brave Browser") echo ":brave_browser:" ;;
    "Calendar") echo ":calendar:" ;;
    "Claude") echo ":claude:" ;;
    "Codex") echo ":codex:" ;;
    "DataGrip") echo ":datagrip:" ;;
    "Discord") echo ":discord:" ;;
    "Docker") echo ":docker:" ;;
    "Finder") echo ":finder:" ;;
    "GIMP") echo ":gimp:" ;;
    "kitty") echo ":kitty:" ;;
    "Mail") echo ":mail:" ;;
    "Messages") echo ":messages:" ;;
    "mpv") echo ":mpv:" ;;
    "Music") echo ":music:" ;;
    "Notes") echo ":notes:" ;;
    "Obsidian") echo ":obsidian:" ;;
    "Preview" | "Skim") echo ":preview:" ;;
    "Safari") echo ":safari:" ;;
    "Slack") echo ":slack:" ;;
    "Steam") echo ":steam:" ;;
    "System Settings") echo ":gear:" ;;
    "TickTick") echo ":tick_tick:" ;;
    "VSCodium") echo ":vscodium:" ;;
    "Zen") echo ":zen_browser:" ;;
    "Zotero") echo ":zotero:" ;;
    *) echo ":default:" ;;
  esac
}
