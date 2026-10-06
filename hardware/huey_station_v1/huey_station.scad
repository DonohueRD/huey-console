// =====================================================================
//  HUEY'S STATION  —  detailed model
//  Two-tone capsule console: light shell, dark band, clear glowing slot
//  bezel, SNES-style eject key, N64-style ribs, swappable color inserts.
//
//  Uses the existing carts and reader. The sleeve is reprinted (v2) only
//  to add the eject plunger holes; the cart cavity, keying rib and click
//  detent are identical to the original.
//
//  Set `part`, F6, export STL. Parts are oriented for printing.
//  Bambu P1S, all dimensions in mm.
// =====================================================================

/* [Part] */
// assembly | shell | band | base | bezel | sleeve | lever | key | badge | front_insert | rear_insert | cart_front | cart_back
part = "assembly";
eject_pressed = false;   // assembly preview: show the eject travel

/* [Body] */
W = 206;  D = 158;  H = 55;
front_r = 30;           // rounded front corners
back_r  = 20;           // flatter back
top_soft = 10;  top_p = 1.6;   // soft rolled shoulders (prints upside down, max ~58°)
bot_ch = 2;             // bottom chamfer (band prints right side up)
wall = 2.4;  top_t = 3;  base_t = 3;
band = 15;              // dark lower band height
lip = 4;                // band lip that slides up inside the shell
ledge = 7;              // band ledge the base plate clamps against

/* [Slot / bezel] */
slot_x = W/2;  slot_y = 95;
pill = [116, 44];       // visible clear bezel
flange = [130, 54];     // bezel flange under the top skin
bezel_t = 10.5;         // same stack height as the original disc
ear_x = 72;             // bezel screw ears (each side)
led_in  = [98, 30];     // LED channel inner edge (clears the sleeve flange)
led_out = [124, 50];    // LED channel outer edge (10 mm strip)
led_d   = 3;

/* [Eject] */
eject_y  = 132;         // key position (behind the slot)
pivot_y  = 116;          // closer to the key = more lift at the cart
plunger_x = 30;         // plungers at ±30 mm under the cart
arm_w = 6;  arm_t = 4;  arm_z = 5;      // lever arms: z 5..9 at rest
key_cap = [24, 11];  key_stem = 6;  key_travel = 3.5;   // cart lifts ~4.6 mm

/* [Raspberry Pi 3: long axis front-to-back, USB end at the back] */
pi_x0 = 5;  pi_y0 = 22;  standoff = 5;

/* [Front panel parts — measure yours and adjust] */
usb_face  = [15.5, 8.5];  usb_body = [18, 10.5];  usb_screw = 28;   // USB-A panel mount
usb_x = [60, 98];       // centres
btn_d = 16.3;  btn_x = 150;
/* [Rear panel parts — measure yours and adjust] */
rj_face = [17, 15];   rj_screw = 30;  rj_x = 70;     // RJ45 panel mount
hdmi_face = [21, 12]; hdmi_screw = 30; hdmi_x = 118; // HDMI panel mount
pwr_face = [12, 8];   pwr_screw = 28; pwr_x = 148;   // micro-USB / USB-C panel mount
screw_d = 3.3;

/* [Cart, reader, sleeve — unchanged from the original design] */
cart_w = 76;  cart_t = 10;  cart_h = 60;  insert_depth = 38;
cart_wall = 1.8;  clear = 0.4;  key_x = 15;  rib_w = 3;  rib_d = 1.6;
tongue_len = 12;  tongue_w = 10;  tongue_top = 8;  bump = 0.8;  bump_r = 1.2;
pcb_w = 43;  pcb_h = 41;  pcb_t = 1.6;  rail_lip = 1.2;
tag_d = 25;  mag_d = 5.2;  mag_h = 2.2;

$fn = 64;  eps = 0.01;

// ------------------------------------------------------------- derived --
ow = cart_w + 2*clear;  ot = cart_t + 2*clear;
end_w = 2.4;  side_w = 1.6;
sf_pad = 6;  sf_t = 3;  sf_pocket = 1;
sleeve_in = insert_depth - (bezel_t - sf_pocket);     // 28.5
sleeve_floor = 2;
sx = ow/2 + end_w;  sy = ot/2 + side_w;
sf_x = sx + sf_pad;  sf_y = sy + sf_pad;
sf_holes = [[ sf_x-2.8,  sy+3], [-(sf_x-2.8),  sy+3],
            [ sf_x-2.8, -(sy+3)], [-(sf_x-2.8), -(sy+3)]];
