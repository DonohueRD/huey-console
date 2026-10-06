"""
HUEY splash - PS1 / Crash-era look.

A tiny software 3D renderer that mimics the PlayStation GPU:
  * low-poly beveled 3D letters + segmented ring
  * Gouraud (per-vertex) lighting + baked vertical vertex-color gradient
  * vertex positions snapped to whole pixels (the classic PS1 polygon jitter)
  * affine (non perspective-correct) color interpolation
  * native 320x240, no anti-aliasing, nearest-neighbour 2x upscale
  * 15-bit color with the PS1 4x4 ordered dither matrix
  * optional semi-transparent blob shadows
Output: transparent intro + seamless loop (PNG frames + APNG).
"""
import math, os, zipfile
import numpy as np
from PIL import Image

# ---------------- settings ----------------
RW, RH = 320, 240          # native render res
UPSCALE = 2                # final 640x480
FPS = 30
OUT = "huey_splash_ps1"
FONT_FILE = "fonts_luckiest-guy.woff"   # None = built-in blocky letters; or a .ttf/.otf/.woff path
THIN = 0.06             # stroke thinning (0 = font as designed)
CONDENSE = 0.94         # horizontal squeeze of each letter
CURVE_STEPS = 3         # segments per font curve (low = more low-poly)
U_STRETCH = 1.2         # the U stands taller than the other letters
CAM = "path"            # "path" = high 3/4 -> 3/4 -> classic pan, or a preset name from CAMERAS

ORANGE, RED, YELLOW, BLUE, TEAL = (255, 112, 22), (232, 30, 40), (255, 200, 22), (36, 92, 236), (20, 172, 150)

LOOP = 120              # loading-screen loop length (ring spin, wobble and bob all repeat every LOOP frames)
DEPTH, BEVEL, BEVEL_Z = 0.62, 0.11, 0.11

# ---------------- letterforms (2D, origin bottom-centre, height ~2) ----------------
def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

_FONT_CACHE = {}
def font_glyph(ch):
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    if FONT_FILE not in _FONT_CACHE:
        _FONT_CACHE[FONT_FILE] = TTFont(FONT_FILE)
    ft = _FONT_CACHE[FONT_FILE]
    gs, cmap = ft.getGlyphSet(), ft.getBestCmap()
    class Flat(BasePen):
        def __init__(s): super().__init__(gs); s.contours, s.cur = [], []
        def _moveTo(s, p): s.cur = [p]
        def _lineTo(s, p): s.cur.append(p)
        def _curveToOne(s, a, b, c):
            p0 = s.cur[-1]
            for i in range(1, CURVE_STEPS + 1):
                t = i / CURVE_STEPS; u = 1 - t
                s.cur.append(tuple(u**3*p0[k] + 3*u*u*t*a[k] + 3*u*t*t*b[k] + t**3*c[k] for k in (0, 1)))
        def _qCurveToOne(s, a, b):
            p0 = s.cur[-1]
            for i in range(1, CURVE_STEPS + 1):
                t = i / CURVE_STEPS; u = 1 - t
                s.cur.append(tuple(u*u*p0[k] + 2*u*t*a[k] + t*t*b[k] for k in (0, 1)))
        def _closePath(s):
            if len(s.cur) > 2: s.contours.append(s.cur)
            s.cur = []
        _endPath = _closePath
    def contours(c):
        pen = Flat(); gs[cmap[ord(c)]].draw(pen); return pen.contours
    hy = [p[1] for cc in contours("H") for p in cc]
    k = 2.0 / (max(hy) - min(hy)); base = min(hy)
    cs = contours(ch)
    if len(cs) > 1:
        print(f"  note: {ch} has {len(cs)} contours in {os.path.basename(FONT_FILE)}; using the outer one")
    c = max(cs, key=lambda q: abs(area(q)))
    pts = [((x) * k, (y - base) * k) for x, y in c]
    # clean: drop duplicates / near-collinear points
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.02: out.append(p)
    if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.02: out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, cc = out[i - 1], out[i], out[(i + 1) % len(out)]
            cr = (b[0]-a[0])*(cc[1]-a[1]) - (b[1]-a[1])*(cc[0]-a[0])
            if abs(cr) < 1e-3: out.pop(i); changed = True; break
    if THIN > 0 or CONDENSE != 1:
        from shapely.geometry import Polygon
        poly = Polygon(out).buffer(0)
        if THIN > 0:
            poly = poly.buffer(-THIN, join_style=2, mitre_limit=3)
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        fac = 1 / (1 - THIN)   # restore cap height so only the strokes get thinner
        out = [(x * fac * CONDENSE, (y - THIN) * fac) for x, y in list(poly.exterior.coords)[:-1]]
    out = simplify_closed(out, 0.03)
    # merge very short edges (tiny corner rounds) into a single vertex
    merged = True
    while merged and len(out) > 4:
        merged = False
        for i in range(len(out)):
            a, b = out[i], out[(i + 1) % len(out)]
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 0.07:
                out[i] = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); out.pop((i + 1) % len(out)); merged = True; break
    xs = [p[0] for p in out]; cx = (min(xs) + max(xs)) / 2
    sy = U_STRETCH if ch == "U" else 1.0
    return [(x - cx, y * sy) for x, y in out]

