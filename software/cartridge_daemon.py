#!/usr/bin/env python3
"""
Cartridge console daemon - HUEY edition.

Boot: a random HUEY splash variant plays its intro, then its seamless loop keeps
spinning behind a blinking "INSERT CARTRIDGE". Seat an NFC-tagged cart on the
PN532 reader and the game's name appears, the ring speeds up, and the game
launches in RetroArch. Pulling the cart closes the game and drops you back on
the spinning HUEY loop, like a real console.

Controllers: a pad icon + count sits in the top-right corner. With nothing
connected (wired or Bluetooth), a small "NO CONTROLLER" shows under INSERT
CARTRIDGE. While the splash is up, the console scans for Bluetooth pads in
pairing mode and pairs, trusts and connects them on its own. Paired pads are
remembered, so after that it's just the PS / Xbox button to reconnect.

Test on a PC without the reader:  python3 cartridge_daemon.py --demo
  (keys 1-9 seat the carts in carts.json, 0 = unknown cart, SPACE = pull cart,
   C = add a fake controller (cycles 0-2), ESC = quit)
"""
import array
import glob
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pygame

# ---------------------------------------------------------------- settings --
BASE = Path(__file__).resolve().parent
CARTS_FILE = BASE / "carts.json"              # tag ID -> game mapping
SPLASH_DIR = BASE / "splash" / "huey_variants"
FONT_FILE = BASE / "splash" / "PressStart2P.ttf"
ROM_DIR = Path.home() / "roms"                # roms/<system folder>/<file>  (absolute paths in carts.json also work)
CORE_DIR = BASE / "cores"                     # filled by install_cores.sh

SCREEN = (320, 240)        # native PS1-style resolution; the GPU scales it to the TV
FPS = 30
CHIME_FRAME = 98           # intro frame where the light sweep starts (chime plays here)
LOGO_LIFT = 20             # px the logo eases upward by the end of the intro, to make room for text
LOAD_SCREEN_SECS = 2.0     # name + fast ring before the game launches
REMOVAL_GRACE = 1.5        # seconds a cart must be gone before the game closes
PRESENCE_HOLD = 0.6        # a cart counts as seated if seen within this many seconds (smooths missed reads)
POLL_TIMEOUT = 0.2         # seconds per NFC read attempt
SLOW_FRAME_MS = 200        # frames slower than this are logged (journalctl -u cartridge)
PAD_CHECK_SECS = 0.25      # how often to look for plugged-in / connected controllers
BT_SCAN_SECS = 8           # length of each Bluetooth scan burst on the splash
BT_RETRY_SECS = 30         # wait before retrying a controller that failed to pair

BG = (6, 6, 10)
WHITE = (240, 240, 240)
DIM = (150, 150, 165)
SHADOW = (0, 0, 0)
WARN = (255, 170, 70)
OK = (110, 230, 130)

# variant name colour (from the folder name) is reused for the game title text
NAME_COLORS = {
    "gem-blue": (111, 160, 255), "coral-pink": (255, 79, 121),
    "gem-rose": (255, 107, 138), "sunset-gold": (255, 210, 63),
}

# Prefer the apt-installed RetroArch; fall back to a RetroPie build if present.
RETROARCH = shutil.which("retroarch") or "/opt/retropie/emulators/retroarch/bin/retroarch"
RETROPIE_CORES = Path("/opt/retropie/libretrocores")

# system key -> (core file, rom folder)
SYSTEMS = {
    "nes":     ("fceumm_libretro.so",          "nes"),
    "snes":    ("snes9x2010_libretro.so",      "snes"),
    "genesis": ("genesis_plus_gx_libretro.so", "megadrive"),
    "gb":      ("gambatte_libretro.so",        "gb"),
    "gbc":     ("gambatte_libretro.so",        "gbc"),
    "gba":     ("mgba_libretro.so",            "gba"),
    "psx":     ("pcsx_rearmed_libretro.so",    "psx"),
}

DEMO = "--demo" in sys.argv


def find_core(name):
    """Look in our cores folder first, then any RetroPie install."""
    p = CORE_DIR / name
    if p.exists():
        return p
    hits = list(RETROPIE_CORES.glob(f"*/{name}"))
    return hits[0] if hits else None