bezel_z0 = H - bezel_t;                       // bezel underside (world)
sleeve_top = bezel_z0 + sf_pocket;            // sleeve flange top (world)
cart_bottom = H - insert_depth;               // 17
floor_bot = cart_bottom - sleeve_floor;       // 15
reader_mid = sleeve_top - sf_t - pcb_h/2;
tag_z = max(reader_mid - cart_bottom, cart_wall + tag_d/2 + 0.5);
det_from_top = tongue_top + tongue_len - 2;
det_z = insert_depth - (bezel_t - sf_pocket) - det_from_top;
pivot_z = arm_z + arm_t/2;
lift_ratio = (pivot_y - slot_y) / (eject_y - pivot_y);
base_bosses = [[24, 16], [W-24, 16], [42, 151], [W-42, 151]];
fp = [W/2 - 65, band + 5, 130, 24];   // front panel x, z, w, h
rp = [W/2 - 60, band + 5, 120, 24];   // rear panel

// ================================================================ body ==
module foot2d() hull() {
    for (x = [front_r, W - front_r]) translate([x, front_r]) circle(front_r);
    for (x = [back_r, W - back_r]) translate([x, D - back_r]) circle(back_r);
}
function outer_pts() = concat(
    [[bot_ch, 0], [0, bot_ch]],
    [for (i = [0:12]) let(d = top_soft*i/12) [top_soft*pow(1 - d/top_soft, top_p), H - d]]);
function inner_pts() = concat(
    [[wall, -1], [wall, bot_ch]],
    [for (i = [0:12]) let(d = top_soft*i/12) [wall + top_soft*pow(1 - d/top_soft, top_p), H - top_t - d]]);
module slices(pts) hull() for (q = pts)
    translate([0, 0, q[1]]) linear_extrude(eps) offset(delta = -q[0]) foot2d();
module body_outer() slices(outer_pts());
module body_inner() slices(inner_pts());
module zslab(z0, z1) translate([-50, -50, z0]) cube([W + 100, D + 100, z1 - z0]);

// a rib that wraps the sides: outward bump with a 45° top so it prints
// cleanly upside down
module side_rib(z0) difference() {
    hull() {
        translate([0, 0, z0]) linear_extrude(eps) offset(delta = 1.8) foot2d();
        translate([0, 0, z0 + 1.2]) linear_extrude(eps) offset(delta = 1.8) foot2d();
        translate([0, 0, z0 + 3]) linear_extrude(eps) foot2d();
    }
    translate([0, 0, z0 - 1]) linear_extrude(5) offset(delta = -0.5) foot2d();
}
rib_z = [band + 6, band + 12, band + 18, band + 24];

module H_outline2d(s = 30) {
    t = s * 0.32;
    union() { square([t, s]); translate([s - t, 0]) square([t, s]);
              translate([0, s/2 - t/2.4]) square([s, t/1.2]); }
}
module H_stripes2d(s = 30) { t = s * 0.32;  g = s * 0.045;
    for (x = [t*0.38, s - t*0.62]) translate([x, -1]) square([g, s + 2]); }
module badge3d() difference() {           // one solid piece; logo stripes engraved 1 mm
    linear_extrude(2) H_outline2d();
    translate([0, 0, 1]) linear_extrude(2) H_stripes2d();
}
H_pos = [W/2 - 15, 22];
module pill2d(sz, grow = 0) offset(r = sz[1]/2 + grow) square([sz[0] - sz[1], eps], center = true);
module rrect2d(sz, r) offset(r = r) square([sz[0] - 2*r, sz[1] - 2*r], center = true);
function pi_holes() = [for (hx = [3.5, 52.5], hy = [3.5, 61.5]) [pi_x0 + hx, pi_y0 + hy]];

