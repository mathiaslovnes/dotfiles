**rule**: `"average"` (default): a card's score is the average frequency rank of its word and the other words in its sentence you haven't met in a reviewed card and no new card teaches; never better than its own word's rank. `"most_common"`: the smallest of those ranks.

**one_day**: how many new cards make a day, for the gap between a card and the card teaching a word it needs. `"auto"`: the median number of new cards you learned on your last 30 study days.

**unranked**: the rank given to a word with no frequency data.

Ranks are the freq-harmonic-mean number: a card's own field, and for other words the same number from Yomitan's `frequency-harmonic-rank-custom` marker (Brave must be open; looked-up words are cached).

**note_types**: `order: true` for the note types whose new cards are ordered; the others only tell which words you know. Words of each sentence come from the Sentence pitch add-on (`word_deps`, empty = its user_files/word_deps.json).
