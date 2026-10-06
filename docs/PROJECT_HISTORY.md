# HUEY Console ("Huey's Station") — Project Context

> Compiled from Claude Desktop chats on 2026-10-03. Items marked (unverified) were checked on
> the Pi on 2026-10-04; see "Verified state" in CLAUDE.md for the results, which take priority.
> Since then: `huey_splash_ps1.py` on the NAS was edited to `RING_Y = -0.3` and the lowered
> classic camera; files were consolidated from Downloads into `Y:\PRojects\HueyConsole`.

## 1. Project summary
- A Raspberry Pi 3 retro console with 3D-printed cartridges. Each cart holds an NTAG215 NFC sticker, and a PN532 reader under the top-loading slot reads its UID.
- `~/cartridge/cartridge_daemon.py` runs as the systemd service `cartridge`:
  - At boot it plays a random PS1-style low-poly "HUEY" splash intro.
  - It then loops the spinning ring behind a blinking INSERT CARTRIDGE.
  - When a cart is seated, it looks up the UID in `carts.json`, shows the game name with NOW LOADING, and launches RetroArch with the matching libretro core.
  - When the cart is pulled (1.5 s grace), it closes RetroArch and returns to the loop.
- ROMs are read from a NAS share mounted read-only. Carts are registered with `add_cart.py`: tap a tag, pick a system, search the game.
- "Huey's Station" is a placeholder name. Ryan wants a better one.

## 2. Current status (as of 2026-10-03 ~23:45 ET)
- **Working end to end on the bench:** the reader reads tags, `add_cart.py` registers carts, tag in launches the game, tag out returns to the splash. Ryan: "it works well!"
- **HUEY splash merged into the daemon and running on the Pi.** Ryan: "this looks amazing."
  - A re-rendered pack with the ring lowered (`RING_Y = -0.3`) was delivered as `huey_splash_pi.zip`.
  - Deployment of that lowered-ring pack: (unverified)
- **Service:** `cartridge.service` installed in `/etc/systemd/system/` and enabled. Boots straight to the console. `getty@tty1` was told to be disabled. (unverified that every boot-cleanup step was run)
- **Pi:** hostname `pi`, user `pi`, reachable at `pi.local` over Wi-Fi.
  - Boot behaviour was switched to console with `raspi-config nonint do_boot_behaviour B1`, because the desktop GUI was taking the HDMI output.
- **NAS share** mounted at `/mnt/games` and working (logs in as `Hueyserver`).
- **RetroArch** installed from apt. 6 prebuilt cores are in `~/cartridge/cores`.
- **Registered carts:** at least one. Test data showed `044105532F0289` → "Sonic The Hedgehog 2" (genesis). (unverified exact contents)
  - The two template entries `04A1B2C3D4E580` and `04F0E1D2C3B480` are probably still in `carts.json`.
- **Printed:** the slot sleeve and one cart of the OLD v2 design (Genesis-wedge model, 76×60×10 carts). Ryan: "test prints work fine."
  - He was then printing the v2 "top circle" (`slot_disc`), which is not used by the current walnut design.
- **Not printed yet:** none of the capsule ("huey_station v1"), walnut edition, or cart v3 parts.
- **Button:**
  - Ryan's existing 16 mm APIELE metal button is latching (stays down), so it can't be used.
  - A momentary 16 mm button with no LED was ordered, arriving 2026-10-04 (Amazon B08SKJ6V7Z).
  - The momentary button is not wired yet.
  - The code currently running on the Pi has NO button support (see section 8).
- **Panel-mount extension cables ordered:** USB-A ×2, HDMI, micro-USB, RJ45. Not measured yet.
- **PS1:** games are extracted as bin/cue on the NAS but not yet moved to `Sony - PlayStation`. BIOS not confirmed copied. No PS1 carts registered. (unverified)
- **Bluetooth:** `dtoverlay=disable-bt` was added during UART troubleshooting. The removal command was given, but whether it was run is (unverified). No controllers paired yet.

## 3. Hardware
- **Pi:** Raspberry Pi 3 (exact model B/B+ unverified). The recommended PSU is 5 V 2.5 A micro-USB.
  - The PC is Windows (user `huey2`). Files are delivered to `C:\Users\huey2\Downloads`.
- **NFC reader:** Elechouse PN532 NFC Module V3 (red board), about 42.7 × 40.4 mm.
  - Mode switches: I2C = SW1 ON, SW2 OFF. HSU/UART = both OFF. SPI = SW1 OFF, SW2 ON. Switches only take effect after a full power cut (unplug ~10 s).
  - Use the 4-pin END header (GND, VCC, SDA/TXD, SCL/RXD). Do NOT use the 8-pin side row, which is SPI only.
  - Wiring (I2C, current):

    | PN532 | Pi 3 pin |
    |---|---|
    | VCC | pin 1 (3.3 V; do not use 5 V) |
    | GND | pin 6 |
    | SDA/TXD | pin 3 (GPIO2) |
    | SCL/RXD | pin 5 (GPIO3) |

  - I2C address `0x24`. The PN532 sometimes doesn't answer `i2cdetect` until it's woken, so use the test script instead.
  - Mount the antenna side facing the cart wall. The board slides into rails on the sleeve, stopped by the flange, with a hot-glue dab.
- **Tags:** NTAG215 25 mm round stickers. UIDs are 7-byte uppercase hex, e.g. `044105532F0289`.
- **Magnets:** 5 × 2 mm discs, 4 per cart half (current carts). The original v1 design used 6 × 3 mm. Check polarity before gluing.
- **Power/reset button (planned wiring):** momentary 16 mm, no LED.
  - Level 1 (planned): one terminal (C) → pin 9 (GND), other terminal (NO) → pin 11 (GPIO17). With a 3-tab button, leave NC unused.
  - Planned code behaviour: tap during a game = restart the game; hold 3 s = safe shutdown (`sudo poweroff`); tap on the splash screen = ignored.
  - Optional level 2 (power-on from halt, not done): two Schottky diodes (1N5817 or BAT43) from the button's NO tab, stripes toward the button. Diode A → pin 11. Diode B → pin 5 (GPIO3, Y-spliced with the reader's SCL wire).
    - This works because wake-from-halt only works on GPIO3, which the reader's SCL already uses, hence the diodes.
    - A latching button must never go on GPIO3: it would hold SCL low and kill the reader.