def load_carts():
    try:
        return json.loads(CARTS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ------------------------------------------------------------------ NFC ----
class Reader(threading.Thread):
    """Polls the PN532 in the background so the screen can animate at full speed.
    Exposes .present() (uid of the seated cart or None) and .last_seen[uid]."""

    def __init__(self):
        super().__init__(daemon=True)
        self.last_uid, self.last_time = None, 0.0
        self.last_seen = {}
        self.error = None
        self.ready = False

    def run(self):
        import board, busio
        from adafruit_pn532.i2c import PN532_I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        pn = None
        for attempt in range(1, 31):   # the PN532 sometimes misses its first handshake over I2C
            try:
                pn = PN532_I2C(i2c, debug=False)
                pn.SAM_configuration()
                break
            except (RuntimeError, OSError, ValueError) as e:
                print(f"Reader not ready ({e}), retry {attempt}/30...")
                time.sleep(0.5)
        if pn is None:
            self.error = "NFC reader not found - check wiring"
            return
        self.ready = True
        while True:
            try:
                uid = pn.read_passive_target(timeout=POLL_TIMEOUT)
            except (RuntimeError, OSError):
                continue  # transient I2C hiccup
            if uid:
                self.seen(uid.hex().upper())

    def seen(self, uid):
        now = time.time()
        self.last_uid, self.last_time = uid, now
        self.last_seen[uid] = now

    def present(self):
        if self.last_uid and time.time() - self.last_time < PRESENCE_HOLD:
            return self.last_uid
        return None


class DemoReader(Reader):
    """Keyboard stand-in for the reader, for testing on a PC."""

    def __init__(self):
        super().__init__()
        self.ready = True
        self.held = None

    def start(self):
        pass

    def key(self, k):
        carts = list(load_carts().keys())
        if k == pygame.K_SPACE:
            self.held = None
        elif k == pygame.K_0:
            self.held = "DEADBEEF00"
        elif pygame.K_1 <= k <= pygame.K_9 and k - pygame.K_1 < len(carts):
            self.held = carts[k - pygame.K_1]

    def present(self):
        if self.held:
            self.seen(self.held)
        return self.held


# ---------------------------------------------------------- controllers ----
PAD_NAME = re.compile(r"wireless controller|pro controller|dualsense|dualshock|xbox|joy-?con|8bitdo|gamepad", re.I)
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|[\x01\x02]")


def connected_pads():
    """{device key: name} for every connected gamepad, wired or Bluetooth.
    Reads sysfs and the udev database, so it needs no permissions. A paired pad
    that's asleep is disconnected, so it has no input device and doesn't count.
    A DualSense shows up as 3 inputs (pad, touchpad, motion), so inputs are
    grouped by their parent device."""
    pads = {}
    for ev in glob.glob("/sys/class/input/event*") + glob.glob("/sys/class/input/js*"):
        try:
            if "/event" in ev:
                dev = Path(ev, "dev").read_text().strip()
                if "E:ID_INPUT_JOYSTICK=1" not in Path(f"/run/udev/data/c{dev}").read_text():
                    continue
            inp = os.path.realpath(os.path.join(ev, "device"))
            name = Path(inp, "name").read_text().strip()
        except OSError:
            continue
        name = re.sub(r"^Sony Interactive Entertainment |^Microsoft ", "", name)
        pads.setdefault(os.path.dirname(inp), name)
    return pads


def looks_like_pad(name, info):
    """True if a Bluetooth device (from `bluetoothctl info`) is a game controller."""
    if "Icon: input-gaming" in info or re.search(r"Appearance: 0x03c[34]", info, re.I):
        return True
    m = re.search(r"Class: 0x([0-9a-f]+)", info, re.I)
    if m:
        c = int(m.group(1), 16)
        if (c >> 8) & 0x1F == 0x05 and (c & 0x3C) in (0x04, 0x08):   # peripheral: joystick / gamepad
            return True
    return bool(PAD_NAME.search(name))


def bt_devices(out):
    """Parse `bluetoothctl devices` output into {mac: name}."""
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"Device ([0-9A-F]{2}(?::[0-9A-F]{2}){5}) ?(.*)", out)}