def simplify_closed(pts, tol):
    """Douglas-Peucker on a closed ring (split at the two farthest-apart points)."""
    def rdp(seg):
        if len(seg) < 3: return seg
        a, b = np.array(seg[0]), np.array(seg[-1]); ab = b - a; L = np.linalg.norm(ab) + 1e-12
        d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in seg[1:-1]]
        i = int(np.argmax(d)) + 1
        if d[i - 1] > tol: return rdp(seg[:i + 1])[:-1] + rdp(seg[i:])
        return [seg[0], seg[-1]]
    P = np.array(pts); i0 = 0
    i1 = int(np.argmax(np.linalg.norm(P - P[0], axis=1)))
    ring = pts + pts
    a = rdp(ring[i0:i1 + 1]); b = rdp(ring[i1:len(pts) + 1])
    return a[:-1] + b[:-1]

def glyph(ch):
    if FONT_FILE: return font_glyph(ch)
    if ch == "H":
        return [(-.75, 0), (-.23, 0), (-.23, .76), (.23, .76), (.23, 0), (.75, 0), (.75, 2),
                (.23, 2), (.23, 1.22), (-.23, 1.22), (-.23, 2), (-.75, 2)]
    if ch == "U":
        top = 2.4
        outer = arc(0, .78, .76, 180, 360, 6)
        inner = arc(0, .78, .24, 360, 180, 3)
        return [(-.76, top)] + outer + [(.76, top), (.24, top)] + inner + [(-.24, top)]
    if ch == "E":
        return [(-.66, 0), (.68, 0), (.68, .46), (-.14, .46), (-.14, .8), (.46, .8), (.46, 1.22),
                (-.14, 1.22), (-.14, 1.54), (.68, 1.54), (.68, 2), (-.66, 2)]
    if ch == "Y":
        return [(-.26, 0), (.26, 0), (.26, .92), (.88, 2), (.3, 2), (0, 1.42), (-.3, 2), (-.88, 2), (-.26, .92)]

def area(p): return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
def ccw(p): return p if area(p) > 0 else p[::-1]

def triangulate(P):
    try:
        import mapbox_earcut as ec
        idx = ec.triangulate_float64(np.array(P, float), np.array([len(P)], dtype=np.uint32))
        tris = [tuple(int(v) for v in idx[i:i + 3]) for i in range(0, len(idx), 3)]
        if tris: return tris
    except ImportError:
        pass
    return triangulate_simple(P)

