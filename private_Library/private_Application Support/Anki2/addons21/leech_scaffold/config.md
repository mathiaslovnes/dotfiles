**enabled**: run after every sync (Tools > Leech scaffold: update now always works).

**fields**: note type → the field whose content puts the sentence on the front.

**graduate_interval_days**: a scaffolded card goes back to word-only once its interval reaches this.

**failed_within_days**: only leeches failed within this many days get the sentence front.

Cards it changes are tagged `leech-scaffold` and have the field set to `scaffold`; it only ever clears a field that still says `scaffold`.