class Bluetooth(threading.Thread):
    """Scans in short bursts while the splash is up. When a controller in pairing
    mode shows up, it pairs, trusts and connects it. Trusted pads reconnect by
    themselves when you press the PS / Xbox button, so there's nothing to do for those."""

    def __init__(self, pads):
        super().__init__(daemon=True)
        self.pads = pads
        self.active = threading.Event()
        self.active.set()
        self.paired = {}       # mac -> name, refreshed every scan burst
        self.skip = {}         # mac -> time it was ruled out (not a pad, or pairing failed)
        self.powered = False
        self.error = None
        self.scan = None

    def ctl(self, *args, timeout=15):
        try:
            r = subprocess.run(["bluetoothctl", *args], stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=timeout)
            return ANSI.sub("", r.stdout + r.stderr)
        except (OSError, subprocess.TimeoutExpired):
            return ""

    def power_on(self):
        out = self.ctl("power", "on")
        if "succeeded" in out:
            self.ctl("pairable", "on")
            self.powered, self.error = True, None
        else:
            self.error = "BLUETOOTH UNAVAILABLE"
            print(f"Bluetooth: power on failed: {out.strip()}", flush=True)

    def run(self):
        while True:
            self.active.wait()
            if not self.powered:
                self.power_on()        # retried until it works: the adapter can come up late
                if not self.powered:
                    time.sleep(10)
                    continue
            self.paired = bt_devices(self.ctl("devices", "Paired"))
            self.start_scan()
            end = time.time() + BT_SCAN_SECS
            while time.time() < end and self.active.is_set():
                time.sleep(1)
                found = self.find_pad()
                if found:
                    self.stop_scan()   # pairing is more reliable with discovery off
                    self.pair(*found)
                    break
            self.stop_scan()

    def start_scan(self):
        self.scan = subprocess.Popen(["bluetoothctl", "--timeout", str(BT_SCAN_SECS + 2), "scan", "on"],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop_scan(self):
        p = self.scan
        if p and p.poll() is None:
            p.terminate()              # bluez ends the discovery when its owner exits
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

    def find_pad(self):
        """A nearby, unpaired controller that's advertising right now, as (mac, name)."""
        now = time.time()
        for mac, name in bt_devices(self.ctl("devices")).items():
            if now - self.skip.get(mac, -BT_RETRY_SECS) < BT_RETRY_SECS:
                continue
            info = self.ctl("info", mac)
            if "RSSI:" not in info:
                continue               # stale entry, not in range right now
            if "Paired: no" in info and looks_like_pad(name, info):
                return mac, name
            if "Paired: yes" in info or not re.fullmatch(r"[0-9A-F]{2}(-[0-9A-F]{2}){5}", name):
                self.skip[mac] = now   # paired already, or named and not a pad: don't ask again for a while
        return None

    def pair(self, mac, name):
        print(f"Bluetooth: pairing {name} ({mac})", flush=True)
        self.pads.say(f"Pairing: {name}", DIM, secs=30)
        out = self.ctl("pair", mac, timeout=30)
        if "Pairing successful" in out or "AlreadyExists" in out:
            self.ctl("trust", mac)
            self.ctl("connect", mac, timeout=20)
            self.paired[mac] = name
            self.pads.say(f"Paired: {name}", OK, check=True)
            print(f"Bluetooth: paired {name}", flush=True)
        else:
            self.skip[mac] = time.time()
            self.ctl("remove", mac)    # clear any half-finished pairing so the next try starts clean
            self.pads.say(f"Pairing failed: {name}", WARN)
            print(f"Bluetooth: pairing {name} failed: {out.strip()[-200:]}", flush=True)

    def pause(self):
        self.active.clear()
        p = self.scan
        if p and p.poll() is None:
            p.terminate()              # no wait here: this runs on the main thread; run() reaps it

    def resume(self):
        self.active.set()


class Controllers:
    """Tracks connected controllers and the short status messages about them."""

    def __init__(self):
        self.pads = {}
        self.next_check = 0.0
        self.message = None    # (text, color, check mark, expiry time)
        self.fake = 0          # --demo: pretend controllers (C key)
        linux = sys.platform.startswith("linux")
        self.bt = Bluetooth(self) if linux and not DEMO and shutil.which("bluetoothctl") else None
        if not linux:
            pygame.joystick.init()

    def start(self):
        if self.bt:
            self.bt.start()

    def pause(self):
        if self.bt:
            self.bt.pause()

    def resume(self):
        if self.bt:
            self.bt.resume()

    def say(self, text, color=OK, check=False, secs=4):
        self.message = (text, color, check, time.time() + secs)

    def current_message(self):
        m = self.message
        return m if m and time.time() < m[3] else None

    def key(self, k):
        if k == pygame.K_c:
            self.fake = (self.fake + 1) % 3
            if self.fake:
                self.say("Paired: DualSense Wireless Controller", OK, check=True)

    def update(self):
        now = time.time()
        if now < self.next_check:
            return
        self.next_check = now + PAD_CHECK_SECS
        if sys.platform.startswith("linux"):
            found = connected_pads()
        else:
            found = {i: pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())}
        found.update({f"fake{i}": "DualSense Wireless Controller" for i in range(self.fake)})
        new = [found[k] for k in found.keys() - self.pads.keys()]
        if new and not self.current_message():   # don't talk over "Paired: ..."
            self.say(f"Connected: {new[0]}", OK, check=True, secs=3)
        self.pads = found

    def count(self):
        return len(self.pads)

    def hint(self):
        if self.bt and self.bt.error:
            return self.bt.error
        if self.bt and self.bt.paired:
            return "PRESS THE PS / XBOX BUTTON"
        return "PLUG IN OR PAIR A CONTROLLER"