// ======================================================== light shell ===
// Upper body z = band..H. Prints upside down on its flat top.
module shell() {
    difference() {
        union() {
            intersection() {
                difference() { body_outer(); body_inner(); }
                zslab(band, H + 1);
            }
            // side ribs: sides + front corners, stopping short of the front panel
            difference() {
                intersection() {
                    for (z = rib_z) side_rib(z);
                    translate([-10, -10, 0]) cube([W + 20, D*0.66 + 10, H]);
                }
                translate([fp[0] - 5, -10, 0]) cube([fp[2] + 10, 15, H]);
            }
            intersection() {
                body_outer();
                union() {
                    // base screw bosses (ceiling down to the base plate)
                    for (p = base_bosses) translate([p[0], p[1], base_t]) cylinder(d = 9, h = H);
                    // bezel ear bosses
                    for (m = [-1, 1]) translate([slot_x + m*ear_x, slot_y, bezel_z0 + 3])
                        cylinder(d = 8, h = 10);
                    // eject key cup + guide tube
                    translate([slot_x, eject_y, H - 9 - 1.6]) linear_extrude(9 + 1.6)
                        rrect2d([key_cap[0] + 2 + 3.2, key_cap[1] + 2 + 3.2], 4.6);
                    translate([slot_x, eject_y, H - 21]) linear_extrude(12)
                        square(key_stem + 4.6, center = true);
                    // thicker wall behind the front and rear panels
                    translate([fp[0] - 3, wall - eps, band + lip + 0.5]) cube([fp[2] + 6, 2.4, fp[1] + fp[3] + 3 - band - lip - 0.5]);
                    translate([rp[0] - 3, D - wall - 2.4 + eps, band + lip + 0.5]) cube([rp[2] + 6, 2.4, rp[1] + rp[3] + 3 - band - lip - 0.5]);
                }
            }
        }
        // pilot holes
        for (p = base_bosses) translate([p[0], p[1], -1]) cylinder(d = 2.6, h = base_t + 14);
        for (m = [-1, 1]) translate([slot_x + m*ear_x, slot_y, bezel_z0])
            cylinder(d = 2.6, h = 9);
        // clear bezel opening
        translate([slot_x, slot_y, H - top_t - 1]) linear_extrude(top_t + 2) pill2d(pill, 0.25);
        // badge pocket
        translate([H_pos[0], H_pos[1], H - 1]) linear_extrude(2) offset(0.2) H_outline2d();
        // eject key pocket + square stem guide
        translate([slot_x, eject_y, H - 9]) linear_extrude(10) rrect2d([key_cap[0] + 2, key_cap[1] + 2], 3);
        translate([slot_x, eject_y, H - 30]) linear_extrude(30) square(key_stem + 0.6, center = true);
        // N64-style ribs beside the slot: grooves cut into the flat top (print-friendly)
        for (m = [-1, 1]) for (i = [0:3])
            translate([slot_x + m*(pill[0]/2 + 9 + i*6.5), slot_y, H - 1.4])
                linear_extrude(2) offset(r = 0.8) square([1.2, 52], center = true);
        // front panel: recess for the insert + openings behind it
        translate([fp[0], -1, fp[1]]) cube([fp[2], 1 + 2.4, fp[3]]);
        front_openings(true);
        // rear panel
        translate([rp[0], D - 2.4, rp[1]]) cube([rp[2], 3, rp[3]]);
        rear_openings(true);
        // vents hidden between the side ribs (left side over the Pi, right side)
        for (zi = [0:2]) {
            z = rib_z[zi] + 3.4;
            translate([-1, 40, z]) cube([wall + 4, 60, 2.2]);
            translate([W - wall - 3, 40, z]) cube([wall + 4, 60, 2.2]);
        }
    }
}

module front_openings(through) {
    yy = through ? -1 : -0.5;
    len = through ? 2.4 + 2.4 + 2 : 4;
    cz = fp[1] + fp[3]/2;
    for (x = usb_x) {
        translate([x - (through ? usb_body[0] : usb_face[0])/2, yy, cz - (through ? usb_body[1] : usb_face[1])/2])
            cube([through ? usb_body[0] : usb_face[0], len, through ? usb_body[1] : usb_face[1]]);
        for (m = [-1, 1]) translate([x + m*usb_screw/2, yy, cz]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = len);
    }
    translate([btn_x, yy, cz]) rotate([-90, 0, 0]) cylinder(d = btn_d, h = len);
}
module rear_openings(through) {
    len = through ? 2.4 + 2.4 + 2 : 4;
    y0 = through ? D - len + 1 : D - 3.5;
    cz = rp[1] + rp[3]/2;
    for (c = [[rj_x, rj_face, rj_screw], [hdmi_x, hdmi_face, hdmi_screw], [pwr_x, pwr_face, pwr_screw]]) {
        translate([c[0] - c[1][0]/2 - (through ? 1 : 0), y0, cz - c[1][1]/2 - (through ? 1 : 0)])
            cube([c[1][0] + (through ? 2 : 0), len, c[1][1] + (through ? 2 : 0)]);
        for (m = [-1, 1]) translate([c[0] + m*c[2]/2, y0, cz]) rotate([-90, 0, 0]) cylinder(d = screw_d, h = len);
    }
}