- **LED strip (only for the capsule design's glowing clear bezel, not the walnut):** WS2812B 5 V, 60/m, about 14–15 LEDs.
  - Planned wiring: 5V → pin 2, GND → pin 14, DIN → pin 19 (GPIO10).
  - Not purchased or wired. (unverified) No code written.
- **Controllers:**
  - Ryan has several Bluetooth controllers (models not stated). Plan: try Bluetooth first.
  - Fallback: 2.4 GHz dongle controllers (8BitDo Ultimate 2C, SN30 Pro 2.4G, M30 2.4G) or wired Xbox.
  - The Pi 3 has 4 USB ports, and the reader uses none.
  - On the Pi 3, Bluetooth shares the Wi-Fi radio, which may stutter during NAS loads or Moonlight streaming.
- **Display/audio:** a TV over HDMI. Audio over HDMI (chime and load blip are generated in code).
- **Printer:** Bambu P1S (256 mm bed), with AMS (unverified).
  - Defaults: 0.2 mm layers, 3 walls, 15% gyroid, stock 0.4 mm nozzle.
  - PETG recommended for the sleeve, lever and carts (flexing detent tongues and leaf spring). Ironing on top plateaus.
  - The cart strip can go at 0.12 mm layers.
- **Filament on hand:**
  - ELEGOO wood-COLORED regular PLA. NOT wood-fill: no special nozzle, no sanding or staining.
  - Marble PLA, matte green, clear.
  - Earlier PS1-gray idea (warm light gray). (unverified purchase)
- **Hardware for walnut build:**
  - 4× M3×12 self-tapping (base → top, clamping body + marble ring)
  - 2× M3×8 (faceplate ears → top)
  - 4× M3×8 (sleeve → faceplate)
  - 4× M2.5 self-tapping (Pi → standoffs)
  - 4× 10 mm rubber feet, hot glue, CA glue (for the cart strip)
- **Still to buy:** Schottky diodes 1N5817/BAT43 (only for power-on), heat-shrink and/or 2.8 mm female spade connectors for the button wires. Optionally a WS2812B strip.
- **Pi 3 capability:**
  - Full speed: NES, SNES, Genesis/MS/GG, GB/GBC/GBA, most PS1.
  - N64 is hit or miss (Mario Kart 64 / Smash playable, GoldenEye not).
  - Saturn, Dreamcast, PSP, GameCube and PS2 are out of reach. A future Pi 5 or N100 mini-PC upgrade would carry over the same reader and software.

## 4. Pi software setup
- **OS:** Raspberry Pi OS. The guide said Lite 64-bit, but the Pi actually had the desktop installed (HDMI showed the GUI), now set to console boot (B1).
  - The venv Python is 3.13, which suggests a Trixie-based release. (unverified)
  - Set in Raspberry Pi Imager: user `pi`, hostname `pi`, Wi-Fi (2.4 GHz only on the Pi 3), SSH enabled.
- **Access from the PC (PowerShell):** `ssh pi@pi.local`.
  - `ping pi.local` returns an IPv6 address (normal). Use `ping -4 pi.local` for IPv4.
  - File transfer: `scp <file> pi@pi.local:~/cartridge/`. WinSCP was also suggested.
- **I2C:** `sudo raspi-config nonint do_i2c 0` (adds `dtparam=i2c_arm=on`).
- **apt packages installed or instructed:**
  - Installed: `i2c-tools python3-pygame python3-venv git retroarch unzip wget cifs-utils`
  - Possibly installed: `tmux`
  - Instructed but (unverified): `python3-gpiozero` for the button, `bluez pi-bluetooth` only if Bluetooth is wanted
- **venv:** `~/cartridge/venv`, created with `python3 -m venv --system-site-packages venv`, so it sees apt's pygame and gpiozero.
  - `venv/bin/pip install adafruit-blinka adafruit-circuitpython-pn532`
  - pyserial comes from the system.
  - Always run reader scripts with `venv/bin/python`, never plain `python3`.
- **RetroArch:** from apt (`shutil.which("retroarch")`). Fallback path in code: `/opt/retropie/emulators/retroarch/bin/retroarch`.
  - Launch command: `retroarch --fullscreen -L <core> <rom>`, with stdout/stderr sent to DEVNULL.
- **Cores:** `~/cartridge/cores/`, downloaded by `install_cores.sh` from `https://buildbot.libretro.com/nightly/linux/$ARCH/latest/<core>_libretro.so.zip`.
  - `$ARCH` is aarch64, or armhf for armv7l.
  - The code also searches `/opt/retropie/libretrocores/*/` as a fallback.
  - The RetroPie-Setup compile was abandoned. `~/RetroPie-Setup` can be deleted, and some partial `/opt/retropie` installs may exist (unverified).
- **System mapping in the daemon:**

  | system key | core file | ROM folder |
  |---|---|---|
  | nes | fceumm_libretro.so | nes |
  | snes | snes9x2010_libretro.so | snes |
  | genesis | genesis_plus_gx_libretro.so | megadrive |
  | gb | gambatte_libretro.so | gb |
  | gbc | gambatte_libretro.so | gbc |
  | gba | mgba_libretro.so | gba |
  | psx | pcsx_rearmed_libretro.so | psx |

- **Local ROM and BIOS folders:**
  - `ROM_DIR = ~/roms`, with subfolders `nes snes megadrive gb gbc gba psx` (created by `install_cores.sh`).
  - An absolute `"rom"` path in `carts.json` overrides `ROM_DIR` (pathlib join). `add_cart.py` always writes absolute paths.
  - PS1 BIOS goes in `~/.config/retroarch/system/` with a lowercase filename, e.g. `scph5501.bin` (US).
    - To find it: `find /mnt/games/Games -iname "scph*"`
    - Copy status: (unverified)
- **Saves** (the share is read-only, so saves go local; applied status unverified):
```
  mkdir -p ~/saves ~/states ~/.config/retroarch
  printf 'savefile_directory = "~/saves"\nsavestate_directory = "~/states"\n' >> ~/.config/retroarch/retroarch.cfg
```
- **NAS share (192.168.1.12):**
  - Credentials in `~/.smbcred` (chmod 600), with lines `username=...` and `password=...`. The user is `Hueyserver`.
  - Mount point: `sudo mkdir -p /mnt/games`.
  - `/etc/fstab` line:
```
    //192.168.1.12/HueyRaid1 /mnt/games cifs credentials=/home/pi/.smbcred,uid=pi,gid=pi,ro,iocharset=utf8,nofail,x-systemd.automount,_netdev 0 0
```
  - If the mount fails with a protocol error, add `,vers=3.0` after `ro`. Debug with `sudo mount -v /mnt/games`.
  - The same share is drive `Y:` on Windows: `Y:\Games\...` = `/mnt/games/Games/...`.
  - Share top level: `Documents  Games  HueyGoogle  Music  'Pictures & Videos'  PRojects  _Serato_  _Serato_Backup  TV`
  - ROM library: `/mnt/games/Games/MEGA FOLDER OF ROMS/Extracted folders/`, containing `Nintendo - NES`, `Nintendo - SNES` and `Sega - Genesis`. The old "Sega - Genesis (Update 1)" folder was merged into Sega - Genesis and deleted.
  - Format: one game per zip. RetroArch loads zips directly. Disc games need .cue/.chd/.m3u.
  - Not extracted yet: `/mnt/games/Games/Nintendo - Game Boy Advance.zip`.
  - Planned folders, which `add_cart.py` already searches: `Sony - PlayStation`, `Nintendo - Game Boy`, `Nintendo - Game Boy Color`, `Nintendo - Game Boy Advance`.
- **Project folder `~/cartridge/` (= `/home/pi/cartridge`):**
  - `cartridge_daemon.py`, `carts.json`, `add_cart.py`, `install_cores.sh`, `nfc_test.py`, `cartridge.service`, `cores/`, `venv/`
  - `logo.png`: unused by the current daemon
  - `nfc_test_uart.py`, `probe.py`: can be deleted
  - `huey_splash_pi.zip`
  - `splash/`, containing:
    - `huey_splash_player.py`: standalone, no longer used by the service
    - `PressStart2P.ttf`
    - `huey_variants/<ring>_<name>/{intro,loop}/huey_intro_###.png | huey_loop_###.png`: 320×240 frames. The intro is 126 frames and the loop is 120 frames at 30 fps.
    - `huey_variants/.last_variant`: no-repeat memory
  - The 8 variant folders: `jewel_gem-blue jewel_coral-pink jewel_gem-rose jewel_sunset-gold sunset_gem-blue sunset_coral-pink sunset_gem-rose sunset_sunset-gold`
- **`carts.json` format:**
```json
  {"044105532F0289": {"name": "Sonic The Hedgehog 2", "system": "genesis",
    "rom": "/mnt/games/Games/MEGA FOLDER OF ROMS/Extracted folders/Sega - Genesis/<file>.zip"}}
```
  - It is re-read on every insert, so new carts work without a restart.
- **Registering carts** (only one program can use the reader at a time):
```
  sudo systemctl stop cartridge
  cd ~/cartridge && venv/bin/python add_cart.py
  sudo systemctl start cartridge
```
- **systemd unit `/etc/systemd/system/cartridge.service`** (newest version from the prototype chat):
```
  [Unit]
  Description=Cartridge console (splash screen + NFC game launcher)
  After=multi-user.target
  Conflicts=getty@tty1.service

  [Service]
  User=pi
  WorkingDirectory=/home/pi/cartridge
  ExecStartPre=+/bin/sh -c 'dmesg -n 1; printf "\033[2J\033[H\033[?25l" > /dev/tty1'
  ExecStart=/home/pi/cartridge/venv/bin/python /home/pi/cartridge/cartridge_daemon.py
  Environment=SDL_VIDEODRIVER=kmsdrm
  StandardInput=tty
  StandardOutput=journal
  StandardError=journal
  TTYPath=/dev/tty1
  TTYReset=yes
  TTYVHangup=yes
  Restart=always
  RestartSec=2

  [Install]
  WantedBy=multi-user.target
```
  - Install: `sudo cp ~/cartridge/cartridge.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable cartridge`, then `sudo systemctl disable getty@tty1`.
  - Possible leftover drop-in: the splash chat first said to add `ExecStartPre=-/usr/bin/python3 /home/pi/cartridge/splash/huey_splash_player.py --max-seconds 8` via `sudo systemctl edit cartridge`. It later said to undo it with `sudo systemctl revert cartridge`, because the daemon now plays the splash itself.
    - Whether the drop-in was ever created, or reverted: (unverified)
    - Check with `systemctl cat cartridge`. If it's still there, the splash plays twice.
  - Logs: `journalctl -u cartridge -n 20 --no-pager`. The daemon prints `Splash variant: <name>` at start.
  - The service runs as `pi` and the old button code called `sudo poweroff`, which assumes passwordless sudo for `pi`. (unverified)
- **`/boot/firmware/config.txt` changes:**
  - `dtparam=i2c_arm=on`: confirmed via raspi-config.
  - `dtoverlay=disable-bt`: appended during the UART detour. Remove it to get Bluetooth back:
    `sudo sed -i '/dtoverlay=disable-bt/d' /boot/firmware/config.txt` (removal unverified)
  - Serial changes from the UART detour, still in effect: `raspi-config nonint do_serial_hw 0` (UART on), `do_serial_cons 1` (serial console off). Harmless, but can be reverted.
  - `dtparam=i2c_arm_baudrate=50000`: ONLY suggested if PN532 ACK errors persist. (unverified that it was added)
  - `disable_splash=1`: optional, hides the rainbow screen. (unverified)
  - `dtoverlay=gpio-shutdown,gpio_pin=17`: in the old SETUP.md only. Don't add it if the daemon handles GPIO17 through gpiozero.
- **`/boot/firmware/cmdline.txt` changes** (must stay ONE line; unverified both were applied):
  - `sudo sed -i 's/console=tty1/console=tty3/' /boot/firmware/cmdline.txt`
  - Append ` quiet loglevel=3 logo.nologo vt.global_cursor_default=0`. An earlier instruction used `loglevel=0`, so check for duplicates.
- **Current daemon, "HUEY edition"** (from the splash chat; newest version adds missing-splash diagnostics):
  - Settings:
    - `SCREEN=(320,240)`, using `pygame.FULLSCREEN|pygame.SCALED, vsync=1` so the GPU upscales.
    - `FPS=30`, `CHIME_FRAME=98`, `LOGO_LIFT=20`, `LOAD_SCREEN_SECS=2.0`, `REMOVAL_GRACE=1.5`, `PRESENCE_HOLD=0.6`, `POLL_TIMEOUT=0.2`.
  - The `Reader` class is a background thread: 30 init retries, `present()`, and `last_seen[uid]`. A `--demo` mode runs without the reader: keys 1–9 seat the carts in carts.json, 0 = unknown cart, SPACE = pull, ESC = quit.
  - Screens:
    - Intro, then the loop with blinking INSERT CARTRIDGE (pixel font, y=196, sub-line y=214).
    - Valid cart: chime + white flash, game name typed in the variant's accent color, ring speeds up under NOW LOADING, fade out, launch.
    - UNKNOWN CARTRIDGE + `TAG <uid>` in orange.
    - CARTRIDGE ERROR + reason.
    - RESEAT CARTRIDGE / TO PLAY AGAIN after quitting from the RetroArch menu with the cart still in.
    - After a game it fades back into the loop without replaying the intro.
  - Accent colors: gem-blue (111,160,255), coral-pink (255,79,121), gem-rose (255,107,138), sunset-gold (255,210,63).
  - It does NOT show the console name or use `logo.png`. It has NO GPIO button code.

## 5. Decisions made (with reasons) and rejected options
- **NFC tags instead of cartridges holding the game:** cheapest, no contacts to wear, and Ryan couldn't find cheap small USB sticks.
  - Rejected: USB-stick carts (no cheap low-capacity sticks), SD/microSD carts (contacts wear).
- **Top-loader, cart stays seated:** the console always knows whether a cart is in, so pulling it quits the game like a real console.
- **Custom pygame daemon instead of EmulationStation, RetroPie menus or a custom OS:** console-like behaviour with no menu and no game until a cart is in.
- **RetroArch from apt + prebuilt buildbot cores:** about 5 minutes to install.
  - Rejected: RetroPie compile. It took hours on the Pi 3; lr-fbneo alone was compiling for hours.
  - Rejected: Debian `libretro-*` packages, which lack the pcsx_rearmed PS1 core.
- **I2C reader mode:** the code was written for it. UART was tried as a fallback while debugging, but the real fault was a solder joint, so the setup returned to I2C.
- **Read ROMs straight from the NAS (read-only CIFS) instead of copying to SD.** Trade-off: the NAS must be on. Frequently played games can be copied to `~/roms` as a fallback.
- **Keep per-game zips** for cartridge systems. Disc games stay as bin/cue (or .chd), and `add_cart.py` offers only `.cue/.chd/.m3u/.pbp`.
- **Console boot (B1) instead of the desktop:** the desktop held the display and wasted RAM.
- **Output to the journal + console moved to tty3 + getty disabled:** black gaps between games instead of terminal text.
- **Splash style chosen:** true low-poly PS1/Crash-era 3D from a custom software renderer:
  - Vertex snapping, affine Gouraud shading, 15-bit color with the PS1 4×4 dither, 320×240 native, nearest-neighbour 2× upscale.
  - Rejected: flat 2D (Inter ExtraBold), then "cartoony" (Lilita One, thick outlines). Ryan wanted to "nail the ps1 era look."
- **Splash motion:**
  - The camera pans high three-quarter → three-quarter → classic.
  - An off-center oval ring is present from frame 1 and spins and wobbles continuously.
  - The letters float in space (no floor or shadows) and bob gently.
  - The U drops last with the biggest bounce, a full mid-air twirl and a jelly twist/bend.
  - Intro (126 frames, ~4.2 s) plus a seamless 120-frame loop.
- **Font:** Luckiest Guy, slightly thinner (`THIN=0.06`, `CONDENSE=0.94`).
  - Rejected: Titan One, Bungee, Russo One, Archivo Black, Passion One, Bowlby One, Rubik Mono One, Black Ops One (stencil), Chango, Lilita One.
  - Rejected PS-style fonts: Michroma, Krona One, Syncopate Bold, Orbitron Black, Audiowide.
- **U size:** same height as the other letters (`U_STRETCH=1.0`, `U_SCALE=1.0`). Rejected: the tall U (1.2) and a 3/4-size U on the baseline or floating.
- **Colors:** single-color names, all four letters one color, on darker jewel-tone rings.
  - Rejected: the primary PS1 colors, multicolor names (gem-tints, warm-glow, sunset, mint-cream), and chrome/gold metal names. Metal still exists as `NAME_MATERIAL` in the renderer.
  - Other palette ideas not chosen: Midnight Neon, Molten.
- **8 random startup variants** (2 rings × 4 names), never the same one twice in a row.
- **Splash merged into the daemon** instead of a separate `ExecStartPre` player: no gap or black flash, and the ring keeps spinning behind INSERT CARTRIDGE.
- **The ring was lowered** (`RING_Y` 0.6 → -0.3, classic camera target y 1.0 → 0.75) so it doesn't cover the letters.
- **Text font Press Start 2P** (pixel font) for the on-screen prompts.
- **Button:**
  - A momentary 16 mm button (tap = reset, hold 3 s = shutdown, optional diode power-on).
  - Rejected: the latching button (can't do reset or wake, would jam SCL) and a flip switch inline on 5 V. Ryan said the flip switch isn't needed.
  - Glowing slot or LED as the power indicator, instead of a button light.
- **Front panel USB ports via panel-mount extensions**, not Bluetooth-only, for dongles, wired controllers, charging and a keyboard. All cables exit the back.
- **Enclosure path:**
  - Genesis wedge v1 → smaller carts v2 → slim (rejected: "not a huge fan")
  - → sketches → capsule concepts (Ryan liked pebble + capsule, then two-tone + flat front, rounder front, flatter back, ribs, eject)
  - → capsule detailed v1 → walnut edition (current), styled to match his walnut tambour TV stand.
- **Walnut edition choices:**
  - Kept: crowned top (Ryan wanted it less flat), reeded body, marble thin line at the seam, inlaid flush marble front and rear plates, solid marble slot faceplate with no glow, eject key printed in wood or marble.
  - Removed: legs, a literal copy of the stand's door/arch front, and the H badge/letter.
  - Same size as the last detailed model.
- **Material:** regular PLA in wood color. Wood-fill PLA advice (0.6 nozzle, sanding/staining) was retracted.
- **Cart v3:**
  - Slide-in paper card. Rejected: clear-filament art window, and a sticker pocket (offered as the alternative).
  - Clip cap in the cart body color with a thin system-color strip, plus a name-sticker recess on top.
  - Keying groove moved to the BACK face so the front is clean for the label.
  - The existing faceplate and sleeve are installed rotated 180° (`slot_flip = true`) instead of redesigned.
- **Moonlight (not Steam Link)** for PC streaming, because Moonlight Embedded uses the Pi's hardware decoder. Sunshine is already on most of Ryan's PCs.
- **Real-cartridge support** is deferred (reader hardware: Epilogue Operators, GBxCart RW, sanni's OSCR).
- **PS1/Sony branding avoided:** the ring and letters only borrow the PS1 feel, not Sony's logo or wordmark.

## 6. Enclosure and carts
- **Design versions (oldest → newest):**
  - **cartridge_console v1:** Genesis-style wedge, 220×180×62 mm, round "Genesis ring" `slot_disc` (disc_r 65, flange_r 75 = 150 mm across).
    - Parts: shell, base, slot_disc, slot_sleeve, cart_front, cart_back.
    - Carts 100×80×18 with 6×3 magnets. Front key groove, tag in the back half.
    - File: `cartridge_console_v1.zip`.
  - **cartridge_console v2:** same shell. Carts shrunk to 76×60×10 (~25 g), insert depth 38 mm, 22 mm exposed. 5×2 magnets, key_x 15, shorter detent tongues. Disc and sleeve resized.
    - File: `cartridge_console_v2.zip`.
    - THIS is what was test-printed (sleeve + one cart, worked). The v2 slot_disc was printing.
  - **Slim:** 195×160×57, same disc and sleeve, rounder. Rejected.
    - File: `cartridge_console_slim.zip`.
  - **Concept renders only:** capsule v1–v5 (two-tone flat-front capsule, inserts, H badge, eject/rib variants A/B/C, final combination B top + front-wrapping C side ribs).
  - **Huey's Station detailed v1 (capsule):** 206×158×55. Superseded by walnut but still valid.
    - Parts: shell (light), band (dark), base, clear bezel with LED channel, sleeve v2 (plunger slots), lever, key, badge (H), front_insert (2×USB + 16 mm button), rear_insert (RJ45/HDMI/power), carts.
    - Eject: key travel 3.5 mm → lever tips ~12° → 2 plungers at ±30 mm lift the cart ~3.8 mm. A printed leaf spring on the base resets it.
    - File: `huey_station_v1.zip`.
  - **Walnut edition v1 (CURRENT console):** footprint 206×158 (front_r 30, back_r 20), overall 211×163×55 with reeds and cap overhang. ~520 g total.
    - Parts and materials:

      | STL | material | ~g | notes |
      |---|---|---|---|
      | cap | wood PLA | 182 | crowned top, 16 mm rise, ~55° max, prints upside down, no supports |
      | body | wood PLA | 75 | reeded tube, reed_r 1.9, pitch 5.2, vents hidden in reed valleys |
      | base | wood PLA | 117 | bottom lip, Pi standoffs 4 mm, eject pivots + leaf spring |
      | ring | marble | 10 | 2.5 mm line at the seam |
      | faceplate | marble | 70 | solid slot surround, same 10.5 mm stack as the old disc |
      | front_plate | marble | 7 | 2×USB + 16 mm button |
      | rear_plate | marble | 6 | RJ45/HDMI/power |
      | key | wood or marble | 3 | eject key |
      | lever | PETG preferred | 5 | eject seesaw |
      | sleeve | PETG preferred | 19 | v2, plunger slots |

    - Files: `huey_walnut_v1.zip` (`huey_walnut.scad`, `BUILD_GUIDE_WALNUT.md`, renders, `stl/`).
    - Updated `huey_walnut.scad` (`slot_flip = true`, cart v3, reader pocket moved to the front of the base) is in `huey_cart_v3.zip`. `huey_walnut_v1_backup.scad` was made before the flip (dev side, not sent).
    - Assembly:
      1. Reader into the sleeve rails.
      2. Sleeve → faceplate.
      3. Both installed ROTATED 180°: keying rib at the back, reader on the FRONT side of the slot.
      4. Faceplate → top.
      5. Key into its pocket.
      6. Pi on the base, USB end toward the back.
      7. Lever into the cradles.
      8. Panel mounts through the plates.
      9. Stack base → body → marble ring → top.
      10. 4 screws up through the base.
- **Carts:**
  - **v2 (printed test cart):** 76×60×10, key groove on the FRONT, tag in the BACK half.
    - Fit problem: in the flipped walnut slot, v2 carts are blocked or only fit backwards.
    - Its 25 mm tag sits ~10 mm above the reader center. It still read fine in testing.
  - **v3 (CURRENT, not printed):** 76 × 10 × 74 mm.
    - The bottom 38 mm (slot fit, click, tag position) is unchanged. 36 mm stands above the slot.
    - Halves: cart_front (card window + tag pocket, tag now in the FRONT half) and cart_back (key groove on the back).
    - 4× 5×2 magnets per half. 31 g per cart.
    - cart_cap: 8 mm, prints top face down, snaps on with 2 bumps, 3 g.
    - cart_strip: system color, 70×2.8×0.8 mm, pressed into the cap groove with a dot of CA.
    - Card channel 64×26 mm, about 60×24 visible through the window. Card thickness up to ~0.5 mm (cardstock or matte photo paper). Thumb notch to push the card out.
    - Name-sticker recess on the cap top: 60×6.4×0.6 mm (sticker 59×5.8).
    - Keying: the rib blocks backwards insertion (checked in CAD).
    - File: `huey_cart_v3.zip`.
- **Known fit risks / to verify:**
  - Panel-mount and button cutouts use typical sizes. Measure and edit the scad parameters `usb_face usb_body usb_screw hdmi_face rj_face pwr_face btn_d (16.3)`, then re-export the plates and body.
  - Port positions vs the actual Pi.
  - Card fit and cap snap on v3. Print one cart first.
  - Eject mechanism untested. Bench-print base + lever + key + sleeve + faceplate before the ~10 h cap.
  - NFC read reliability through the v3 front-half wall with the reader on the front side.
  - Size floors: the reader board is 41 mm tall (sets ~55 mm height). HDMI/USB plugs need 35–40 mm behind them (why the capsule grew from the 185×125 sketch).

## 7. Splash, branding and labels
- **Logo:** `huey.png` in Downloads, a Sega-like transparent HUEY logo. Copied to the Pi as `~/cartridge/logo.png` (unused now).
  - Color conflict: one chat summary says red background and white letters, while earlier notes and renders say blue. (unverified)
- **Console name:** "HUEY'S STATION" is a placeholder. The old daemon had `CONSOLE_NAME`; the HUEY daemon doesn't display a name.
- **Splash renderer:** `huey_splash_ps1.py` (dev side; PC copy outdated, see section 11).
  - Settings: `RW,RH=320,240`, `UPSCALE=2`, `FPS=30`, `FONT_FILE="fonts_luckiest-guy.woff"`, `THIN=0.06`, `CONDENSE=0.94`, `CURVE_STEPS=3`, `U_STRETCH=1.0`, `U_SCALE=1.0`, `CAM="path"`, `LOOP=120`, `LOOP_START=126`.
  - Letter timing: `DROP_START H16 E24 Y32 U46`, `FALL=13`, `U_FALL=16`.
  - Camera and sweep: `CAM_END=104`, `SWEEP 98+20`.
  - Ring: `OVAL=0.70`, `RING_Y=-0.3`, `RING_OFFSET=(0.22,0,0)`, `RING_TILT=7`, `RING_YAW=10`, `RING_DRIFT=(0.40,0.12,0.25)`, ring_mesh `N=48 Ro=5.5 Ri=4.55 h=0.46`.
  - Letter layout: `GAP=0.36`, `MAX_SPAN=7.4`.
  - `GLINTS=True`: pixel star glints during the sweep, staggered twinkles in the loop.
  - Camera presets:
    - high-three-quarter: `((-8.4,10.8,10.4),(0,0.6,0),42)`
    - three-quarter: `((-7.6,4.5,11.4),(0,0.9,0),40)`
    - classic: `((0,4.4,12.9),(0,0.75,0),40)`
  - Rings:
    - jewel = emerald (14,107,82), sapphire (27,58,140), garnet (122,20,40), old gold (168,120,15)
    - sunset = dusky teal (21,94,99), dark purple (59,24,86), magenta (122,23,86), amber (154,84,16)
  - Names (single color): gem-blue (111,160,255), coral-pink (255,79,121), gem-rose (255,107,138), sunset-gold (255,210,63).
  - Build all variants: `python3 huey_splash_ps1.py --variants` (~30 s each). The Pi pack is the frames downscaled to 320×240 nearest.
  - Dev dependencies: `mapbox_earcut`, `shapely`, `fontTools`, Pillow, numpy. Fonts come from `npm pack @fontsource/<name>`.
- **Sounds (generated in code):** the boot chime is B5 987.8 Hz → E6 1318.5 Hz at intro frame 98. The load blip is 659.3 / 987.8 / 1318.5 Hz.
- **Standalone player** `huey_splash_player.py` (not used by the service), flags:
  - `--max-seconds`, `--until-file /tmp/huey_ready`, `--variant <folder>`, `--min-loops`, `--window`
  - `--bg`: background color (hex)
  - `--fps`
  - `--dir`: frames folder (default `huey_variants` next to the script)
- **Labels:** `labels/make_labels.py` builds a Letter, 300 dpi, true-scale PDF.
  - Card art goes in `labels/art/` (cropped to fill 64×26 mm). Names in `labels/names.txt`, or taken from the art filenames.
  - `python make_labels.py` → `labels.pdf`. `--blank` → `labels_blank.pdf`.
  - Print at 100% / Actual size. Names on sticker paper.
  - Strip color ideas: NES red, SNES purple, Genesis black, GBA indigo, PS1 gray, Moonlight green.
- **Dropped branding items:** the H badge (capsule design only) and the earlier "R + S shapes with Ryan's name" intro idea (superseded by HUEY).

## 8. Problems and fixes
1. `i2cdetect`: "Could not open /dev/i2c-1". Fix: `sudo raspi-config nonint do_i2c 0` + reboot.
2. Empty i2cdetect grid / `ValueError: No I2C device at address: 0x24`.
   - Tried: full power-off, swapping SDA/SCL, `pinctrl get 2,3` (both `hi`, so no short on the Pi side), UART mode (`RuntimeError: Failed to detect the PN532`).
   - Root cause: cold joint on TXD/SDA plus a near-bridge to VCC on the PN532 header.
   - Fix: wick the gap, reflow, clean the solder balls. Then it worked: test reads OK.
3. `echo ... | sudo tee -a` split across two lines executed config.txt as a script. Harmless; re-run as one line.
4. `systemctl disable hciuart`: unit doesn't exist on new Pi OS. Ignore.
5. `~/cartridge` missing: create with `mkdir -p`. The short `nfc_test.py` was created via heredoc.
6. RetroPie compiling for hours (lr-fbneo). Fix: Ctrl+C, then `install_cores.sh` with prebuilt cores (~5 min).
7. NAS path "No such file". The share wasn't mounted yet: `sudo mount -v /mnt/games`, then follow `ls` down. Linux paths are case-sensitive.
8. `add_cart.py` not on the Pi: scp it over.
9. `RuntimeError: Did not receive expected ACK from PN532!`
   - Fix: added `init_reader()` retries (10 in add_cart, 30 in the daemon).
   - Make sure nothing else holds the reader (`pgrep -af python`, stop the service).
   - Fallback: `dtparam=i2c_arm_baudrate=50000`.
10. HDMI showed the Pi desktop: `raspi-config nonint do_boot_behaviour B1` (B4 to restore).
11. Terminal text between games. Fix: Popen stdout/stderr to DEVNULL, `StandardOutput=journal`, `ExecStartPre=+` tty clear, `disable getty@tty1`, `console=tty3` + quiet flags.
12. Old boot animation was laggy. Fix: 720p `SCALED` + pre-rendered frames. Superseded by the 320×240 HUEY daemon with a background reader thread.
13. Existing button is latching. Fix: momentary button ordered; latching mode not implemented.
14. Splash renderer artifacts (dev side), with fixes:
    - Dark wedges on curved fonts → `mapbox_earcut` triangulation.
    - Self-intersecting bevels → shapely validity check that shrinks the bevel.
    - 1 px ring seam crack → rounding epsilon.
    - H/U collision → GAP 0.36.
    - Ring overshoot clipping → softened.
    - 48 MB zip upload failure → split zips.
15. `sudo systemctl restart cartridge` hung ~90 s: the OLD daemon ignored SIGTERM. One-time; the new daemon stops promptly.
16. No HUEY logo after the merge: `~/cartridge/splash/huey_variants` didn't exist (zip never unzipped). Fix:
```
    cd ~/cartridge && unzip -o huey_splash_pi.zip
```
    Then scp `PressStart2P.ttf` to `~/cartridge/splash/`. The daemon now logs the variant and shows an orange "SPLASH FILES MISSING" warning.
17. Ring covered the letters: `RING_Y = -0.3`, re-rendered `huey_splash_pi.zip`. Deploy (unverified):
```
    scp $HOME\Downloads\huey_splash_pi.zip pi@pi.local:~/cartridge/
    cd ~/cartridge && unzip -o huey_splash_pi.zip && sudo systemctl restart cartridge
```
18. **OPEN — button regression.** The HUEY-edition daemon (splash chat) has no button support. The prototype chat's version had it:
    - `BUTTON_PIN=17`, `HOLD_TO_SHUTDOWN=3.0`
    - gpiozero `Button(17, pull_up=True, bounce_time=0.05, hold_time=3.0)`
    - `when_held` → shutdown event, `when_released` (if not held) → reset event
    - `run_game` returns "removed" / "quit" / "reset" / "shutdown"
    - reset → "Restarting..." + relaunch; shutdown → "SHUTTING DOWN" screen + `sudo poweroff`
    - taps on the splash screen ignored

    This needs porting into the HUEY daemon. Note the reader there is a background thread.
19. **OPEN:** Bluetooth possibly still disabled (`dtoverlay=disable-bt`).
20. **OPEN:** v2 test carts (front groove) won't fit the flipped walnut slot. Reprint as v3.
21. Wood-fill PLA assumption was wrong. The build guide was corrected to regular PLA settings.
22. Walnut fit fixes (in CAD): Pi standoff 5 → 4 mm, plates raised to z=13, top lip 4 → 3 mm. Plunger holes became slots, because the plungers swing as the lever tips.

## 9. Open to-do list (priority order)
1. Check the Pi state:
   - `systemctl cat cartridge`: no splash `ExecStartPre` drop-in left over.
   - `cat /boot/firmware/config.txt /boot/firmware/cmdline.txt`: cmdline still one line, no duplicate flags.
   - Deploy the lowered-ring `huey_splash_pi.zip` if not done.
2. Port the GPIO17 button code into the HUEY daemon (tap = reset game, hold 3 s = safe shutdown) and `sudo apt install -y python3-gpiozero`.
   - Then wire the momentary button: one tab → pin 9, other → pin 11. Use heat-shrink or spade connectors.
3. Remove `dtoverlay=disable-bt`, `sudo apt install -y bluez pi-bluetooth`, pair the controllers (`bluetoothctl`: `scan on`, then `pair`/`trust`/`connect <MAC>`), and test in-game.
   - Optionally set a RetroArch menu hotkey (default Select+Start) for save states.
4. PS1:
   - Move the bin/cue folders to `...\Extracted folders\Sony - PlayStation`.
   - Copy the BIOS (`scph5501.bin`, lowercase) to `~/.config/retroarch/system/`.
   - Register psx carts.
   - Write a `.m3u` generator for multi-disc games (register Disc 1 until then).
5. Extract `Nintendo - Game Boy Advance.zip` (plus any GB/GBC) into `Extracted folders` with the exact folder names `add_cart.py` expects.
6. Confirm the RetroArch save/state dirs are set. Remove the template entries from `carts.json`.
7. When parts arrive: measure the panel mounts (face size, screw spacing) and the button (thread length, body depth). Update the `huey_walnut.scad` parameters and re-export `front_plate`, `rear_plate`, `body`.
8. Bench-test the eject: print base, lever, key, sleeve (walnut v2 sleeve with plunger slots) and faceplate. Install the faceplate and sleeve rotated 180°.
9. Print one v3 cart. Check card fit, cap snap, magnet polarity, keying, and NFC read reliability (`venv/bin/python nfc_test.py`, which reports read %).
10. Print the walnut body, ring, plates and cap (~10 h), then assemble per `BUILD_GUIDE_WALNUT.md`.
11. Print labels with `make_labels.py`. Print strips in system colors.
12. Moonlight cart: install Moonlight Embedded, pair with Sunshine, add a "moonlight" system or cart type to the daemon that launches the stream instead of RetroArch. Pulling the cart ends the stream.
13. Pick a better console name.
14. Optional: diode power-on (level 2), `disable_splash=1`, delete `~/RetroPie-Setup`, `nfc_test_uart.py`, `probe.py`.

## 10. Ideas for later
- Moonlight/Sunshine PC streaming cart (Sunshine already on most PCs). Could cover GoldenEye and Dreamcast games the Pi 3 can't emulate.
- Real original cartridge support: a slot that fits real carts plus a USB reader (Epilogue GB/SN Operator, GBxCart RW, sanni Open Source Cartridge Reader), a microswitch, dump-once caching, and saves written back to the cart.
- A glowing slot with WS2812B: breathing while waiting, a sweep on insert, a color per system, amber for an unknown cart, and dark = safe to unplug. This would need a clear bezel; the walnut uses solid marble.
- A pinstripe accent ring, a spring-loaded dust flap, a matching walnut/marble cart rack (8–12 carts), a hidden controller-dongle bay.
- Alternative loading styles (sketched only): tower side-loader, swing-down tray (Ryan's idea), push-push drawer, flip-up clear lid, angled front-loader, toaster tower. Claude's favorites were the tray and the lid.
- Cart extras: per-system strip colors, era-inspired cart tops, finger grip, spine labels.
- Upgrade the brain to a Pi 5 or an N100 mini PC for N64, Dreamcast, PSP, GameCube and PS2.
- A chrome or gold metal name variant for the splash (supported by the renderer).
- Party-game carts: Mario Kart 64 and Smash 64 are playable on the Pi 3; Bomberman, CTR, Tekken 3.
- Cheap ESP32-C3 + PN532/RC522 readers for other home NFC uses, separate from the console.

## 11. Files
Prototype chat (most also delivered to `C:\Users\huey2\Downloads`):
- `cartridge_daemon.py`: console daemon. Prototype-chat versions, in order:
  - initial (RetroPie paths)
  - prebuilt cores + `~/roms`
  - reader retry
  - logo-zoom intro + chime + `CONSOLE_NAME`
  - 720p `SCALED` + pre-rendered frames + DEVNULL
  - **button support (newest in this chat)**
  - Superseded by the HUEY edition below.
- `carts.json`: template with 2 example entries. The live copy is on the Pi.
- `cartridge.service`: newest has the `ExecStartPre=+` tty clear and journal output (section 4).
- `SETUP.md`: original setup guide. OUTDATED (RetroPie paths, `~/RetroPie/BIOS`).
- `nfc_test.py`: bench test that prints `TAG IN/OUT` and read reliability %.
- `nfc_test_uart.py`, `probe.py`: UART debug only (created on the Pi via heredoc). Can be deleted.
- `install_cores.sh`: apt retroarch + 6 buildbot cores + `~/roms` folders + `~/.config/retroarch/system`.
- `add_cart.py`: cart registration. Newest has PS1/GB/GBC/GBA folders, disc-file filtering and 10× reader retry.
- `logo.png`: copy of `huey.png`. `boot_preview.gif`: preview of the old intro.
- Enclosure files:
  - `cartridge_console_v1.zip`: `cartridge_console.scad`, `PRINTING.md`, `stl/`, `preview_front.png`
  - `cartridge_console_v2.zip`: small carts; matches the printed test parts
  - `cartridge_console_slim.zip`: `cartridge_console_slim.scad`, `PRINTING_SLIM.md`, `stl_slim/`, `preview_slim.png`
- Concept images: `concept_sheet.png`, `concept_v2_sheet.png`, `concept_v3_sheet.png`, `colorways.png`, `eject_ribs_sheet.png`, `concept_v5_sheet.png`, `wood_concepts.png`, `accent_concepts.png`, `walnut_marble.png`, `cart_v2_concept.png`. Inline sketch widgets were also shown (shell shapes, loading styles, cart concepts).
- `huey_station_v1.zip`: capsule detailed model (`huey_station.scad`, `BUILD_GUIDE.md`, 12 STLs, `huey_station_renders.png`). Superseded by walnut.
- `huey_walnut_v1.zip`: walnut edition (`huey_walnut.scad`, `BUILD_GUIDE_WALNUT.md`, `walnut_edition_renders.png`, `stl/`: cap, body, ring, base, faceplate, sleeve, lever, key, front_plate, rear_plate, cart_front, cart_back). Re-sent once with corrected filament notes. Use these STLs for every console part EXCEPT base.
- **`huey_cart_v3.zip` (newest enclosure package):**
  - `huey_walnut.scad` with `slot_flip=true` + cart v3
  - `CART_V3.md`, updated `BUILD_GUIDE_WALNUT.md`, `cart_v3_slidein.png`
  - `stl/`: cart_front, cart_back, cart_cap, cart_strip, base (reader pocket moved to the front; replaces the walnut v1 base)
  - `labels/`: `make_labels.py`, `labels_blank.pdf`, `labels_sample.pdf`, `art/Huey's Station.png`
- Inline wiring diagrams: `pn532_to_pi3_i2c_wiring`, `metal_button_to_pi3_wiring`.

Splash chat:
- Superseded splash versions:
  - `huey_splash.py` + `huey_splash.png` (APNG), `huey_splash_frames.zip`, `huey_logo_final.png`: flat v1
  - `huey_splash_toon.py`, `LilitaOne.woff`, `huey_splash_toon.png`, `huey_logo_toon_final.png`, `huey_splash_toon_frames.zip`: cartoon version
  - `huey_splash_ps1.png`, `huey_logo_ps1_final.png`, `huey_splash_ps1_frames.zip`: first 3D version
- `huey_splash_ps1.py`: the 3D renderer.
  - The newest copy on Ryan's PC came in `huey_variants_sunset.zip` and predates the ring change (`RING_Y=0.6`).
  - The newest version (`RING_Y=-0.3`, classic camera `((0,4.4,12.9),(0,0.75,0),40)`) was NOT re-sent. Edit those two lines locally.
- Mockup and preview images: `demo_fonts.png`, `demo_angles.png`, `mockups_fonts.png`, `mockups_colors.png`, `huey_chrome_jewel_preview.png`, `mockups_mono.png`, `huey_variants_sheet.png`, `ring_heights.png`.
- Intro/loop outputs (pre-variant, multicolor): `huey_preview.png`, `huey_intro.png`, `huey_loop.png`, `huey_frames.zip`.
- `huey_variants_jewel.zip` + `huey_variants_sunset.zip`: 640×480 variant frames + player + renderer + `fonts_luckiest-guy.woff`. Superseded by the Pi pack.
- `huey_splash_player.py`: standalone random-variant player. The newest version is inside the Pi pack.
- **`huey_splash_pi.zip` (newest):** `splash/` with all 8 variants at 320×240 (lowered ring), `PressStart2P.ttf`, `huey_splash_player.py`.
- `PressStart2P.ttf`: pixel font for the daemon text.
- **`cartridge_daemon.py`, HUEY edition (NEWEST daemon):** splash merged, background reader thread, `--demo` mode, missing-splash diagnostics. Lacks button support. `d_sheet.png` previews its screens.