def triangulate_simple(P):
    P = [np.array(v, float) for v in P]
    idx, tris = list(range(len(P))), []
    def cr(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            if cr(P[a], P[b], P[c]) <= 1e-9: continue
            if any(cr(P[a], P[b], P[q]) >= 0 and cr(P[b], P[c], P[q]) >= 0 and cr(P[c], P[a], P[q]) >= 0
                   for q in idx if q not in (a, b, c)): continue
            tris.append((a, b, c)); idx.pop(k); break
        else:
            break
    if len(idx) == 3: tris.append(tuple(idx))
    return tris

def inset(P, b):
    n = len(P); out = []
    for i in range(n):
        p0, p1, p2 = np.array(P[i - 1]), np.array(P[i]), np.array(P[(i + 1) % n])
        e1, e2 = p1 - p0, p2 - p1
        n1 = np.array([-e1[1], e1[0]]) / np.linalg.norm(e1)
        n2 = np.array([-e2[1], e2[0]]) / np.linalg.norm(e2)
        m = (n1 + n2) / max(0.25, 1 + n1 @ n2)
        out.append(tuple(p1 + b * m))
    return out

# ---------------- mesh ----------------
class Mesh:
    def __init__(self): self.tri, self.ref, self.col = [], [], []
    def add(self, a, b, c, ref, col):
        self.tri.append([a, b, c]); self.ref.append(ref); self.col.append(col)
    def quad(self, a, b, c, d, ref, col):
        self.add(a, b, c, ref, col); self.add(a, c, d, ref, col)
    def arrays(self):
        T = np.array(self.tri, float)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        ref = np.array(self.ref, float)
        n *= np.sign((n * ref).sum(1, keepdims=True) + 1e-9)
        return T, n, np.array(self.col, float)

def letter_mesh(ch, color):
    P = ccw(glyph(ch))
    bev = BEVEL
    try:
        from shapely.geometry import Polygon
        while bev > 0.02 and not Polygon(inset(P, bev)).is_valid: bev *= 0.75
    except ImportError:
        pass
    I = inset(P, bev)
    zf, zb, zs = DEPTH / 2, -DEPTH / 2, DEPTH / 2 - BEVEL_Z
    m = Mesh()
    for a, b, c in triangulate(P):
        m.add((*P[a], zb), (*P[b], zb), (*P[c], zb), (0, 0, -1), color)
    for a, b, c in triangulate(I):
        m.add((*I[a], zf), (*I[b], zf), (*I[c], zf), (0, 0, 1), color)
    n = len(P)
    for i in range(n):
        j = (i + 1) % n
        dx, dy = P[j][0] - P[i][0], P[j][1] - P[i][1]
        out = (dy, -dx, 0)
        m.quad((*P[i], zb), (*P[j], zb), (*P[j], zs), (*P[i], zs), out, color)
        m.quad((*P[i], zs), (*P[j], zs), (*I[j], zf), (*I[i], zf), (dy, -dx, math.hypot(dx, dy)), color)
    return m.arrays()

def ring_color(theta_deg):
    a = theta_deg % 360
    if a < 50 or a >= 310: return TEAL
    if a < 150: return BLUE
    if a < 210: return RED
    return YELLOW

def ring_mesh(N=48, Ro=5.5, Ri=4.55, h=0.46, b=0.1, spin=0.0):
    prof = [(Ro, 0), (Ro, h - b), (Ro - b, h), (Ri + b, h), (Ri, h - b), (Ri, 0)]
    refs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
    m = Mesh()
    for k in range(N):
        t0, t1 = 2 * math.pi * k / N, 2 * math.pi * (k + 1) / N
        col = ring_color(math.degrees((t0 + t1) / 2) - spin)
        def P(r, y, t): return (r * math.sin(t), y, r * math.cos(t))
        tm = (t0 + t1) / 2
        for e in range(len(prof) - 1):
            (r0, y0), (r1, y1) = prof[e], prof[e + 1]
            rr, ry = refs[e]
            ref = (rr * math.sin(tm), ry, rr * math.cos(tm))
            m.quad(P(r0, y0, t0), P(r0, y0, t1), P(r1, y1, t1), P(r1, y1, t0), ref, col)
    return m.arrays()

def disc_mesh(r=1.0, n=10):
    m = Mesh()
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        m.add((0, 0, 0), (r * math.sin(t0), 0, r * math.cos(t0)), (r * math.sin(t1), 0, r * math.cos(t1)), (0, 1, 0), (0, 0, 0))
    return m.arrays()

# ---------------- math ----------------
def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def look_at(eye, target):
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.array([r, u, -f]), eye

def ease_out_back(t, s=1.7): t -= 1; return t * t * ((s + 1) * t + s) + 1
def ease_out_cubic(t): return 1 - (1 - t) ** 3
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

# ---------------- renderer ----------------
DITHER = np.array([[-4, 0, -3, 1], [2, -2, 3, -1], [-3, 1, -4, 0], [3, -1, 2, -2]], float)

class Frame:
    def __init__(self):
        self.rgb = np.zeros((RH, RW, 3), float)
        self.z = np.full((RH, RW), np.inf)
        self.a = np.zeros((RH, RW), np.uint8)

def project(V, cam, fov):
    R, eye = cam
    v = np.round((V - eye) @ R.T, 6)
    zc = -v[..., 2]
    f = 1 / math.tan(math.radians(fov) / 2)
    x = (v[..., 0] * f / (RW / RH)) / zc
    y = (v[..., 1] * f) / zc
    sx = np.floor((x + 1) * RW / 2 + 1e-6)     # integer snap = PS1 jitter
    sy = np.floor((1 - y) * RH / 2 + 1e-6)
    return sx, sy, zc

def raster(fr, sx, sy, zc, cols, shadow=False, shadow_alpha=110):
    for t in range(len(sx)):
        x, y, z = sx[t], sy[t], zc[t]; c = None if cols is None else cols[t]
        if np.any(z <= 0.1): continue
        x0, x1 = int(max(0, x.min())), int(min(RW - 1, x.max()))
        y0, y1 = int(max(0, y.min())), int(min(RH - 1, y.max()))
        if x0 > x1 or y0 > y1: continue
        d = (x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])
        if abs(d) < 1e-9: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((x[1] - X) * (y[2] - Y) - (x[2] - X) * (y[1] - Y)) / d
        w1 = ((x[2] - X) * (y[0] - Y) - (x[0] - X) * (y[2] - Y)) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any(): continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        zb = fr.z[y0:y1 + 1, x0:x1 + 1]
        m = inside & (zz < zb)
        if shadow:
            ab = fr.a[y0:y1 + 1, x0:x1 + 1]
            ab[m & (ab == 0)] = shadow_alpha
            continue
        zb[m] = zz[m]
        cc = w0[..., None] * c[0] + w1[..., None] * c[1] + w2[..., None] * c[2]   # affine Gouraud
        fr.rgb[y0:y1 + 1, x0:x1 + 1][m] = cc[m]
        fr.a[y0:y1 + 1, x0:x1 + 1][m] = 255