// ========================================================== dark band ===
// Lower ring z = 0..band with a lip into the shell and a ledge the base
// plate pulls up against. Prints right side up.
module band_part() {
    difference() {
        union() {
            intersection() { body_outer(); zslab(0, band); }
            // lip that slides up inside the shell, joined to the band wall
            translate([0, 0, band - 3]) linear_extrude(3 + lip)
                difference() { offset(delta = -wall - 0.25) foot2d(); offset(delta = -wall - 2.4) foot2d(); }
            translate([0, 0, band - 3]) linear_extrude(3)
                difference() { offset(delta = -1) foot2d(); offset(delta = -wall - 2.4) foot2d(); }
            // ledge the base plate pulls up against
            translate([0, 0, base_t]) linear_extrude(2) difference() {
                offset(delta = -1) foot2d(); offset(delta = -ledge - wall) foot2d();
            }
        }
        // hollow inside; the bottom edge keeps a 1.2 mm wall under the chamfer
        translate([0, 0, bot_ch + 1.2]) linear_extrude(band) offset(delta = -wall - 2.4 - eps) foot2d();
        translate([0, 0, -1]) linear_extrude(bot_ch + 2.2 + eps) offset(delta = -bot_ch - 1.2) foot2d();
        translate([0, 0, bot_ch + 1.2 - eps]) linear_extrude(base_t + 2 - bot_ch - 1.2 + 2*eps)
            offset(delta = -ledge - wall) foot2d();
        translate([0, 0, 5]) linear_extrude(band - 3 - 5 + eps) offset(delta = -wall) foot2d();
        for (p = base_bosses) translate([p[0], p[1], -1]) cylinder(d = 10, h = band + lip + 2);
        for (p = pi_holes()) translate([p[0], p[1], -1]) cylinder(d = 7.5, h = band + 2);   // Pi standoffs
    }
}

// ========================================================== base plate ==
module base() difference() {
    union() {
        linear_extrude(base_t) offset(delta = -bot_ch - 1.2 - 0.3) foot2d();
        for (p = pi_holes()) translate([p[0], p[1], 0]) cylinder(d = 6, h = base_t + standoff);
        // eject lever: pivot cradles, front stops, return spring
        for (m = [-1, 1]) translate([slot_x + m*(plunger_x + arm_w/2 + 4.5) - 3, pivot_y - 4, 0])
            difference() {
                cube([6, 8, pivot_z + 3]);
                translate([-1, 4, pivot_z]) rotate([0, 90, 0]) cylinder(d = 4.4, h = 8);
                translate([-1, 4 - 2.2, pivot_z]) cube([8, 4.4, 10]);
            }
        for (m = [-1, 1]) translate([slot_x + m*plunger_x - 3, slot_y - 4, 0]) cube([6, 4, arm_z]);
        // printed leaf spring: pushes the lever's back bar up (key up, plungers down)
        translate([slot_x - 15, eject_y + 7, 0]) cube([30, 4, base_t + 2]);
        translate([slot_x - 12, 0, 0]) hull() {
            translate([0, eject_y + 7, base_t + 0.8]) cube([24, 1, 1.2]);
            translate([0, eject_y - 1, arm_z - 1.2]) cube([24, 1, 1.2]);
        }
    }
    for (p = pi_holes()) translate([p[0], p[1], 1]) cylinder(d = 2.2, h = base_t + standoff);
    for (p = base_bosses) translate([p[0], p[1], 0]) {
        translate([0, 0, -1]) cylinder(d = 3.4, h = base_t + 2);
        translate([0, 0, -eps]) cylinder(d1 = 6.6, d2 = 3.4, h = 1.6);
    }
    // pocket under the lever's back bar so the key has full travel
    translate([slot_x - plunger_x - arm_w/2 - 2, eject_y - 6, 1]) cube([2*plunger_x + arm_w + 4, 12, base_t]);
    // pocket so the bottom of the reader board clears the plate
    translate([slot_x - pcb_w/2 - 6, slot_y + sy - 1, 1]) cube([pcb_w + 12, pcb_t + 10, base_t]);
    // vents under the Pi
    for (i = [0:6]) translate([pi_x0 + 9 + i*6, pi_y0 + 14, -1]) cube([3, 56, base_t + 2]);
    // rubber feet
    for (p = [[30, 22], [W - 30, 22], [26, D - 22], [W - 26, D - 22]])
        translate([p[0], p[1], -eps]) cylinder(d = 10.5, h = 1);
}

