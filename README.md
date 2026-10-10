# HUEY Console
A Raspberry Pi 3 retro console that plays games from NFC-tagged 3D-printed cartridges. Seat a cart on the PN532 reader and the daemon shows the game name and launches RetroArch. Pull the cart and the game closes, returning to the spinning HUEY splash.

**Current Status:** Actively developed and tested on Raspberry Pi 3 Model B Rev 1.2, Raspberry Pi OS Trixie (Debian 13) 64-bit.
**Word of warning** - This is a claude assisted personal project.  It is just for fun and I have done this to see what I could push myself to create on my own.  All errors and terrible slop coding are a learning experience and comments and assists are appreciated for improvement.

## Features

- **NFC-based cartridge detection** — tap a 3D-printed cart with an NTAG215 sticker to launch a game
- **Multi-system support** — NES, SNES, Genesis, Game Boy, Game Boy Color, Game Boy Advance, PlayStation 1
- **Bluetooth controller support** — auto-pairs and connects wireless controllers on boot
- **Customizable splash art** — 8 themed intro/loop variants with auto-rotation
- **Moonlight streaming ready** — infrastructure for N64, GameCube, PS2 streaming from a secondary host
- **Minimalist UI** — PS1-style 320x240 resolution with custom pixel fonts

## Hardware

- **Console:** Raspberry Pi 3 Model B Rev 1.2, 64-bit OS
- **Reader:** PN532 V3 in I2C mode (I2C address 0x24)
- **Cartridges:** NTAG215 25mm NFC stickers + 5x2mm magnets
- **Emulation:** RetroArch with per-core libretro cores
- **Enclosure:** 3D-printed wood-textured case (PLA + PETG)
- **Printer:** Bambu P1S

## Quick Start

### On the Pi

1. **Set up the reader** on GPIO3 (SCL) and GPIO2 (SDA), VCC to 3.3V, GND to GND.
2. **Install dependencies:**
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-gpiozero bluez
   python3 -m venv ~/cartridge/venv
   ~/cartridge/venv/bin/pip install adafruit-circuitpython-pn532 pygame
   ```
3. **Copy files** from this repo to `~/cartridge/`:
   - `cartridge_daemon.py`
   - `add_cart.py`
   - `carts.json` (starts empty)
   - `PressStart2P.ttf`
   - `install_cores.sh` (then run it to fetch libretro cores)
4. **Configure RetroArch:** Ensure cores are in `~/cartridge/cores/` and BIOS files are in `~/.config/retroarch/system/`.
5. **Set up the service:**
   ```bash
   sudo cp cartridge_3.service /etc/systemd/system/cartridge.service
   sudo systemctl enable cartridge
   sudo systemctl start cartridge
   ```

### Registering Cartridges

Stop the daemon first (only one program can use the reader at a time):
```bash
sudo systemctl stop cartridge
~/cartridge/venv/bin/python ~/cartridge/add_cart.py
```

Tap a tag, pick the system, search for a game, confirm the name. Repeat for each cart.

Then restart the console:
```bash
sudo systemctl start cartridge
```

## Project Structure

- **`software/`** — Python daemon, cartridge registration tool, systemd service file
- **`hardware/`** — OpenSCAD designs and exported STL files for 3D printing
  - `huey_walnut_v1/` — current console enclosure (wood-style PLA)
  - `huey_cart_v3/` — current cart design with card slots
  - `huey_station_v1/` — older capsule variant (superseded)
- **`splash/`** — splash screen renderer and frame data
- **`docs/`** — build guides, hardware reference, project history

## Building the Enclosure

See `hardware/huey_walnut_v1/BUILD_GUIDE_WALNUT.md` for assembly instructions.

**Print settings:**
- Bambu P1S, PLA regular (not wood-fill), 0.2mm layers
- Supports for complex parts only; most snap together
- Total print time ~10 hours for the full enclosure

## Games & ROM Organization

ROMs are stored on a network share mounted at `/mnt/games/Games/MEGA FOLDER OF ROMS/Extracted folders/`:
- `Nintendo - NES/` (275 games)
- `Nintendo - SNES/` (325 games)
- `Sega - Genesis/` (175 games)
- `Sony - PlayStation/` (215 games via `.m3u` playlists)
- `Nintendo - Game Boy Advance/` (162 games)
- And more: N64, Gamecube, PS2, Game Boy, Game Boy Color, ROM Hacks

## Troubleshooting

**Reader not found:**
- Check I2C wiring (SCL/SDA) and enable I2C in raspi-config
- Verify address: `i2cdetect -y 1` should show `0x24`

**Game won't launch:**
- Ensure the core file exists: `ls ~/cartridge/cores/`
- Check ROM path: `ls /mnt/games/...` or `~/roms/...`
- View logs: `journalctl -u cartridge -n 50 --no-pager`

**Controller not detected:**
- Ensure Bluetooth is powered on: `bluetoothctl power on && bluetoothctl pairable on`
- Pair manually: `bluetoothctl pair <mac>`
- Check sysfs: `ls /sys/class/input/event*`

## Known Issues & Limitations

- v2 test carts don't fit the flipped walnut slot; use v3 carts instead
- Pi 3 struggles with N64; most games run at partial speed (handled by Moonlight streaming on secondary host)
- No power/reset button (can be added if needed)

## To-Do

- [ ] Register remaining PS1 carts
- [ ] Extract GBA and GB/GBC into proper folder structure
- [ ] Print and assemble full walnut enclosure
- [ ] Set up Moonlight streaming for N64/GameCube/PS2
- [ ] Custom panel mounts for HDMI, USB, power, network

## License

This is a personal maker project. Feel free to adapt it for your own use.

## Project History

For full context on every decision, rejected option, hardware detail, and past bug, see `docs/PROJECT_HISTORY.md`.
