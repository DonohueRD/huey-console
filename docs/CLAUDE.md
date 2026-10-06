# HUEY Console ("Huey's Station", placeholder name)

Ryan's Raspberry Pi 3 retro console that plays games from NFC-tagged 3D-printed cartridges.
Seat a cart on the PN532 reader and `cartridge_daemon.py` shows the game name and launches
RetroArch. Pull the cart and the game closes, returning to the spinning PS1-style HUEY splash.

Full history (every decision, rejected option, past bug, hardware detail and file version):
`Y:\PRojects\HueyConsole\docs\PROJECT_HISTORY.md`. Read the relevant section before redesigning
anything. Many options were already tried and rejected for a reason.

## Working on the Pi
- `ssh pi "command"` (key auth, IPv4 forced; `pi.local`, last seen at 192.168.1.169). Copy with `scp file pi:~/cartridge/`.
- PowerShell mangles quotes in multi-line ssh commands. For anything non-trivial, write a script
  and pipe it with CRLF stripped and no BOM: `(Get-Content -Raw x.sh) -replace "`r","" | ssh pi "bash -s"`.
- **`sudo` on the Pi needs a password**, so it can't run non-interactively. Give Ryan the sudo commands to
  run, or ask Ryan to add a sudoers rule.
- Service: `cartridge` (runs as `pi` on tty1 with SDL kmsdrm). Logs: `journalctl -u cartridge -n 50 --no-pager`.
  Stop it before running `add_cart.py` or `nfc_test.py`: only one program can use the reader at a time.
- Run reader scripts with `~/cartridge/venv/bin/python`, never plain `python3`.
- Read the current file on the Pi before changing it. Keep the NAS copy in sync after a change.

## Verified state (checked over SSH 2026-10-04)
- Pi 3 Model B Rev 1.2, Raspberry Pi OS Trixie (Debian 13) 64-bit, Python 3.13, pygame 2.6.1.
- `cartridge` enabled and active. No drop-ins, so the splash plays once. `getty@tty1` disabled. Last boot picked variant `sunset_coral-pink`.
- These files on the Pi are byte-identical to the NAS copies: `cartridge_daemon.py`, `add_cart.py`, `carts.json`, `huey_splash_pi.zip`.
  The lowered-ring splash is deployed: 8 variants are in `~/cartridge/splash/huey_variants`, plus `PressStart2P.ttf`.
- 6 cores are in `~/cartridge/cores`. PS1 BIOS `scph5501.bin` is in `~/.config/retroarch/system`.
- Saves go to `~/.config/retroarch/saves` and `~/.config/retroarch/states`, both local.
- NAS automounts at `/mnt/games` (read-only). ROMs are in `/mnt/games/Games/MEGA FOLDER OF ROMS/Extracted folders/` (the `SHARE` path in `add_cart.py`).
  It has `Nintendo - NES` (275), `Nintendo - SNES` (325), `Sega - Genesis` (175), `Sony - PlayStation`, `Nintendo - Game Boy Advance` (162, added 2026-10-04),
  plus `Nintendo - N64`, `Gamecube`, `Sony - PS2`, `ROM Hacks` and `Tekken`, which `add_cart.py` doesn't map. GB/GBC folders don't exist yet.
  The PS1 folder was renamed from `Sony - PS1` on 2026-10-04 to match `add_cart.py`.
  It holds 215 `.chd` files and 176 `.m3u` playlists, one per game, multi-disc included, with relative paths.
  Crash Bash (USA) is a `.cue`/`.bin` subfolder only. Tekken 3 has both an `.m3u` and a `.cue` subfolder, so pick the `.m3u`.
  When registering PS1 carts, pick the game's `.m3u`, not a single disc's `.chd`.
- config.txt: `dtparam=i2c_arm=on` and `enable_uart=1`. `disable-bt` is gone, so Bluetooth isn't blocked. No baudrate override, no `disable_splash`.
- cmdline.txt is one line with `console=tty3 ... quiet loglevel=3 logo.nologo vt.global_cursor_default=0`. `quiet` appears twice, which is harmless.
- Installed: `python3-gpiozero` 2.0.1, `bluez`. Not installed: `pi-bluetooth`, `tmux`.
- `carts.json` has Sonic The Hedgehog 2 (`044105532F0289`) plus the 2 template entries.
- Leftovers that can be deleted: `~/RetroPie-Setup`, `/opt/retropie`, `~/cartridge/nfc_test_uart.py`.

