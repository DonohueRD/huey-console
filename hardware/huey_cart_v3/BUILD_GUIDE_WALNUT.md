# Huey's Station — Walnut Edition: Build Guide

**Size:** 211 × 163 × 55 mm (same footprint as the v1 detailed model).
About 520 g of filament in total. Every part fits the P1S bed and each one is a
separate STL, so any piece can be reprinted in a different material later.

## Parts

| STL | Material | Orientation (set) | ~g | Notes |
|---|---|---|---|---|
| cap | Wood-color PLA | Upside down on its flat plateau | 182 | Crowned top, max overhang ~55°, no supports |
| body | Wood-color PLA | Right side up | 75 | Reeded walls (open tube), vents hidden in the reed valleys |
| base | Wood-color PLA | Flat | 117 | Doubles as the thin bottom lip. Pi standoffs, eject pivots + spring |
| ring | Marble | Flat | 10 | Thin marble line between body and top |
| faceplate | Marble | Flange down | 70 | Solid marble slot surround (same stack as the old disc) |
| front_plate | Marble | Flat | 7 | Inlays flush: 2× USB + 16 mm button |
| rear_plate | Marble | Flat | 6 | Inlays flush: Ethernet, HDMI, power |
| key | Wood-color or marble | Cap down | 3 | Eject key |
| lever | Any (PETG best) | Flat | 5 | Eject seesaw |
| sleeve | Any (PETG best) | Flange down | 19 | v2 sleeve with plunger slots; same cart fit and click |
| cart_front / cart_back | Wood-color PLA | Outer face down | 31/cart | v3 cart: slide-in card window, keying groove on the back |
| cart_cap | Wood-color PLA | Top face down | 3/cart | Clip cap, same color as the cart |
| cart_strip | System color | Flat | <1 | Thin strip that presses into the cap front |

**Filament:** the wood parts are regular PLA in a wood color (ELEGOO), so print
them with normal PLA settings and the stock 0.4 mm nozzle. Turn on ironing for the
cap's plateau for a smooth top. The vertical reeds hide layer lines well.

## Hardware
- 4× M3×12 self-tapping: base → top (through the body). The base pulls up and clamps the body and marble ring between it and the top
- 2× M3×8: faceplate ears → top
- 4× M3×8: sleeve → faceplate
- Panel-mount extensions: 2× USB-A, HDMI, micro-USB, RJ45 (optional)
- 16 mm momentary button, 4× rubber feet

## Assembly
1. Reader into the sleeve rails (hot glue dab). Sleeve → faceplate (4 screws).
   **Turn both 180° when installing:** the keying rib goes to the BACK and the reader ends up on the FRONT side of the slot (it clears everything; the base has a pocket for it on that side). Old carts with the front groove only fit backwards after this.
2. Faceplate up into the top's pill opening from inside, 2 screws through the ears.
3. Eject key into its pocket from the top.
4. Pi onto the base standoffs (USB end toward the back). Lever stubs into the base cradles.
5. Panel mounts through the marble plates + body wall; button nut clamps the front plate.
6. Stack: base → body (sits on the locating ridge) → marble ring → top (its lip drops inside).
7. 4 screws up through the base into the top.

## Measure before printing the big parts
The plate cutouts use typical panel-mount sizes. Check your parts against the
parameters near the top of `huey_walnut.scad` (`usb_face`, `usb_screw`,
`hdmi_face`, `rj_face`, `pwr_face`, `btn_d`), then re-export the plates and body.