// ================================================== clear slot bezel ===
// Print in clear filament, flange side down. LED strip sits in the
// channel underneath, LEDs facing up, so the whole bezel glows.
module bezel() difference() {
    union() {
        linear_extrude(bezel_t - top_t) rrect2d(flange, 8);
        linear_extrude(bezel_t) pill2d(pill);
        for (m = [-1, 1]) translate([m*ear_x, 0, 0]) linear_extrude(3)
            hull() { circle(d = 11); translate([-m*8, 0]) square([1, 11], center = true); }
    }
    // cart opening with entry chamfer, keeping the keying rib
    difference() {
        union() {
            translate([-ow/2, -ot/2, -1]) cube([ow, ot, bezel_t + 2]);
            hull() {
                translate([-ow/2, -ot/2, bezel_t - 1.2]) cube([ow, ot, eps]);
                translate([-ow/2 - 1.2, -ot/2 - 1.2, bezel_t]) cube([ow + 2.4, ot + 2.4, eps]);
            }
        }
        rib();
    }
    // sleeve flange pocket + pilots
    translate([-sf_x - 0.2, -sf_y - 0.2, -eps]) cube([2*sf_x + 0.4, 2*sf_y + 0.4, sf_pocket]);
    for (p = sf_holes) translate([p[0], p[1], -1]) cylinder(d = 2.6, h = 9);
    // LED channel + wire exit toward the left ear
    translate([0, 0, -eps]) linear_extrude(led_d) difference() { rrect2d(led_out, 6); rrect2d(led_in, 3); }
    translate([-flange[0]/2 - 1, -3, -eps]) cube([flange[0]/2 - led_out[0]/2 + 2, 6, led_d]);
    // ear screw holes
    for (m = [-1, 1]) translate([m*ear_x, 0, -1]) cylinder(d = 3.4, h = 5);
}

module rib(len = 200) translate([key_x - rib_w/2, -ot/2 - 1, -len/2]) cube([rib_w, rib_d + 1, len]);

// ========================================================== sleeve v2 ===
// Original sleeve + two plunger holes in the floor for the eject lever.
module sleeve() {
    total = sleeve_in + sleeve_floor;
    difference() {
        union() {
            translate([-sf_x, -sf_y, -sf_t]) cube([2*sf_x, 2*sf_y, sf_t]);
            translate([-sx, -sy, -total]) cube([2*sx, 2*sy, total]);
            for (m = [0, 1]) mirror([m, 0, 0])
                translate([pcb_w/2 + 0.3 - rail_lip, sy, -total]) difference() {
                    cube([rail_lip + 3, pcb_t + 0.4 + 1.2, total]);
                    translate([-eps, -eps, -1]) cube([rail_lip + eps, pcb_t + 0.4 + eps, total + 2]);
                }
        }
        difference() { translate([-ow/2, -ot/2, -sleeve_in]) cube([ow, ot, sleeve_in + 10]); rib(); }
        for (m = [0, 1]) mirror([m, 0, 0]) tongue_cut();
        for (p = sf_holes) translate([p[0], p[1], -sf_t - 1]) cylinder(d = 3.4, h = sf_t + 2);
        // plunger slots (the plungers swing slightly as the lever tips)
        for (m = [-1, 1]) translate([m*plunger_x, 0, -total - 3]) linear_extrude(10)
            hull() for (yy = [-2.4, 2.4]) translate([0, yy]) circle(d = 5.4);
    }
    for (m = [0, 1]) mirror([m, 0, 0]) translate([ow/2 + eps, 0, -det_from_top]) intersection() {
        rotate([90, 0, 0]) cylinder(r = bump_r, h = tongue_w - 1, center = true);
        translate([-bump, -tongue_w, -3]) cube([bump, 2*tongue_w, 6]);
    }
}
module tongue_cut() {
    gap = 1;  z_top = -tongue_top;
    translate([ow/2 - 1, 0, 0]) difference() {
        translate([0, -tongue_w/2 - gap, z_top - tongue_len - gap]) cube([end_w + 2, tongue_w + 2*gap, tongue_len + gap]);
        translate([-1, -tongue_w/2, z_top - tongue_len]) cube([end_w + 4, tongue_w, tongue_len + 1]);
    }
}