KEY = np.array([-0.45, 0.75, 0.55]); KEY /= np.linalg.norm(KEY)

def shade(Tw, Nw, base, cam_eye, sweep_x=None, ymax=2.4):
    """Per-vertex lighting (flat normals, so faces stay crisp) + baked vertical gradient."""
    n = Nw[:, None, :]
    diff = np.clip((n * KEY).sum(-1), 0, 1)
    fill = np.clip((n * np.array([0.6, 0.2, 0.7])).sum(-1), 0, 1) * 0.25
    grad = 0.78 + 0.32 * np.clip(Tw[..., 1] / ymax, 0, 1)      # brighter toward the top
    lit = (0.34 + 0.72 * diff + fill) * grad
    col = base[:, None, :] * lit[..., None]
    # specular (Blinn) - plus a light sweep near the end
    V = cam_eye - Tw; V /= np.linalg.norm(V, axis=-1, keepdims=True)
    lights = [(KEY, 0.30, 18)]
    if sweep_x is not None:
        Ls = np.array([sweep_x, 2.5, 5.0])[None, None, :] - Tw
        Ls /= np.linalg.norm(Ls, axis=-1, keepdims=True)
        lights.append((Ls, 0.9, 30))
    for L, k, p in lights:
        Hh = L + V; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True)
        s = np.clip((n * Hh).sum(-1), 0, 1) ** p * k
        col += 255 * s[..., None]
    return col

def transform(T, N, scale, yaw, pos):
    R = rot_y(math.radians(yaw))
    S = np.array(scale, float)
    Tw = (T * S) @ R.T + pos
    Nw = (N / S) @ R.T
    Nw /= np.linalg.norm(Nw, axis=1, keepdims=True)
    return Tw, Nw

def finalize(fr):
    yy, xx = np.mgrid[0:RH, 0:RW]
    d = DITHER[yy % 4, xx % 4][..., None]
    c = np.clip(fr.rgb + d, 0, 255).astype(np.uint8) & 0xF8   # 15-bit color
    c = c | (c >> 5)
    img = np.dstack([c, fr.a])
    img[fr.a == 0, :3] = 0
    im = Image.fromarray(img, "RGBA")
    return im.resize((RW * UPSCALE, RH * UPSCALE), Image.NEAREST)

