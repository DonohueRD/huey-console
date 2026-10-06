#!/usr/bin/env python3
"""
Register cartridges: tap a tag, pick a system, search for a game, done.
Writes the entry to carts.json for the console to use.

Run:  venv/bin/python add_cart.py
(Stop the console service first if it's running: sudo systemctl stop cartridge)
"""
import json
import re
import time
from pathlib import Path

import board
import busio
from adafruit_pn532.i2c import PN532_I2C

BASE = Path(__file__).resolve().parent
CARTS_FILE = BASE / "carts.json"
HOME = Path.home()

# Where the network share's extracted folders appear on the Pi.
# Check with:  ls "/mnt/games"   and adjust if your path differs.
SHARE = Path("/mnt/games/Games/MEGA FOLDER OF ROMS/Extracted folders")

# system key -> folders to search (share folders + local ~/roms fallback)
LIBRARY = {
    "nes":     [SHARE / "Nintendo - NES",  HOME / "roms/nes"],
    "snes":    [SHARE / "Nintendo - SNES", HOME / "roms/snes"],
    "genesis": [SHARE / "Sega - Genesis", HOME / "roms/megadrive"],
    "gb":      [SHARE / "Nintendo - Game Boy", HOME / "roms/gb"],
    "gbc":     [SHARE / "Nintendo - Game Boy Color", HOME / "roms/gbc"],
    "gba":     [SHARE / "Nintendo - Game Boy Advance", HOME / "roms/gba"],
    "psx":     [SHARE / "Sony - PlayStation", HOME / "roms/psx"],
}
ROM_EXT = {".zip", ".7z", ".nes", ".sfc", ".smc", ".md", ".gen", ".bin", ".smd",
           ".gb", ".gbc", ".gba", ".chd", ".cue", ".pbp"}


def init_reader(tries=10):
    """The PN532 sometimes misses its first handshake over I2C; retry."""
    i2c = busio.I2C(board.SCL, board.SDA)
    for attempt in range(1, tries + 1):
        try:
            pn = PN532_I2C(i2c, debug=False)
            pn.SAM_configuration()
            return pn
        except (RuntimeError, OSError, ValueError) as e:
            print(f"Reader not ready ({e}), retry {attempt}/{tries}...")
            time.sleep(0.5)
    raise SystemExit("Could not talk to the NFC reader. Check wiring, then try again.")


def wait_for_tag(pn):
    print("\nTap a tag on the reader...")
    while True:
        try:
            uid = pn.read_passive_target(timeout=0.5)
        except (RuntimeError, OSError):
            uid = None
        if uid:
            return uid.hex().upper()


def wait_for_removal(pn, uid):
    print("Remove the tag.")
    gone_since = None
    while True:
        try:
            now = pn.read_passive_target(timeout=0.3)
        except (RuntimeError, OSError):
            now = None
        if now and now.hex().upper() == uid:
            gone_since = None
        else:
            gone_since = gone_since or time.time()
            if time.time() - gone_since > 1.0:
                return


def pick(prompt, options):
    for i, opt in enumerate(options, 1):
        print(f"  {i:>2}. {opt}")
    while True:
        ans = input(f"{prompt} (number, or blank to cancel): ").strip()
        if not ans:
            return None
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return options[int(ans) - 1]
        print("  Not a valid choice.")


DISC_EXT = {".cue", ".chd", ".m3u", ".pbp"}   # what to launch for disc games


def find_games(system, term):
    words = term.lower().split()
    hits = []
    disc = system == "psx"
    for folder in LIBRARY[system]:
        if not folder.is_dir():
            continue
        files = folder.rglob("*") if disc else folder.iterdir()   # disc games often sit in per-game folders
        for f in files:
            ok_ext = DISC_EXT if disc else ROM_EXT
            if f.is_file() and f.suffix.lower() in ok_ext:
                if all(w in f.name.lower() for w in words):
                    hits.append(f)
    return sorted(hits, key=lambda p: p.name.lower())


def clean_name(path):
    name = re.sub(r"\s*[\(\[].*?[\)\]]", "", path.stem)  # drop (USA), [!], etc.
    return name.strip() or path.stem


def main():
    for system, folders in LIBRARY.items():
        if not any(f.is_dir() for f in folders):
            print(f"note: no folders found for {system}")
    pn = init_reader()

    while True:
        carts = json.loads(CARTS_FILE.read_text()) if CARTS_FILE.exists() else {}
        uid = wait_for_tag(pn)
        if uid in carts:
            print(f"Tag {uid} is already '{carts[uid]['name']}'.")
            if input("Overwrite it? (y/N): ").strip().lower() != "y":
                wait_for_removal(pn, uid)
                continue
        else:
            print(f"New tag: {uid}")

        system = pick("System", list(LIBRARY))
        if not system:
            wait_for_removal(pn, uid)
            continue

        game = None
        while not game:
            term = input("Search for a game (part of the name): ").strip()
            if not term:
                break
            hits = find_games(system, term)
            if not hits:
                print("  No matches, try fewer or different words.")
                continue
            if len(hits) > 25:
                print(f"  {len(hits)} matches, showing the first 25. Be more specific to narrow it.")
            choice = pick("Game", [h.name for h in hits[:25]])
            if choice:
                game = next(h for h in hits if h.name == choice)
        if not game:
            wait_for_removal(pn, uid)
            continue

        name = clean_name(game)
        typed = input(f"Name shown on screen [{name}]: ").strip()
        carts[uid] = {"name": typed or name, "system": system, "rom": str(game)}
        CARTS_FILE.write_text(json.dumps(carts, indent=2))
        print(f"Saved: {uid} -> {carts[uid]['name']}")
        wait_for_removal(pn, uid)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye.")