## Known issues
- v2 test carts (key groove on the front) don't fit the flipped walnut slot. Print v3 carts.

## Not planned: power/reset button
Ryan has no button, so button support is on hold. Don't add button code or wiring unless asked.
If it comes back: the old spec is in PROJECT_HISTORY.md §3 and §8.18. Shutdown would need a sudoers rule,
because `pi` has no passwordless sudo. The walnut `front_plate` still has a 16 mm button hole, so cover it or remove `btn_d`.

## To-do (priority order)
1. Remove the template entries from carts.json.
2. Bluetooth controllers: install `pi-bluetooth` if needed, pair with `bluetoothctl`, test in-game.
3. Register PS1 carts (pick the `.m3u`).
4. Extract GBA (and GB/GBC) into `Extracted folders/` using the folder names `add_cart.py` expects.
5. Panel mounts: HDMI measured and set (`hdmi_face` 18.6x8, `hdmi_screw` 28). USB spacing is unconfirmed. RJ45 and power aren't bought yet, so they use standard dims.
   Print `huey_cart_v3/stl/port_test.stl` (`part = "port_test"`) to check the fit, then re-export front_plate, rear_plate and body.
   Export from the CLI with `openscad.com` (not the .exe) and a wrapper .scad that sets `part`.
6. Bench-print the eject (base, lever, key, sleeve, faceplate, rotated 180°). Print one v3 cart and test fit and NFC read %.
7. Print the full walnut enclosure (~10 h cap) and assemble per `BUILD_GUIDE_WALNUT.md`. Print labels and strips.
8. Moonlight streaming carts: N64/GameCube/PS2 run on a desktop (HUEYDESKTOP, RTX 3080, Sunshine already running) and stream to the Pi.
   One cart per game: seat = `moonlight stream <host> "<App>"`, pull = `moonlight quit`. Must also work with a second desktop host.
9. Later: a better console name, cleanup of leftovers.

## Hardware quick reference
- PN532 V3 in I2C mode (SW1 ON, SW2 OFF), address 0x24. VCC pin 1 (3.3 V), GND pin 6, SDA pin 3, SCL pin 5.
  GPIO3 is SCL, so never put a latching button on it. Diode power-on is optional (§3 of the history).
- Carts: NTAG215 25 mm stickers, 5x2 mm magnets (4 per half). Printer: Bambu P1S. Regular wood-colour PLA (not wood-fill) plus marble PLA. PETG for the sleeve and lever.
- Pi 3 runs NES/SNES/Genesis/GB/GBC/GBA and most PS1 at full speed. N64 is hit-or-miss. Nothing newer.

## Files (`Y:\PRojects\HueyConsole\`, NAS `\\192.168.1.12\HueyRaid1`; same share is `/mnt/games` on the Pi)
- Software: `cartridge_daemon.py` (HUEY edition, current), `add_cart.py`, `carts.json`, `cartridge_3.service` (current unit),
  `install_cores.sh`, `huey_splash_pi.zip` (Pi splash pack), `PressStart2P.ttf`. `SETUP.md` is OUTDATED (RetroPie paths).
- Splash renderer: `huey_splash_ps1.py` (RING_Y -0.3 and lowered classic camera applied 2026-10-04).
  Build with `--variants`. Needs mapbox_earcut, shapely, fontTools, Pillow, numpy and `fonts_luckiest-guy.woff`, which isn't on the NAS yet.
- Enclosure: `huey_walnut_v1/` (current console; use its STLs except `base`), `huey_cart_v3/` (current carts, new base,
  updated scad with `slot_flip=true`, labels), `huey_station_v1/` (capsule, superseded).
- `d_sheet.png`: all daemon screens. `huey_frames/`: splash frames. `reference/`: walnut TV stand photos (the style target).
- `old_versions/`: older daemon, v1 bundle, old service files. `docs/PROJECT_HISTORY.md`: the full history.
- Test the daemon on the PC: `python cartridge_daemon.py --demo` (keys 1-9 seat carts, 0 unknown, SPACE pull, ESC quit).
- Backups: `Y:\PRojects\Backups\`, `C:\Users\huey2\Backups\`.