# ---------------------------------------------------------------- sound ----
def tone_buffer(notes, length, rate=22050, decay=3.2, vol=0.35):
    buf = array.array("h")
    for i in range(int(rate * length)):
        t = i / rate
        v = 0.0
        for start, f in notes:
            if t >= start:
                dt = t - start
                v += math.exp(-dt * decay) * (math.sin(2 * math.pi * f * dt) + 0.3 * math.sin(4 * math.pi * f * dt))
        s = int(max(-1, min(1, v * vol)) * 32767)
        buf.extend((s, s))
    return pygame.mixer.Sound(buffer=buf.tobytes())


# ------------------------------------------------------------- splash art ----
class Frames:
    """Loads frames the first time they're shown, then keeps them."""

    def __init__(self, folder):
        self.paths = sorted(glob.glob(str(folder / "*.png")))
        self.cache = {}

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        if i not in self.cache:
            img = pygame.image.load(self.paths[i]).convert_alpha()
            if img.get_size() != SCREEN:
                img = pygame.transform.scale(img, SCREEN)
            self.cache[i] = img
        return self.cache[i]


def pick_variant():
    variants = sorted(d for d in glob.glob(str(SPLASH_DIR / "*")) if os.path.isdir(os.path.join(d, "loop")))
    if not variants:
        return None
    last_file = SPLASH_DIR / ".last_variant"
    last = last_file.read_text().strip() if last_file.exists() else ""
    choice = random.choice([v for v in variants if os.path.basename(v) != last] or variants)
    try:
        last_file.write_text(os.path.basename(choice))
    except OSError:
        pass
    return Path(choice)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# Pad icon for the top-right corner, 1 px per character.
PAD_ICON = (
    ".XXXXXXXXXXX.",
    "XXXXXXXXXXXXX",
    "XX.XXXXXXX.XX",
    "X...XXXXX.X.X",
    "XX.XXXXXXX.XX",
    "XXXXXXXXXXXXX",
    "XXXX.....XXXX",
    ".XX.......XX.",
)

# 3x5 pixel font for the small controller hint (Press Start 2P only stays crisp at 8 px and up).
TINY = {line[0]: line[2:].replace(" ", "") for line in """\
A .#. #.# ### #.# #.#
B ##. #.# ##. #.# ##.
C .## #.. #.. #.. .##
D ##. #.# #.# #.# ##.
E ### #.. ##. #.. ###
F ### #.. ##. #.. #..
G .## #.. #.# #.# .##
H #.# #.# ### #.# #.#
I ### .#. .#. .#. ###
J ..# ..# ..# #.# .#.
K #.# #.# ##. #.# #.#
L #.. #.. #.. #.. ###
M #.# ### ### #.# #.#
N ##. #.# #.# #.# #.#
O .#. #.# #.# #.# .#.
P ##. #.# ##. #.. #..
Q .#. #.# #.# ##. .##
R ##. #.# ##. #.# #.#
S .## #.. .#. ..# ##.
T ### .#. .#. .#. .#.
U #.# #.# #.# #.# ###
V #.# #.# #.# #.# .#.
W #.# #.# ### ### #.#
X #.# #.# .#. #.# #.#
Y #.# #.# .#. .#. .#.
Z ### ..# .#. #.. ###
0 ### #.# #.# #.# ###
1 .#. ##. .#. .#. ###
2 ##. ..# .#. #.. ###
3 ##. ..# .#. ..# ##.
4 #.# #.# ### ..# ..#
5 ### #.. ##. ..# ##.
6 .## #.. ### #.# ###
7 ### ..# .#. .#. .#.
8 ### #.# ### #.# ###
9 ### #.# ### ..# ##.
/ ..# ..# .#. #.. #..
+ ... .#. ### .#. ...
- ... ... ### ... ...
. ... ... ... ... .#.
: ... .#. ... .#. ...
! .#. .#. .#. ... .#.""".splitlines()}