# ---------------- scene / animation ----------------
LS = 1.24          # letter scale (auto-reduced if a font is too wide)
MAX_SPAN = 7.4     # max total word width (keeps it clear of the ring)
GAP = 0.36
SHADOWS = False    # floating in space -> no floor shadows
# per-letter colour, z offset (gentle arc), resting yaw, bob phase
LETTER_STYLE = [("H", ORANGE, -0.3, 10, 0.0), ("U", RED, 0.15, 3, 1.6),
                ("E", YELLOW, 0.15, -3, 3.1), ("Y", BLUE, -0.3, -10, 4.5)]

# timeline (frames @30fps)
DROP_START = {"H": 16, "E": 24, "Y": 32, "U": 46}   # U drops last
FALL = 13
U_FALL = 16
CAM_END = 104
SWEEP_START, SWEEP_LEN = 98, 20
LOOP_START = 126            # intro = frames [0, LOOP_START), loop = [LOOP_START, LOOP_START + LOOP)

# ring placement
OVAL = 0.70                 # z squash -> oval
RING_Y = -0.3               # lowered from 0.6 so the ring doesn't cover the letters
RING_OFFSET = (0.22, 0.0, 0.0)
RING_SPIN = 360 / LOOP      # deg/frame colour flow around the ring
RING_TILT = 7.0             # wobble tilt (deg)
RING_YAW = 10.0             # yaw sway (deg)
RING_DRIFT = (0.40, 0.12, 0.25)

CAMERAS = {  # name: (eye, target, fov)
    "high-three-quarter": ((-8.4, 10.8, 10.4), (0.0, 0.6, 0.0), 42),
    "three-quarter":      ((-7.6, 4.5, 11.4),  (0.0, 0.9, 0.0), 40),
    "classic":            ((0.0, 4.4, 12.9),   (0.0, 0.75, 0.0), 40),
    "hero-low":           ((0.0, 1.4, 13.0),   (0.0, 1.5, 0.0), 42),
    "high":               ((0.0, 10.0, 10.8),  (0.0, 0.3, 0.0), 42),
}
CAM_PATH = ["high-three-quarter", "three-quarter", "classic"]

def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
TAU = 2 * math.pi

def rot_axis(axis, a):
    axis = np.array(axis, float); axis /= np.linalg.norm(axis)
    x, y, z = axis; c, s = math.cos(a), math.sin(a); C = 1 - c
    return np.array([[c + x*x*C, x*y*C - z*s, x*z*C + y*s],
                     [y*x*C + z*s, c + y*y*C, y*z*C - x*s],
                     [z*x*C - y*s, z*y*C + x*s, c + z*z*C]])

def transform_m(T, N, M, pos):
    Tw = T @ M.T + pos
    Nw = N @ np.linalg.inv(M)
    Nw /= np.linalg.norm(Nw, axis=1, keepdims=True)
    return Tw, Nw

def deform(T, N, twist, bend, H):
    """Jelly twist (torsion around the letter's vertical axis) + bend, in model space."""
    if abs(twist) < 1e-4 and abs(bend) < 1e-4: return T, N
    T = T.copy(); N = N.copy()
    h = np.clip(T[..., 1] / H, 0, 1.3)
    a = twist * h
    c, s = np.cos(a), np.sin(a)
    x, z = T[..., 0].copy(), T[..., 2].copy()
    T[..., 0] = c * x + s * z + bend * h * h
    T[..., 2] = -s * x + c * z
    ac = twist * np.clip(T[..., 1].mean(1) / H, 0, 1.3)
    c, s = np.cos(ac), np.sin(ac)
    nx, nz = N[:, 0].copy(), N[:, 2].copy()
    N[:, 0] = c * nx + s * nz; N[:, 2] = -s * nx + c * nz
    return T, N

def bob(f, settle, phase):
    r = smooth((f - settle) / 20)
    return 0.09 * r * math.sin(TAU * f / 60 + phase), 2.5 * r * math.sin(TAU * f / LOOP + phase)

def lerp_keys(keys, t):
    for (fa, *a), (fb, *b) in zip(keys, keys[1:]):
        if fa <= t < fb:
            k = 0.5 - 0.5 * math.cos(math.pi * (t - fa) / (fb - fa))
            return [u + (v - u) * k for u, v in zip(a, b)]
    return list(keys[-1][1:])