// ======================================================= eject lever ===
// U-shaped seesaw. Key presses the back bar down; the front of each arm
// rises and pushes a plunger up through the sleeve floor, popping the cart.
// Modeled in world coordinates at rest.
module lever() {
    tip = cart_bottom - 0.5;          // plunger tip sits just below the floor at rest
    for (m = [-1, 1]) {
        translate([slot_x + m*plunger_x - arm_w/2, slot_y - 3, arm_z]) cube([arm_w, eject_y + 4 - slot_y + 3, arm_t]);
        translate([slot_x + m*plunger_x, slot_y, arm_z + arm_t - eps]) cylinder(d = 4.6, h = tip - arm_z - arm_t);
        // pivot stubs
        translate([slot_x + m*(plunger_x + arm_w/2) - (m < 0 ? 5 : 0), pivot_y, pivot_z])
            rotate([0, 90, 0]) cylinder(d = 3.9, h = 5);
    }
    translate([slot_x - plunger_x - arm_w/2, eject_y - 4, arm_z]) cube([2*plunger_x + arm_w, 8, arm_t]);
}

// ========================================================== eject key ===
module eject_key() {
    stem_len = (H - 4.5) - (arm_z + arm_t);
    translate([0, 0, stem_len]) linear_extrude(5) rrect2d(key_cap, 2.5);
    translate([-key_stem/2, -key_stem/2, 0]) cube([key_stem, key_stem, stem_len + eps]);
}

// ===================================================== color inserts ===
module front_insert() difference() {
    translate([fp[0] + 0.2, 0, fp[1] + 0.2]) cube([fp[2] - 0.4, 2.4, fp[3] - 0.4]);
    front_openings(false);
}
module rear_insert() difference() {
    translate([rp[0] + 0.2, D - 2.4, rp[1] + 0.2]) cube([rp[2] - 0.4, 2.4, rp[3] - 0.4]);
    rear_openings(false);
}

// =========================================================== cartridge ==
module cart_profile(inset = 0) {
    r_top = 6 - inset;  r_bot = 1.5;  w = cart_w - 2*inset;  h = cart_h - 2*inset;
    translate([-w/2, inset]) hull() {
        translate([r_bot, r_bot]) circle(r_bot);  translate([w - r_bot, r_bot]) circle(r_bot);
        translate([r_top, h - r_top]) circle(r_top);  translate([w - r_top, h - r_top]) circle(r_top);
    }
}
module cart_solid(inset = 0, t = cart_t) rotate([90, 0, 0]) linear_extrude(t, center = true) cart_profile(inset);
mag_posts = [[cart_w/2 - 6, 6], [-(cart_w/2 - 6), 6], [cart_w/2 - 6.5, cart_h - 10], [-(cart_w/2 - 6.5), cart_h - 10]];
module cart_half(front = true) {
    s = front ? -1 : 1;
    difference() {
        intersection() {
            union() {
                difference() { cart_solid(); cart_solid(cart_wall, cart_t - 2*cart_wall); }
                for (p = mag_posts) translate([p[0], 0, p[1]]) rotate([90, 0, 0]) cylinder(d = mag_d + 3, h = cart_t, center = true);
                if (front) translate([key_x - 4.5, -cart_t/2, 0]) cube([9, cart_wall + 2.6, insert_depth + 3]);
            }
            cart_solid();
            translate([-cart_w, front ? -cart_t : 0, -1]) cube([2*cart_w, cart_t, cart_h + 2]);
        }
        for (p = mag_posts) translate([p[0], s*(mag_h/2 - eps), p[1]]) rotate([90, 0, 0]) cylinder(d = mag_d, h = mag_h, center = true);
        for (m = [-1, 1]) translate([m*(cart_w/2 + clear), 0, det_z]) rotate([90, 0, 0]) cylinder(r = bump_r + 0.2, h = cart_t + 2, center = true);
        for (m = [-1, 1], i = [0:3]) translate([m*cart_w/2, 0, insert_depth + 4 + i*3.5]) cube([1.6, cart_t + 2, 1.6], center = true);
        if (front) {
            translate([key_x - rib_w/2 - 0.4, -cart_t/2 - 1, -1]) cube([rib_w + 0.8, rib_d + 0.6 + 1, insert_depth + 3]);
            translate([-(cart_w/2 - 11), -cart_t/2 - 1, insert_depth + 3]) cube([cart_w - 22, 1 + 0.6, cart_h - insert_depth - 8]);
        } else {
            translate([0, cart_t/2 - cart_wall - 1 + 0.6, tag_z]) rotate([-90, 0, 0]) cylinder(d = tag_d + 0.6, h = 1);
        }
    }
}

