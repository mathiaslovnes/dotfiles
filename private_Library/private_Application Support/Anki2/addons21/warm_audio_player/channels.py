"""Tell whether an audio file is mono by reading its header (microseconds; no ffprobe)."""
import os

_MP3_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}


def _mp3_mono(f) -> bool | None:
    head = f.read(10)
    off = 0
    if head[:3] == b"ID3":
        size = (head[6] & 0x7F) << 21 | (head[7] & 0x7F) << 14 | (head[8] & 0x7F) << 7 | (head[9] & 0x7F)
        off = 10 + size + (10 if head[5] & 0x10 else 0)
    f.seek(off)
    buf = f.read(16384)
    for j in range(len(buf) - 4):
        if buf[j] != 0xFF or buf[j + 1] & 0xE0 != 0xE0:
            continue
        version = (buf[j + 1] >> 3) & 3   # 3: MPEG-1, 2: MPEG-2, 0: MPEG-2.5, 1: reserved
        layer = (buf[j + 1] >> 1) & 3
        bitrate = buf[j + 2] >> 4
        rate = (buf[j + 2] >> 2) & 3
        if version == 1 or layer == 0 or bitrate in (0, 15) or rate == 3:
            continue
        return (buf[j + 3] >> 6) == 3     # channel mode 3 = single channel
    return None


def is_mono(path: str) -> bool:
    """False when unsure, which leaves mpv's normal handling in place."""
    try:
        with open(path, "rb") as f:
            start = f.read(64)
            if start[:4] == b"RIFF" and start[8:12] == b"WAVE":
                f.seek(0)
                data = f.read(4096)
                i = data.find(b"fmt ")
                return i >= 0 and int.from_bytes(data[i + 10:i + 12], "little") == 1
            if start[:4] == b"OggS":
                for tag, at in ((b"\x01vorbis", 11), (b"OpusHead", 9)):
                    i = start.find(tag)
                    if i >= 0 and i + at < len(start):
                        return start[i + at] == 1
                return False
            if start[:4] == b"fLaC" or start[4:8] == b"ftyp":
                return False
            f.seek(0)
            return bool(_mp3_mono(f))
    except (OSError, IndexError):
        return False


if __name__ == "__main__":
    import random, subprocess, sys
    media = os.path.expanduser("~/Library/Application Support/Anki2/user 1/collection.media")
    files = [x for x in os.listdir(media) if x.lower().endswith((".mp3", ".wav", ".ogg"))]
    random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
    sample = random.sample(files, 400)
    bad = 0
    for x in sample:
        p = os.path.join(media, x)
        ch = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                             "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
        if (ch == "1") != is_mono(p):
            bad += 1
            print("MISMATCH", x, ch, is_mono(p))
    print("checked", len(sample), "mismatches", bad)