def check_mark(surf, x, y, color):
    """A small check mark that matches the 8 px font."""
    for dx, dy in ((1, 1), (0, 0)):
        pygame.draw.lines(surf, SHADOW if dx else color, False,
                          [(x + dx, y + 4 + dy), (x + 2 + dx, y + 6 + dy), (x + 7 + dx, y + 1 + dy)], 2)


# --------------------------------------------------------------- screen ----
class Screen:
    def __init__(self):
        variant = pick_variant()
        self.variant_name = variant.name if variant else ""
        print(f"Splash variant: {self.variant_name}" if variant else f"No splash variants found in {SPLASH_DIR}", flush=True)
        self.missing_art = variant is None
        self.accent = next((c for k, c in NAME_COLORS.items() if self.variant_name.endswith(k)), WHITE)
        self.open()
        self.intro = Frames(variant / "intro") if variant else []
        self.loop = Frames(variant / "loop") if variant else []
        self.loop_i = 0.0
        self.tick = 0
        self.pads = None              # Controllers, set by main()

    def open(self):
        os.environ.setdefault("SDL_HINT_RENDER_SCALE_QUALITY", "0")   # nearest = crisp pixels
        pygame.display.init()
        pygame.font.init()
        try:
            self.surf = pygame.display.set_mode(SCREEN, pygame.FULLSCREEN | pygame.SCALED, vsync=1)
        except pygame.error:
            self.surf = pygame.display.set_mode(SCREEN, pygame.SCALED)
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("HUEY")
        f = str(FONT_FILE) if FONT_FILE.exists() else None
        self.font8 = pygame.font.Font(f, 8 if f else 12)
        self.font16 = pygame.font.Font(f, 16 if f else 22)
        self.clock = pygame.time.Clock()
        for fr in (getattr(self, "intro", None), getattr(self, "loop", None)):
            if fr:
                fr.cache.clear()        # surfaces belong to the old display; reload lazily
        self.chime = self.blip = None
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2)
            self.chime = tone_buffer([(0.00, 987.8), (0.14, 1318.5)], 1.6)              # B5 -> E6
            self.blip = tone_buffer([(0.0, 659.3), (0.07, 987.8), (0.14, 1318.5)], 0.9, decay=5)
        except pygame.error:
            pass  # no audio device: everything still works silently

    def close(self):
        try:
            pygame.mixer.quit()     # free the audio device for RetroArch
        except pygame.error:
            pass
        pygame.display.quit()       # free the display for RetroArch

    def events(self, reader):
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and DEMO):
                raise SystemExit
            if e.type == pygame.KEYDOWN and isinstance(reader, DemoReader):
                reader.key(e.key)
                if self.pads:
                    self.pads.key(e.key)

    # -- drawing helpers --
    def text(self, msg, y, font=None, color=WHITE, alpha=255):
        font = font or self.font8
        for line_i, line in enumerate(self.wrap(msg, font)):
            yy = y + line_i * (font.get_height() + 3)
            sh = font.render(line, False, SHADOW)
            tx = font.render(line, False, color)
            if alpha < 255:
                sh.set_alpha(alpha); tx.set_alpha(alpha)
            x = (SCREEN[0] - tx.get_width()) // 2
            self.surf.blit(sh, (x + 1, yy + 1))
            self.surf.blit(tx, (x, yy))

    def wrap(self, msg, font, width=SCREEN[0] - 16):
        words, lines, cur = msg.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= width or not cur:
                cur = test
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        return lines[:3]

    def tiny(self, msg, y, color):
        """Centred text in the 3x5 pixel font, with a drop shadow."""
        msg = msg.upper()
        x0 = (SCREEN[0] - (len(msg) * 4 - 1)) // 2
        for off, col in ((1, SHADOW), (0, color)):
            for i, ch in enumerate(msg):
                for p, bit in enumerate(TINY.get(ch, "")):
                    if bit == "#":
                        self.surf.set_at((x0 + i * 4 + p % 3 + off, y + p // 3 + off), col)

    def note(self, msg, y, color, check):
        """Status line in the 8 px font, optionally ending in a check mark."""
        lines = self.wrap(msg, self.font8, SCREEN[0] - 28)
        for i, line in enumerate(lines):
            last = check and i == len(lines) - 1
            yy = y + i * (self.font8.get_height() + 3)
            w = self.font8.size(line)[0]
            x = (SCREEN[0] - w - (12 if last else 0)) // 2
            self.surf.blit(self.font8.render(line, False, SHADOW), (x + 1, yy + 1))
            self.surf.blit(self.font8.render(line, False, color), (x, yy))
            if last:
                check_mark(self.surf, x + w + 4, yy, color)

    def pad_icon(self, n):
        """Controller icon + count in the top-right corner."""
        color = WHITE if n else DIM
        label = self.font8.render(str(n), False, color)
        lx = SCREEN[0] - 6 - label.get_width()
        ix, iy = lx - 4 - len(PAD_ICON[0]), 6
        for off, col in ((1, SHADOW), (0, color)):
            for dy, row in enumerate(PAD_ICON):
                for dx, c in enumerate(row):
                    if c == "X":
                        self.surf.set_at((ix + dx + off, iy + dy + off), col)
        self.surf.blit(self.font8.render(str(n), False, SHADOW), (lx + 1, iy + 1))
        self.surf.blit(label, (lx, iy))

    def art(self, frame, lift):
        self.surf.fill(BG)
        if frame is not None:
            self.surf.blit(frame, (0, -int(lift)))

    def loop_frame(self, speed=1.0):
        if not self.loop:
            return None
        self.loop_i = (self.loop_i + speed) % len(self.loop)
        return self.loop[int(self.loop_i)]

    def present(self, flash=0, fade=0):
        if flash:
            w = pygame.Surface(SCREEN); w.fill((255, 255, 255)); w.set_alpha(int(flash))
            self.surf.blit(w, (0, 0))
        if fade:
            b = pygame.Surface(SCREEN); b.fill((0, 0, 0)); b.set_alpha(int(fade))
            self.surf.blit(b, (0, 0))
        pygame.display.flip()
        ms = self.clock.tick(FPS)
        if ms > SLOW_FRAME_MS and self.tick:
            print(f"Slow frame: {ms} ms", flush=True)
        self.tick += 1

    def blink(self, period=30, on=20):
        return (self.tick % period) < on

    # -- scenes --
    def play_intro(self, reader):
        n = len(self.intro)
        for i in range(n):
            self.events(reader)
            if i == CHIME_FRAME and self.chime:
                self.chime.play()
            self.art(self.intro[i], LOGO_LIFT * smooth(i / max(1, n - 1)))
            if i > n - 15:   # INSERT CARTRIDGE fades in over the last half second
                self.text("INSERT CARTRIDGE", 196, alpha=int(255 * (i - (n - 15)) / 15))
            self.present()

    def idle(self, reader, message="INSERT CARTRIDGE", sub="", color=WHITE, blink=True, fade_in=0, pad_status=False):
        self.events(reader)
        self.art(self.loop_frame(), LOGO_LIFT)
        if not blink or self.blink():
            self.text(message, 196, color=color)
        if sub:
            self.text(sub, 214, color=DIM)
        if self.pads:
            self.pads.update()
            self.pad_icon(self.pads.count())
            note = self.pads.current_message()
            if note and not sub:
                self.note(note[0], 212, note[1], note[2])
            elif pad_status and not self.pads.count():
                self.tiny("NO CONTROLLER", 211, WARN)     # small, so a cart can still be seated
                self.tiny(self.pads.hint(), 220, DIM)
        if reader.error:
            self.text(reader.error, 8, color=WARN)
        if self.missing_art:
            self.text("SPLASH FILES MISSING: ~/cartridge/splash/huey_variants", 40, color=WARN)
        self.present(fade=fade_in)

    def loading(self, reader, title, uid, lookup):
        """Name types in, ring speeds up, then fades out. Holds at full speed until
        `lookup` (a Lookup) finishes. Returns True to launch, False if the cart was
        pulled, or the error string from resolve()."""
        if self.blip:
            self.blip.play()
        total = int(LOAD_SCREEN_SECS * FPS)
        fade_at = total - 10
        title = title.upper()
        big = self.font16 if self.font16.size(title)[0] <= SCREEN[0] - 16 else self.font8
        i = 0
        while i < total:
            self.events(reader)
            if reader.present() != uid and time.time() - reader.last_seen.get(uid, 0) > 0.8:
                return False
            if i >= fade_at and lookup.is_alive():
                i = fade_at - 1                                         # NAS still answering: keep spinning
            if i == fade_at and isinstance(lookup.result, str):
                return lookup.result
            speed = 1 + 3 * smooth(i / (total * 0.5))                 # ring winds up
            self.art(self.loop_frame(speed), LOGO_LIFT)
            shown = title[: max(1, int(i * 1.5))]                       # typewriter reveal
            self.text(shown, 192, font=big, color=self.accent)
            if self.blink(16, 10):
                self.text("NOW LOADING", 220 if big is self.font16 else 214, color=DIM)
            flash = 200 * max(0, 1 - i / 8)
            fade = 255 * smooth((i - fade_at) / 10)
            self.present(flash=flash, fade=fade)
            i += 1
        return True


# ----------------------------------------------------------------- game ----
def resolve(cart):
    """Return (core, rom) paths, or an error string."""
    system = cart.get("system")
    if system not in SYSTEMS:
        return f"Unknown system '{system}'"
    core_name, folder = SYSTEMS[system]
    core = find_core(core_name)
    rom = ROM_DIR / folder / cart.get("rom", "")      # an absolute "rom" path overrides ROM_DIR
    if not core:
        return f"Core missing: {core_name}"
    if not rom.is_file():
        return f"ROM missing: {rom.name}"
    return core, rom


class Lookup(threading.Thread):
    """Runs resolve() off the main thread. The ROM check reads the NAS, which can
    take seconds while its drives spin up, and the splash has to keep spinning."""

    def __init__(self, cart):
        super().__init__(daemon=True)
        self.cart, self.result = cart, None
        self.start()

    def run(self):
        self.result = resolve(self.cart)


def run_game(reader, screen, uid, core, rom):
    screen.close()
    if DEMO:
        print(f"[demo] would launch: {RETROARCH} -L {core} {rom}")
        time.sleep(2)
        screen.open()
        return
    cmd = [RETROARCH, "--fullscreen", "-L", str(core), str(rom)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while proc.poll() is None:
        if time.time() - reader.last_seen.get(uid, 0) > REMOVAL_GRACE:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        time.sleep(0.1)
    screen.open()


def main():
    screen = Screen()
    reader = DemoReader() if DEMO else Reader()
    reader.start()                    # reader warms up in the background while the intro plays
    pads = screen.pads = Controllers()
    pads.start()                      # Bluetooth scanning runs while the splash is up
    screen.play_intro(reader)
    fade_in = 0
    while True:
        uid = reader.present()
        if not uid:
            screen.idle(reader, fade_in=fade_in, pad_status=True)
            fade_in = max(0, fade_in - 17)
            continue

        cart = load_carts().get(uid)  # re-read every time: new carts work without a restart
        if not cart:
            screen.idle(reader, "UNKNOWN CARTRIDGE", f"TAG {uid}", color=WARN, blink=False)
            continue

        lookup = Lookup(cart)         # ROM check runs in the background while the load screen plays
        pads.pause()                  # no Bluetooth scanning while a game runs (it adds input lag)
        try:
            outcome = screen.loading(reader, cart.get("name", "LOADING"), uid, lookup)
            if outcome is True:
                run_game(reader, screen, uid, *lookup.result)
        finally:
            pads.resume()
        if outcome is False:
            continue                  # cart pulled during the load screen
        if isinstance(outcome, str):
            while reader.present() == uid:   # shown until the cart is pulled; no NAS check per frame
                screen.idle(reader, "CARTRIDGE ERROR", outcome, color=WARN, blink=False)
            continue
        fade_in = 255                 # fade back in on the spinning loop

        # Game was quit from RetroArch's menu with the cart still seated:
        # wait for the cart to be pulled before it can boot again.
        while reader.present() == uid:
            screen.idle(reader, "RESEAT CARTRIDGE", "TO PLAY AGAIN", fade_in=fade_in)
            fade_in = max(0, fade_in - 17)


if __name__ == "__main__":
    try:
        main()
    finally:
        pygame.quit()