// ===================================================== stand-ins (fit) ==
module pi_standin() {
    z = base_t + standoff;
    translate([pi_x0, pi_y0, z]) cube([56, 85, 1.6]);                       // PCB
    translate([pi_x0 + 1, pi_y0 + 85 - 21, z + 1.6]) cube([54, 24, 16]);    // USB + Ethernet stack
    translate([pi_x0 + 3, pi_y0 + 85 + 3, z]) cube([49, 36, 16]);           // USB/Eth plugs + cable bend
    for (yy = [10.6, 32]) translate([pi_x0 + 56, pi_y0 + yy - 10, z]) cube([36, 20, 12]); // power + HDMI plugs
    translate([pi_x0, pi_y0 + 5, z + 1.6]) cube([7, 52, 26]);               // GPIO header + jumper wires
}
module reader_standin() translate([slot_x - pcb_w/2, slot_y + sy + 0.05, sleeve_top - sf_t - pcb_h]) cube([pcb_w, pcb_t + 3, pcb_h]);
module panel_standins() {
    cz = fp[1] + fp[3]/2;
    for (x = usb_x) translate([x - 8, 4.8, cz - 5]) cube([16, 22, 10]);       // USB panel mount bodies
    translate([btn_x, 4.8, cz]) rotate([-90, 0, 0]) cylinder(d = 15, h = 26); // button body
    cr = rp[1] + rp[3]/2;
    for (x = [rj_x, hdmi_x, pwr_x]) translate([x - 9, D - 4.8 - 24, cr - 7]) cube([18, 24, 14]);
}

// ============================================================ assembly ==
module place_bezel()  translate([slot_x, slot_y, bezel_z0]) children();
module place_sleeve() translate([slot_x, slot_y, sleeve_top]) children();
module place_lever()  if (eject_pressed)
        translate([0, pivot_y, pivot_z]) rotate([-atan(key_travel / (eject_y - pivot_y)), 0, 0])
            translate([0, -pivot_y, -pivot_z]) children();
    else children();

module assembly() {
    color("#cfccc4") shell();
    color("#3b3b41") band_part();
    color("#3b3b41") base();
    color([0.85, 0.9, 1.0, 0.55]) place_bezel() bezel();
    color("#55555c") place_sleeve() sleeve();
    color("#b52025") place_lever() lever();
    color("#b52025") translate([slot_x, eject_y, arm_z + arm_t - (eject_pressed ? key_travel : 0)]) eject_key();
    color("#b52025") translate([H_pos[0], H_pos[1], H - 1]) badge3d();
    color("#b52025") front_insert();
    color("#b52025") rear_insert();
    color("#3a3a3f") translate([slot_x, slot_y, cart_bottom]) { cart_half(true); cart_half(false); }
}

if (part == "assembly") assembly();
if (part == "shell")  translate([0, 0, H]) rotate([180, 0, 0]) shell();
if (part == "band")   band_part();
if (part == "base")   base();
if (part == "bezel")  bezel();
if (part == "sleeve") rotate([180, 0, 0]) sleeve();
if (part == "lever")  translate([0, 0, -arm_z]) lever();
if (part == "key")    translate([0, 0, (H - 4.5) - (arm_z + arm_t) + 5]) rotate([180, 0, 0]) eject_key();
if (part == "badge")  badge3d();
if (part == "front_insert") rotate([90, 0, 0]) front_insert();
if (part == "rear_insert")  translate([0, 0, -(D - 2.4)]) rotate([90, 0, 0]) rear_insert();
if (part == "cart_front") translate([0, 0, cart_t/2]) rotate([90, 0, 0])  cart_half(true);
if (part == "cart_back")  translate([0, 0, cart_t/2]) rotate([-90, 0, 0]) cart_half(false);