def letter_anim(f, ch, rest_yaw, phase):
    """returns (y, (sx,sy,sz), yaw, twist, bend) or None before it appears"""
    start = DROP_START[ch]
    t = f - start
    if t < 0: return None
    if ch != "U":
        if t <= FALL:
            p = t / FALL; st = 1 + 0.30 * p * p
            return 8.0 * (1 - p * p), (1 / math.sqrt(st), st, 1 / math.sqrt(st)), rest_yaw + 360 * (1 - p) ** 2, 0, 0
        t2 = t - FALL
        keys = [(0, 0, 1.36, .64), (2, 0, 1.22, .78), (4, .55, .86, 1.18), (7, .75, .95, 1.06),
                (10, .38, 1, 1), (12, 0, 1.14, .87), (14, .1, .97, 1.04), (16, 0, 1.03, .98), (18, 0, 1, 1)]
        y, sx, sy = lerp_keys(keys, t2)
        by, byaw = bob(f, start + FALL + 18, phase)
        return y + by, (sx, sy, sx), rest_yaw + byaw, 0, 0
    # --- the U: falls from higher, big twirling bounce, then a jelly twist ---
    if t <= U_FALL:
        p = t / U_FALL; st = 1 + 0.45 * p * p
        return 12.0 * (1 - p * p), (1 / math.sqrt(st), st, 1 / math.sqrt(st)), rest_yaw, 0, 0
    t2 = t - U_FALL
    if t2 < 4:   # heavy squash, then spring
        y, sx, sy = lerp_keys([(0, 0, 1.55, .52), (2, 0, 1.32, .70), (4, 0, .80, 1.30)], t2)
        return y, (sx, sy, sx), rest_yaw, 0, 0
    if t2 < 22:  # big ballistic hop with a full twirl
        s = (t2 - 4) / 18
        y = 2.4 * 4 * s * (1 - s)
        sy = 1 + 0.28 * abs(1 - 2 * s); sx = 1 / math.sqrt(sy)
        return y, (sx, sy, sx), rest_yaw + 360 * smooth(s), 0, 0
    t3 = t2 - 22  # land, then wobble like jelly
    y, sx, sy = lerp_keys([(0, 0, 1.32, .74), (3, 0, .93, 1.09), (6, 0, 1.03, .97), (9, 0, 1, 1)], t3)
    damp = math.exp(-t3 / 9)
    twist = 0.85 * damp * math.sin(TAU * t3 / 11) if t3 < 40 else 0
    bend = 0.30 * math.exp(-t3 / 10) * math.sin(TAU * t3 / 14 + 0.6) if t3 < 40 else 0
    by, byaw = bob(f, start + U_FALL + 22 + 30, phase)
    return y + by, (sx, sy, sx), rest_yaw + byaw, twist, bend

def ring_state(f):
    ph = TAU * f / LOOP
    spin = RING_SPIN * f
    yaw = math.radians(RING_YAW) * math.sin(ph)
    tilt = rot_axis((math.cos(ph), 0, math.sin(ph)), math.radians(RING_TILT))
    M = tilt @ rot_y(yaw) @ np.diag([1, 1, OVAL])
    pos = np.array([RING_OFFSET[0] + RING_DRIFT[0] * math.cos(ph),
                    RING_Y + RING_DRIFT[1] * math.sin(2 * ph),
                    RING_OFFSET[2] + RING_DRIFT[2] * math.sin(ph)])
    return spin, M, pos

def catmull(p0, p1, p2, p3, t):
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)

def camera(f):
    if CAM != "path":
        eye, target, fov = CAMERAS[CAM]
        return look_at(np.array(eye, float), np.array(target, float)), fov
    keys = [CAMERAS[k] for k in CAM_PATH]
    E = [np.array(k[0], float) for k in keys]; Tg = [np.array(k[1], float) for k in keys]; F = [k[2] for k in keys]
    u = smooth(f / CAM_END) * (len(keys) - 1)
    i = min(int(u), len(keys) - 2); t = u - i
    def path(P):
        p0 = P[max(i - 1, 0)]; p3 = P[min(i + 2, len(P) - 1)]
        return catmull(p0, P[i], P[i + 1], p3, t)
    fov = F[i] + (F[i + 1] - F[i]) * t
    return look_at(path(E), path(Tg)), fov

