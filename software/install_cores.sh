#!/bin/bash
# Installs RetroArch + prebuilt emulator cores. No compiling, takes a few minutes.
set -e
case "$(uname -m)" in
  aarch64) ARCH=aarch64 ;;
  armv7l)  ARCH=armhf ;;
  *) echo "Unsupported CPU: $(uname -m)"; exit 1 ;;
esac

echo "== Installing RetroArch =="
sudo apt update
sudo apt install -y retroarch unzip wget

echo "== Downloading cores for $ARCH =="
mkdir -p ~/cartridge/cores
cd ~/cartridge/cores
for c in fceumm snes9x2010 genesis_plus_gx gambatte mgba pcsx_rearmed; do
  wget -q --show-progress -O "$c.zip" \
    "https://buildbot.libretro.com/nightly/linux/$ARCH/latest/${c}_libretro.so.zip"
  unzip -o -q "$c.zip" && rm "$c.zip"
done

echo "== Creating ROM folders =="
mkdir -p ~/roms/{nes,snes,megadrive,gb,gbc,gba,psx}
mkdir -p ~/.config/retroarch/system   # PS1 BIOS goes here (optional)

echo
echo "Done. Cores installed:"
ls ~/cartridge/cores
