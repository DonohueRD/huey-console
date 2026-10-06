# Huey's Station: Cart v3 (slide-in card + clip cap)

**Size:** 76 × 10 × 74 mm. The bottom 38 mm (the part that goes in the slot) is unchanged, and so are the click and the NFC tag position. The cart is 14 mm taller above the slot, so the label is never hidden.

## Print (per cart)
| STL | Material | Orientation | Notes |
|---|---|---|---|
| cart_front | Wood-color PLA | Outer face down (as exported) | Card window and slot are bridged over (~26 mm). No supports |
| cart_back | Wood-color PLA | Outer face down | Keying groove on this half |
| cart_cap | Wood-color PLA | Top face down | Snaps onto the tenon with two small bumps |
| cart_strip | System color | Flat | 70 × 2.8 × 0.8 mm. Press it into the cap groove with a dot of CA glue |

0.2 mm layers (0.12 mm for the strip if you want it crisp), 3 walls. Strip color ideas: NES red, SNES purple, Genesis black, GBA indigo, PS1 gray, Moonlight green.

## Assemble
1. Put a 25 mm NTAG215 sticker in the round pocket inside the **front** half. The reader now sits in front of the slot.
2. Put 4 magnets (5 × 2 mm) in each half. Check the polarity first so the halves attract.
3. Close the halves.
4. Slide the label card down into the window from the top.
5. Press the cap on. The cap holds the card in and holds the top of the two halves together.

## Labels
- **Card:** 64 × 26 mm. About 60 × 24 mm shows through the window.
- **Name sticker:** 59 × 5.8 mm, in the recess on top of the cap.
- `labels/make_labels.py` builds a print-ready Letter PDF at true scale:
  - Put box art in `labels/art/`.
  - Optionally list names in `labels/names.txt`.
  - Run `python make_labels.py`.
- `labels_blank.pdf` is the empty cut template.
- Print at **100% / Actual size**. Use cardstock or matte photo paper (up to about 0.5 mm thick). Print names on sticker paper.
- To swap a card: pull the cap off, push the card up through the thumb notch, and drop in the new one.

## Console change
Only the walnut base changes: its reader pocket moves to the front (`stl/base.stl`, included; you haven't printed it yet). Install the walnut faceplate and sleeve turned 180°, so the keying rib is at the back (the `slot_flip = true` setting in `huey_walnut.scad`).