def setup():
    glyphs = [glyph(ch) for ch, *_ in LETTER_STYLE]
    order = ["H", "U", "E", "Y"]
    widths = [max(p[0] for p in g) - min(p[0] for p in g) for g in glyphs]
    ls = min(LS, MAX_SPAN / (sum(widths) + GAP * (len(widths) - 1)))
    total = (sum(widths) + GAP * (len(widths) - 1)) * ls
    xs, x = [], -total / 2
    for w in widths:
        xs.append(x + w * ls / 2); x += (w + GAP) * ls
    letters = []
    for (ch, col, z, yaw, ph), x, g in zip(LETTER_STYLE, xs, glyphs):
        letters.append(dict(ch=ch, x=x, z=z, yaw=yaw, phase=ph, mesh=letter_mesh(ch, col),
                            h=max(p[1] for p in g)))
    ymax = max(L["h"] for L in letters) * ls
    return dict(letters=letters, ls=ls, ymax=ymax, disc=disc_mesh())

def render(f, sc):
    fr = Frame()
    cam, fov = camera(f)
    eye = cam[1]
    sweep = None
    if SWEEP_START <= f < SWEEP_START + SWEEP_LEN:
        sweep = -8 + 16 * (f - SWEEP_START) / SWEEP_LEN
    spin, M, pos = ring_state(f)
    ringT, ringN, ringC = ring_mesh(spin=spin)
    Tw, Nw = transform_m(ringT, ringN, M, pos)
    raster(fr, *project(Tw, cam, fov), shade(Tw, Nw, ringC, eye, sweep, ymax=RING_Y + 0.6))
    ls, shadows = sc["ls"], []
    for L in sc["letters"]:
        la = letter_anim(f, L["ch"], L["yaw"], L["phase"])
        if la is None: continue
        y, scl, yw, twist, bend = la
        T, N, C = L["mesh"]
        T, N = deform(T, N, twist, bend, L["h"])
        Mx = rot_y(math.radians(yw)) @ np.diag([v * ls for v in scl])
        Tw, Nw = transform_m(T, N, Mx, np.array([L["x"], y, L["z"]]))
        raster(fr, *project(Tw, cam, fov), shade(Tw, Nw, C, eye, sweep, ymax=sc["ymax"]))
        shadows.append((L["x"], L["z"], y))
    if SHADOWS:
        discT, discN, _ = sc["disc"]
        for x, z, y in shadows:
            r = 0.95 * ls * (1 - clamp(y / 9) * 0.6)
            Tw, _ = transform(discT, discN, (r, 1, r * 0.75), 0, np.array([x, 0.01, z]))
            raster(fr, *project(Tw, cam, fov), None, shadow=True, shadow_alpha=int(130 * (1 - clamp(y / 9) * 0.7)))
    return finalize(fr)

def save_apng(frames, path, loop):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / FPS),
                   loop=loop, disposal=1, blend=0)

def main():
    sc = setup()
    for d in ("intro", "loop"): os.makedirs(f"{OUT}/{d}", exist_ok=True)
    intro, loop = [], []
    for f in range(LOOP_START + LOOP):
        img = render(f, sc)
        if f < LOOP_START:
            img.save(f"{OUT}/intro/huey_intro_{f:03d}.png"); intro.append(img)
        else:
            i = f - LOOP_START
            img.save(f"{OUT}/loop/huey_loop_{i:03d}.png"); loop.append(img)
    save_apng(intro, f"{OUT}/huey_intro.png", loop=1)            # plays once
    save_apng(loop, f"{OUT}/huey_loop.png", loop=0)              # loops forever
    save_apng(intro + loop * 3, f"{OUT}/huey_preview.png", loop=0)
    loop[0].save(f"{OUT}/huey_logo_still.png")
    with zipfile.ZipFile(f"{OUT}/huey_frames.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for d in ("intro", "loop"):
            for name in sorted(os.listdir(f"{OUT}/{d}")):
                zf.write(f"{OUT}/{d}/{name}", f"{d}/{name}")
    print(f"intro: {len(intro)} frames ({len(intro)/FPS:.1f}s), loop: {len(loop)} frames ({len(loop)/FPS:.1f}s)")

if __name__ == "__main__":
    main()
