# Huey's Station — Build Guide

**Size:** 206 × 158 × 55 mm. Every part fits the P1S bed and every colored part is
its own STL, so you can reprint any piece in a new color.

## Parts to print

| STL | Suggested color | Orientation (already set) | ~g | Notes |
|---|---|---|---|---|
| shell | Light (PS1 gray) | Upside down on its top | 188 | No supports. Ribs on top are grooves, side ribs have a 45° top so they print cleanly |
| band | Dark | Right side up | 44 | Lower band with lip + ledge |
| base | Dark | Flat | 101 | Pi standoffs, lever pivots, return spring, vents |
| bezel | **Clear** | Flange down | 58 | Glows from the LED strip underneath. Turn on ironing for the top |
| sleeve | Any | Flange down | 19 | v2 of your sleeve: same cart fit + plunger slots. PETG recommended |
| lever | Accent | Flat | 5 | Eject seesaw. PETG recommended |
| key | Accent | Cap down | 3 | Eject key |
| badge | Accent | Flat | 1 | Glue into the pocket in front of the slot |
| front_insert | Accent | Flat | 8 | 2× USB + 16 mm button |
| rear_insert | Accent | Flat | 6 | Ethernet, HDMI, power |
| cart_front / cart_back | Any | Outer face down | 25/cart | Unchanged |

0.2 mm layers, 3 walls, 15% gyroid. Print the base spring and lever in PETG if you can,
so the spring keeps its push.

## Hardware
- 4× M3×10 self-tapping: base → shell (through the band)
- 2× M3×8 self-tapping: bezel ears → shell
- 4× M3×8 self-tapping: sleeve → bezel
- Panel-mount extensions: 2× USB-A, 1× HDMI, 1× micro-USB (power), 1× RJ45 (optional), ~15–30 cm each
- 16 mm momentary metal button
- WS2812B 5 V LED strip, about 15 LEDs (60/m), for the slot glow
- 4× rubber feet (10 mm)

## Assembly order
1. **Reader:** slide the PN532 up the rails on the back of the sleeve until it stops; dab of hot glue.
2. **LED strip:** stick it in the channel on the underside of the bezel, LEDs facing up. Run the wires out the notch toward the left ear.
3. **Sleeve → bezel:** 4 screws into the pocket under the bezel.
4. **Bezel → shell:** push the bezel up through the pill opening from inside, 2 screws through the ears.
5. **Eject:** drop the key into its pocket from the top. Snap the lever's pivot stubs into the cradles on the base (plungers forward, under the slot).
6. **Pi:** screw onto the base standoffs (USB end toward the back). Plug in the panel-mount cables and the reader/button/LED wires.
7. **Inserts:** screw the panel mounts through the inserts and the shell wall; button nut clamps the front insert.
8. **Close:** fit the band onto the shell (lip slides inside), set the base into the band, 4 screws up into the shell.
9. Badge: glue the H into its pocket.

## Wiring summary
| From | Pi pin |
|---|---|
| Reader VCC / GND / SDA / SCL | 1 / 6 / 3 / 5 (unchanged) |
| Button | 9 (GND) + 11 (GPIO17); optional power-on via diodes to pin 5 |
| LED strip 5V / GND / DIN | 2 (5V) / 14 (GND) / 19 (GPIO10) |

## Measure before the big print
Panel-mount cutouts use typical sizes. Check yours against the parameters at the top
of `huey_station.scad` (`usb_face`, `usb_screw`, `hdmi_face`, `rj_face`, `pwr_face`...),
change the numbers, and re-export just the inserts and shell.

## Eject mechanism
Press the key 3.5 mm → the lever tips 12° → two plungers rise through the sleeve floor and
lift the cart ~3.8 mm past its click. The printed leaf spring on the base resets it.
