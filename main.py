# The World in One Day - Saturday 21 November 2026.
# Draws a 1024x1024 newspaper front page in code (Python 3.13 stdlib only).
# No network, no randomness, no time dependence: two runs write the same bytes.
import math
import os
import struct
import zlib
from binascii import crc32

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (163, 22, 33)
NAVY = (31, 56, 100)
TEAL = (15, 82, 87)
GOLD = (176, 124, 12)
GREEN = (46, 110, 46)
PURPLE = (88, 60, 120)
GREY = (96, 96, 90)
LIGHT = (235, 230, 218)
WHITE = (255, 255, 255)
SEA = (18, 42, 84)
LAND = (232, 222, 190)
SKY = (20, 30, 58)
CREAM = (250, 246, 236)

REG = {
    'EUROPE': NAVY, 'AMERICAS': RED, 'ASIA': TEAL, 'ASIA-PACIFIC': TEAL,
    'MIDEAST': GOLD, 'OCEANIA': GREEN, 'SPACE': PURPLE, 'WORLD': (70, 70, 70),
}


class Canvas:
    def __init__(self, w=W, h=H, bg=PAPER):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for i in range(0, len(self.px), 3):
            self.px[i], self.px[i + 1], self.px[i + 2] = bg

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def hline(self, x0, x1, y, c):
        for x in range(max(0, x0), min(self.w, x1 + 1)):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                if fill:
                    if d <= r * r:
                        self.set(x, y, c)
                elif r * r - 2 * r <= d <= r * r:
                    self.set(x, y, c)

    def ring(self, cx, cy, r0, r1, c):
        for y in range(cy - r1, cy + r1 + 1):
            for x in range(cx - r1, cx + r1 + 1):
                d = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                if r0 * r0 <= d <= r1 * r1:
                    self.set(x, y, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[k])), min(self.w, int(xs[k + 1]) + 1)):
                    self.set(x, y, c)

    def tri(self, a, b, c_, c):
        self.poly([a, b, c_], c)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        return (struct.pack('>I', len(data)) + typ + data +
                struct.pack('>I', crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', comp) + chunk(b'IEND', b''))


# 5x7 bitmap font: each glyph is 7 rows of 5 bits (bit 4 = leftmost).
FONT = {
    'A': (14, 17, 17, 31, 17, 17, 17), 'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14), 'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31), 'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15), 'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14), 'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17), 'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17), 'N': (17, 25, 21, 19, 17, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14), 'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13), 'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30), 'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14), 'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17), 'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4), 'Z': (31, 1, 2, 4, 8, 16, 31),
    '0': (14, 17, 19, 21, 25, 17, 14), '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31), '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2), '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14), '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14), '9': (14, 17, 17, 15, 1, 2, 12),
    ' ': (0, 0, 0, 0, 0, 0, 0), '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 4, 8), ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 4, 8), "'": (4, 4, 8, 0, 0, 0, 0),
    '!': (4, 4, 4, 4, 4, 0, 4), '?': (14, 17, 1, 6, 4, 0, 4),
    '-': (0, 0, 0, 14, 0, 0, 0), '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8), '/': (1, 2, 2, 4, 8, 8, 16),
    '&': (12, 18, 20, 8, 21, 18, 13), '%': (25, 26, 2, 4, 8, 11, 19),
    '+': (0, 4, 4, 14, 4, 4, 0), '=': (0, 0, 31, 0, 31, 0, 0),
    '$': (4, 15, 20, 14, 5, 30, 4), '"': (10, 10, 0, 0, 0, 0, 0),
    '*': (0, 21, 14, 21, 0, 0, 0), '#': (10, 10, 31, 10, 31, 10, 10),
    '>': (16, 8, 4, 2, 4, 8, 16), '<': (1, 2, 4, 8, 4, 2, 1),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, scale, color, text):
    text = text.upper()
    cx = x
    for ch in text:
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            bits = g[r]
            for col in range(5):
                if bits >> (4 - col) & 1:
                    cv.rect(cx + col * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap(text, max_chars):
    words = text.split()
    lines, cur = [], ''
    for wd in words:
        if len(cur) + (1 if cur else 0) + len(wd) <= max_chars:
            cur = cur + ' ' + wd if cur else wd
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, w, scale, color, text, lh=None, max_lines=None):
    max_chars = max(1, (w + scale) // (6 * scale))
    lines = wrap(text, max_chars)
    if max_lines:
        lines = lines[:max_lines]
    if lh is None:
        lh = 9 * scale
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, scale, color, ln)
    return y + len(lines) * lh


def ellipse(cv, cx, cy, rx, ry, c):
    prev = None
    for deg in range(0, 361, 4):
        a = math.radians(deg)
        p = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
        if prev:
            cv.line(prev[0], prev[1], p[0], p[1], c)
        prev = p


# ---- illustrations: each draws inside (x, y, w, h), all geometric ----
def illo_cop31(cv, x, y, w, h):
    cv.rect(x, y, w, h, (24, 34, 56))
    cv.rect(x, y, w, int(h * 0.22), RED)
    draw_text(cv, x + 6, y + 4, 1, WHITE, 'COP31 - OVERTIME')
    for r in range(4):
        yy = y + int(h * 0.38) + r * int(h * 0.15)
        for i in range(9):
            xx = x + int(w * 0.08) + i * int(w * 0.10)
            cv.circle(xx, yy, 3, (200, 200, 190))
            cv.rect(xx - 5, yy + 3, 10, 2, (140, 140, 130))
    cv.rect(x + int(w * 0.42), y + int(h * 0.78), int(w * 0.16), int(h * 0.16), GOLD)
    cv.rect(x + int(w * 0.38), y + int(h * 0.70), int(w * 0.24), 3, GOLD)


def illo_bepi(cv, x, y, w, h):
    cv.rect(x, y, w, h, (8, 10, 26))
    for i in range(14):
        sx = x + (i * 37) % w
        sy = y + (i * 23) % h
        cv.set(sx, sy, WHITE)
    mx, my, mr = x + int(w * 0.68), y + int(h * 0.52), int(h * 0.34)
    cv.circle(mx, my, mr, (168, 132, 96))
    cv.circle(mx - mr // 3, my - mr // 4, mr // 5, (140, 108, 78))
    cv.circle(mx + mr // 4, my + mr // 5, mr // 6, (140, 108, 78))
    cv.circle(mx, my + mr // 2, mr // 7, (120, 92, 66))
    ellipse(cv, mx, my, int(w * 0.42), int(h * 0.42), (120, 160, 220))
    sx, sy = x + int(w * 0.22), y + int(h * 0.30)
    cv.rect(sx - 8, sy - 4, 16, 8, WHITE)
    cv.rect(sx - 22, sy - 2, 12, 4, (150, 170, 220))
    cv.rect(sx + 10, sy - 2, 12, 4, (150, 170, 220))
    cv.tri((sx - 8, sy + 4), (sx + 8, sy + 4), (sx, sy + 16), (255, 170, 40))
    draw_text(cv, x + 6, y + h - 12, 1, (255, 210, 90), '19:24 CET')


def illo_an12(cv, x, y, w, h):
    cv.rect(x, y, w, h, (150, 170, 195))
    cv.rect(x, y, w, int(h * 0.30), (110, 135, 170))
    cv.poly([(x, y + h), (x + int(w * 0.25), y + int(h * 0.62)),
             (x + int(w * 0.45), y + h)], (90, 100, 110))
    cv.poly([(x + int(w * 0.55), y + h), (x + int(w * 0.80), y + int(h * 0.55)),
             (x + w, y + h)], (70, 82, 95))
    px, py = x + int(w * 0.50), y + int(h * 0.34)
    cv.rect(px - 40, py - 6, 80, 12, (40, 44, 52))
    cv.tri((px + 40, py - 6), (px + 40, py + 6), (px + 56, py), (40, 44, 52))
    cv.tri((px - 40, py), (px - 52, py - 14), (px - 52, py + 2), (40, 44, 52))
    cv.tri((px - 6, py - 6), (px + 8, py - 6), (px + 2, py - 22), (40, 44, 52))
    cv.tri((px - 6, py + 6), (px + 8, py + 6), (px + 2, py + 18), (40, 44, 52))
    for ox in (-28, 28):
        cv.circle(px + ox, py - 2, 4, (120, 124, 130))
        cv.line(px + ox - 6, py - 2, px + ox + 6, py - 2, (90, 94, 100))
    cv.circle(px + 62, py + 22, 6, (120, 120, 120))
    cv.circle(px + 72, py + 30, 9, (140, 140, 140))
    cv.circle(px + 84, py + 38, 12, (160, 160, 160))


def illo_kryvyi(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    for i, bh in enumerate((0.55, 0.75, 0.45, 0.65, 0.5)):
        bx = x + int(w * (0.06 + i * 0.19))
        bw = int(w * 0.15)
        cv.rect(bx, y + h - int(h * bh), bw, int(h * bh), (10, 14, 26))
        for wy in range(3):
            cv.set(bx + 3, y + h - int(h * bh) + 6 + wy * 9, (255, 200, 90))
    ex, ey = x + int(w * 0.72), y + int(h * 0.30)
    for k in range(8):
        a = math.radians(k * 45)
        cv.line(ex, ey, int(ex + 16 * math.cos(a)), int(ey + 16 * math.sin(a)), (255, 190, 40))
    cv.circle(ex, ey, 6, (255, 120, 30))
    cv.rect(x + int(w * 0.06), y + int(h * 0.62), 14, 14, WHITE)
    cv.rect(x + int(w * 0.06) + 5, y + int(h * 0.62) + 2, 4, 10, RED)
    cv.rect(x + int(w * 0.06) + 2, y + int(h * 0.62) + 5, 10, 4, RED)


def illo_rutte(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY)
    cx, cy = x + int(w * 0.30), y + int(h * 0.52)
    cv.tri((cx, cy - 26), (cx + 7, cy), (cx - 7, cy), WHITE)
    cv.tri((cx, cy + 26), (cx + 7, cy), (cx - 7, cy), WHITE)
    cv.tri((cx - 26, cy), (cx, cy - 7), (cx, cy + 7), WHITE)
    cv.tri((cx + 26, cy), (cx, cy - 7), (cx, cy + 7), WHITE)
    cv.circle(cx, cy, 5, WHITE)
    fx = x + int(w * 0.62)
    cv.rect(fx, y + int(h * 0.30), int(w * 0.30), int(h * 0.20), WHITE)
    cv.rect(fx, y + int(h * 0.50), int(w * 0.30), int(h * 0.20), RED)
    draw_text(cv, x + 6, y + h - 12, 1, WHITE, 'WARSAW')


def illo_zecler(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 228, 214))
    cx = x + int(w * 0.50)
    cv.rect(cx - 2, y + int(h * 0.18), 4, int(h * 0.55), INK)
    cv.rect(cx - 26, y + int(h * 0.12), 52, 4, INK)
    for sgn in (-1, 1):
        tx = cx + sgn * 22
        cv.line(cx + sgn * 24, y + int(h * 0.12), tx, y + int(h * 0.30), INK)
        cv.tri((tx - 10, y + int(h * 0.30)), (tx + 10, y + int(h * 0.30)),
               (tx, y + int(h * 0.44)), GOLD)
    cv.rect(cx - 30, y + int(h * 0.76), 60, 4, INK)
    cv.rect(x + int(w * 0.72), y + int(h * 0.30), 22, 8, (120, 72, 30))
    cv.line(x + int(w * 0.72) + 11, y + int(h * 0.38), x + int(w * 0.72) + 26,
            y + int(h * 0.62), (120, 72, 30))
    draw_text(cv, x + 6, y + h - 12, 1, RED, '5 YRS')


def illo_chips(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 24, 40))
    cx, cy = x + int(w * 0.30), y + int(h * 0.50)
    cv.rect(cx - 18, cy - 18, 36, 36, (30, 90, 130))
    cv.rect(cx - 9, cy - 9, 18, 18, (200, 220, 240))
    for i in range(4):
        cv.rect(cx - 18 + i * 9, cy - 24, 3, 6, GOLD)
        cv.rect(cx - 18 + i * 9, cy + 18, 3, 6, GOLD)
        cv.rect(cx - 24, cy - 18 + i * 9, 6, 3, GOLD)
        cv.rect(cx + 18, cy - 18 + i * 9, 6, 3, GOLD)
    draw_text(cv, x + int(w * 0.58), y + int(h * 0.22), 2, (255, 210, 90), '879K')
    draw_text(cv, x + int(w * 0.58), y + int(h * 0.58), 1, WHITE, 'CHIPS')
    cv.line(x + int(w * 0.58), y + int(h * 0.72), x + int(w * 0.90), y + int(h * 0.72), RED)
    cv.tri((x + int(w * 0.90), y + int(h * 0.72)), (x + int(w * 0.84), y + int(h * 0.72) - 4),
           (x + int(w * 0.84), y + int(h * 0.72) + 4), RED)


def illo_nvidia(cv, x, y, w, h):
    cv.rect(x, y, w, h, (235, 232, 220))
    for i in range(3):
        cx = x + int(w * (0.20 + i * 0.22))
        cv.rect(cx - 8, y + int(h * 0.30), 16, int(h * 0.45), NAVY)
        cv.rect(cx - 12, y + int(h * 0.22), 24, 6, NAVY)
        cv.rect(cx - 12, y + int(h * 0.76), 24, 5, NAVY)
    mx, my = x + int(w * 0.80), y + int(h * 0.42)
    cv.ring(mx, my, 12, 17, INK)
    cv.line(mx + 12, my + 12, mx + 24, my + 24, INK)
    cv.line(mx + 12, my + 12, mx + 24, my + 24, INK)
    draw_text(cv, x + 6, y + h - 12, 1, RED, 'WACHTELL')


def illo_atp(cv, x, y, w, h):
    cv.rect(x, y, w, h, (36, 110, 60))
    cv.rect(x + 4, y + 4, w - 8, h - 8, (52, 140, 80))
    cv.hline(x + 4, x + w - 5, y + h // 2, WHITE)
    cv.vline(x + w // 2, y + 4, y + h - 5, WHITE)
    cv.rect(x + int(w * 0.42), y + h // 2 - 2, int(w * 0.16), 4, INK)
    bx, by = x + int(w * 0.72), y + int(h * 0.30)
    cv.circle(bx, by, 8, (200, 220, 60))
    cv.line(bx - 8, by - 3, bx + 8, by - 3, WHITE)
    draw_text(cv, x + 6, y + h - 12, 2, WHITE, 'SF')


def illo_riemann(cv, x, y, w, h):
    cv.rect(x, y, w, h, (28, 68, 48))
    cv.frame(x + 4, y + 4, w - 8, h - 8, (180, 150, 90), 2)
    draw_text(cv, x + 10, y + int(h * 0.22), 2, WHITE, 'Z(S)=0')
    draw_text(cv, x + 10, y + int(h * 0.55), 1, (255, 210, 90), 'CLAIM: UNVERIFIED')
    cv.rect(x + int(w * 0.62), y + int(h * 0.60), 26, 18, RED)
    draw_text(cv, x + int(w * 0.62) + 4, y + int(h * 0.60) + 5, 1, WHITE, '?')


def illo_oil(cv, x, y, w, h):
    cv.rect(x, y, w, h, (240, 232, 210))
    bx, by = x + int(w * 0.32), y + int(h * 0.42)
    cv.rect(bx - 18, by - 18, 36, 36, (30, 30, 34))
    cv.rect(bx - 18, by - 6, 36, 4, (200, 60, 40))
    cv.rect(bx - 18, by + 8, 36, 4, (200, 60, 40))
    fx = x + int(w * 0.68)
    cv.tri((fx, y + int(h * 0.22)), (fx - 10, y + int(h * 0.48)),
           (fx + 10, y + int(h * 0.48)), (255, 140, 30))
    cv.tri((fx, y + int(h * 0.38)), (fx - 6, y + int(h * 0.52)),
           (fx + 6, y + int(h * 0.52)), (255, 200, 60))
    cv.line(x + int(w * 0.60), y + int(h * 0.78), x + int(w * 0.88), y + int(h * 0.78), GREEN)
    cv.tri((x + int(w * 0.88), y + int(h * 0.78)), (x + int(w * 0.82), y + int(h * 0.78) - 5),
           (x + int(w * 0.82), y + int(h * 0.78) + 5), GREEN)
    draw_text(cv, x + 6, y + h - 12, 1, INK, '$83.41')


def illo_youth(cv, x, y, w, h):
    cv.rect(x, y, w, h, (238, 236, 224))
    for i in range(8):
        px = x + int(w * (0.08 + i * 0.11))
        py = y + int(h * 0.62)
        cv.circle(px, py - 14, 6, (60, 60, 70))
        cv.rect(px - 7, py - 8, 14, int(h * 0.38), (60, 60, 70))
    for i, pc in enumerate((RED, NAVY, TEAL)):
        px = x + int(w * (0.16 + i * 0.30))
        cv.rect(px, y + int(h * 0.10), 3, int(h * 0.42), INK)
        cv.rect(px, y + int(h * 0.10), 26, 14, pc)
    draw_text(cv, x + 6, y + h - 12, 1, RED, 'DAY 2')


def illo_xavier(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 60, 90))
    cx, cy = x + int(w * 0.50), y + int(h * 0.42)
    for r in (8, 15, 22, 29):
        for deg in range(0, 300, 6):
            a = math.radians(deg + r * 9)
            px = int(cx + r * 1.15 * math.cos(a))
            py = int(cy + r * 0.75 * math.sin(a))
            cv.set(px, py, WHITE)
    cv.circle(cx, cy, 4, (255, 210, 90))
    for wy in range(3):
        yy = y + int(h * (0.78 + wy * 0.07))
        for xx in range(x + 6, x + w - 6, 14):
            cv.line(xx, yy, xx + 8, yy, (120, 190, 220))
    draw_text(cv, x + 6, y + h - 12, 1, WHITE, 'CAT 5 - WEAKENING')


# ---- world map (stylised continents, equirectangular) ----
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 25),
     (-85, 20), (-95, 18), (-105, 22), (-115, 30), (-125, 40), (-125, 49),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-58, 64), (-45, 60), (-40, 70), (-55, 76), (-68, 76), (-60, 70)],
    [(-80, 10), (-70, 12), (-60, 8), (-50, 5), (-40, 0), (-35, -8),
     (-40, -20), (-48, -28), (-55, -35), (-65, -40), (-70, -50), (-73, -40),
     (-75, -25), (-80, -15), (-80, -5)],
    [(-10, 36), (-2, 37), (0, 39), (3, 42), (8, 44), (12, 45), (18, 40),
     (23, 36), (28, 38), (30, 42), (28, 45), (20, 45), (15, 44), (8, 48),
     (0, 50), (-2, 48), (-5, 43), (-9, 38)],
    [(-17, 15), (-10, 30), (5, 36), (20, 32), (32, 31), (40, 20), (51, 11),
     (45, 0), (38, -12), (30, -25), (20, -35), (15, -28), (12, -15), (8, -2),
     (8, 5), (-8, 5), (-15, 10)],
    [(30, 45), (38, 40), (45, 35), (52, 30), (58, 26), (65, 24), (72, 20),
     (78, 12), (84, 10), (90, 15), (96, 12), (102, 8), (108, 12), (114, 20),
     (120, 26), (128, 34), (135, 40), (142, 44), (150, 50), (158, 55),
     (168, 62), (178, 65), (170, 60), (160, 56), (148, 50), (138, 45),
     (126, 42), (114, 40), (102, 38), (90, 36), (78, 35), (66, 36),
     (54, 38), (42, 42), (34, 45)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (136, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (150, -22), (146, -19),
     (142, -15), (142, -11), (136, -12), (132, -12), (126, -14), (122, -17),
     (118, -20)],
]

PINS = [  # (story, lon, lat, region) — nudged apart so pins do not merge
    (1, 28.0, 33.0, 'WORLD'), (3, 86.1, 55.4, 'ASIA'),
    (4, 36.0, 44.0, 'EUROPE'), (5, 28.0, 58.0, 'EUROPE'),
    (6, -10.0, 50.5, 'EUROPE'), (7, -77.0, 38.9, 'AMERICAS'),
    (8, -115.0, 32.0, 'AMERICAS'), (9, 10.0, 42.0, 'EUROPE'),
    (10, -125.0, 42.0, 'AMERICAS'), (11, 56.5, 26.5, 'MIDEAST'),
    (12, 10.0, 53.5, 'EUROPE'), (13, -160.0, -21.0, 'OCEANIA'),
]


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    for cont in CONTINENTS:
        pts = [(x + int((lon + 180) / 360 * w),
                y + int((75 - lat) / 135 * h)) for lon, lat in cont]
        cv.poly(pts, LAND)
    for num, lon, lat, region in PINS:
        px = x + int((lon + 180) / 360 * w)
        py = y + int((75 - lat) / 135 * h)
        cv.circle(px, py, 7, REG[region])
        cv.ring(px, py, 6, 7, WHITE)
        s = str(num)
        draw_text(cv, px - text_w(s, 1) // 2, py - 4, 1, WHITE, s)
    cv.rect(x + 6, y + h - 30, 96, 24, PURPLE)
    draw_text(cv, x + 10, y + h - 22, 1, WHITE, '2 - SPACE')
    draw_text(cv, x + 10, y + h - 12, 1, WHITE, 'MERCURY')


# ---- stories: all verified as happened or first reported 21 Nov 2026 ----
HEROES = [
    dict(num=1, region='WORLD', place='ANTALYA', beat='CLIMATE', illo=illo_cop31,
         title='COP31 RUNS INTO OVERTIME WITH NO DEAL',
         dek='Third draft due Saturday after talks pass their deadline; '
             'fossil-fuel wording and the $120bn fund are out. (UN News)'),
    dict(num=2, region='SPACE', place='MERCURY', beat='SPACE', illo=illo_bepi,
         title='BEPICOLOMBO REACHES MERCURY AFTER 8 YEARS',
         dek='Twin orbiters fire thrusters at 19:24 CET for a 37-minute '
             'capture burn; science starts in April 2027. (ESA)'),
    dict(num=3, region='ASIA', place='SIBERIA', beat='CRASH', illo=illo_an12,
         title='MILITARY PLANE CRASHES IN SIBERIA; 19 DEAD',
         dek='An-12 goes down near Kemerovo, 3,000km east of Moscow; '
             'fault indicated. (RIA)'),
]

CARDS = [
    dict(num=4, region='EUROPE', place='KRYVYI RIH', beat='WAR', illo=illo_kryvyi,
         title='KRYVYI RIH TOLL RISES TO 44',
         dek='Two dead, 42 hurt; missiles hit a car park, then drones '
             'hit rescuers. (Vilkul)'),
    dict(num=5, region='EUROPE', place='WARSAW', beat='NATO', illo=illo_rutte,
         title='RUTTE HEADS TO WARSAW',
         dek='NATO chief due as Poland seeks more Eastern Sentry '
             'forces. (AP)'),
    dict(num=6, region='EUROPE', place='PARIS', beat='JUSTICE', illo=illo_zecler,
         title='OFFICERS GUILTY OVER BEATING',
         dek='Three police convicted; racism an aggravating factor. '
             'Five-year terms. (Court)'),
    dict(num=7, region='AMERICAS', place='WASHINGTON', beat='TECH', illo=illo_chips,
         title='879,000 AI CHIPS FOR CHINA',
         dek='75,000 for Alibaba, 150,000 for Tencent; firms sought '
             '3.4M. (House)'),
    dict(num=8, region='AMERICAS', place='CALIFORNIA', beat='TECH', illo=illo_nvidia,
         title='NVIDIA PROBES SPY CLAIM',
         dek='Wachtell to probe CEO link to alleged Chinese spy. '
             '(Reports)'),
    dict(num=9, region='EUROPE', place='TURIN', beat='SPORT', illo=illo_atp,
         title='TOP FOUR MEET IN TURIN',
         dek='Alcaraz v Shelton, Zverev v Medvedev; Medvedev beat '
             'Tiafoe 6-3 6-4. (ATP)'),
    dict(num=10, region='AMERICAS', place='SAN FRANCISCO', beat='SCIENCE',
         illo=illo_riemann,
         title='RIEMANN PROOF CLAIMED',
         dek='Alpoge says Claude helped prove it; claim unverified. '
             '(Verge)'),
    dict(num=11, region='MIDEAST', place='HORMUZ', beat='ENERGY', illo=illo_oil,
         title='OIL CLIMBS ON IRAN FEARS',
         dek='WTI $83.41 as traders weigh new strikes; gold $3,530.80. '
             '(Forbes)'),
    dict(num=12, region='EUROPE', place='EUROPE', beat='PROTEST', illo=illo_youth,
         title='YOUTH PROTESTS, DAY TWO',
         dek='Coordinated action over living costs, housing, education. '
             '(Call)'),
    dict(num=13, region='OCEANIA', place='COOK ISLANDS', beat='WEATHER',
         illo=illo_xavier,
         title='XAVIER WEAKENS AT LAST',
         dek='Cyclone eases to a tropical storm over the Cook Islands. '
             '(Met)'),
]

BRIEFS = [
    (14, 'ANTALYA', 'COP31 draws 92,000, largest ever.', 'SMC'),
    (15, 'PACIFIC', 'Xavier gale warning narrowed.', 'Met'),
    (16, 'CANBERRA', 'APEC pact by Australia, Canada, NZ.', 'DFAT'),
    (17, 'LONDON', 'England v NZ in Twickenham semi.', 'BBC'),
    (18, 'WORLD', 'Break-A-Thon: 100,000 boards.', 'OCR'),
    (19, 'LOS ANGELES', 'SAG-AFTRA vows healthcare push.', 'SAG'),
    (20, 'NASHVILLE', 'CMA ratings up as Swift returns.', 'CMA'),
    (21, 'WASHINGTON', 'Pre-Salt Typhoon telecom warning.', 'Fifth'),
    (22, 'CALIFORNIA', 'Cursor drops Chinese AI models.', 'CNBC'),
    (23, 'WASHINGTON', 'Trump weighs new Iran strikes.', 'FT'),
    (24, 'YONGBYON', 'Satellite images show plant grown.', 'WSJ'),
    (25, 'MUMBAI', 'NSE now 5th-largest exchange.', 'NSE'),
    (26, 'HARYANA', 'Orient Electric warehouse fire.', 'Rashtra'),
    (27, 'MUMBAI', 'SEBI proposes MII governance reform.', 'SEBI'),
    (28, 'MUMBAI', 'Govt in Yes Bank AT-1 review plea.', 'Govt'),
    (29, 'CAMBRIDGE', 'Free radicals may fire T cells.', 'Study'),
    (30, 'FRANKFURT', 'Lufthansa to cut 1,000 jobs.', 'JT'),
    (31, 'EUROPE', 'Shares post worst week in a year.', 'Forbes'),
    (32, 'GUANGZHOU', 'UOB to open tech centre.', 'UOB'),
    (33, 'HONG KONG', 'Hongkong Land lifts guidance.', 'HK Land'),
    (34, 'SEATTLE', 'Judge doubts Amazon bid vs Perplexity.', 'MLex'),
    (35, 'WASHINGTON', 'State AG races redraw privacy map.', 'MLex'),
    (36, 'LAS VEGAS', 'UFC seeks arbitration ruling first.', 'MLex'),
    (37, 'PUNE', 'Bajaj Pulsar RS200 at Rs1.98 lakh.', 'Bajaj'),
    (38, 'MUMBAI', 'Maharashtra Seamless orders +30%.', 'Co'),
    (39, 'MUMBAI', 'Bank of Maharashtra to raise $175M.', 'RBI'),
    (40, 'MUMBAI', 'JM Financial invests $4.41M abroad.', 'JM'),
]

NUMBERS = [
    ('19', 'DEAD IN SIBERIA CRASH'),
    ('92,000', 'AT COP31, LARGEST EVER'),
    ('879,000', 'AI CHIPS FOR CHINA'),
    ('37 MIN', 'BEPICOLOMBO CAPTURE BURN'),
    ('42', 'HURT IN KRYVYI RIH'),
    ('100,000', 'BOARDS FOR 10M MEALS'),
]

REGIONS = [('EUROPE', 9), ('AMERICAS', 10), ('ASIA-PACIFIC', 13),
           ('MIDEAST', 2), ('OCEANIA', 2), ('SPACE', 1), ('WORLD', 3)]

DATE_CHECK = ('AKVAN LANDFALL - KYIV BARRAGE - MISSILES IN POLAND - '
              'TRUMP-XI-PUTIN SUMMIT - ICJ ROHINGYA RULING - GTA VI $3.79BN - '
              'US STOCKS PLUNGE - ANTHROPIC IPO - GUPTA SENTENCE - WELLINGTON '
              'TEST DAY 2 - CAIRNCROSS FIRING - SEC PROBING NVIDIA - ESTONIA '
              'BORDER SHUTDOWN - UK DRONES - SENATE IRAN VOTE')


def build():
    cv = Canvas()
    # top bar
    draw_text(cv, 8, 5, 1, RED, 'THE WORLD IN ONE DAY')
    r = "SATURDAY'S NEWS - ONE PAGE - 40 STORIES"
    draw_text(cv, W - 8 - text_w(r, 1), 5, 1, INK, r)
    cv.rect(8, 20, W - 16, 2, INK)
    # masthead
    title = 'SATURDAY 21 NOVEMBER 2026'
    draw_text(cv, (W - text_w(title, 6)) // 2, 26, 6, INK, title)
    stand = ('COP31 RUNS INTO OVERTIME - BEPICOLOMBO REACHES MERCURY - '
             'AN-12 CRASHES IN SIBERIA')
    draw_text(cv, (W - text_w(stand, 2)) // 2, 74, 2, RED, stand)
    # region chips
    cx = 8
    for name, n in REGIONS:
        label = '%s %d' % (name, n)
        wch = text_w(label, 1) + 12
        cv.rect(cx, 92, wch, 16, REG[name if name in REG else 'WORLD'])
        draw_text(cv, cx + 6, 96, 1, WHITE, label)
        cx += wch + 5
    note = 'ALL STORIES: SAT 21 NOV 2026, ANY TIME ZONE'
    draw_text(cv, W - 8 - text_w(note, 1), 96, 1, INK, note)
    cv.rect(8, 112, W - 16, 1, INK)
    # day in numbers
    for i, (num, label) in enumerate(NUMBERS):
        bx = 8 + i * 170
        cv.frame(bx, 118, 164, 46, INK)
        draw_text(cv, bx + 6, 122, 3, RED, num)
        draw_block(cv, bx + 6, 145, 152, 1, INK, label, lh=9, max_lines=2)
    # heroes
    for i, h in enumerate(HEROES):
        hx = 8 + i * 337
        cv.frame(hx, 168, 330, 204, INK)
        h['illo'](cv, hx + 1, 169, 328, 126)
        cv.rect(hx + 1, 295, 328, 1, INK)
        kicker = '%d - %s - %s' % (h['num'], h['place'], h['beat'])
        draw_text(cv, hx + 8, 300, 1, REG[h['region']], kicker)
        draw_block(cv, hx + 8, 312, 314, 2, INK, h['title'], lh=16, max_lines=2)
        draw_block(cv, hx + 8, 344, 314, 1, (60, 60, 60), h['dek'], lh=9,
                   max_lines=3)
    # small cards, two rows of five
    for i, c in enumerate(CARDS):
        row, col = divmod(i, 5)
        x = 8 + col * 203
        y = 376 + row * 144
        cv.frame(x, y, 196, 140, INK)
        c['illo'](cv, x + 1, y + 1, 194, 56)
        kicker = '%d - %s - %s' % (c['num'], c['place'], c['beat'])
        draw_text(cv, x + 6, y + 60, 1, REG[c['region']], kicker)
        draw_block(cv, x + 6, y + 72, 184, 2, INK, c['title'], lh=16,
                   max_lines=2)
        draw_block(cv, x + 6, y + 106, 184, 1, (60, 60, 60), c['dek'], lh=10,
                   max_lines=3)
    # map + briefs
    draw_text(cv, 8, 668, 1, INK, 'WHERE IT HAPPENED')
    draw_text(cv, 338, 668, 1, INK, 'ALSO ON SATURDAY 21 NOVEMBER - 27 MORE STORIES')
    draw_map(cv, 8, 686, 322, 260)
    draw_text(cv, 8, 950 - 4, 1, (60, 60, 60),
              'PINS 1-13: POSITIONS APPROXIMATE.')
    left, right = BRIEFS[:14], BRIEFS[14:]
    for col_i, col in enumerate((left, right)):
        bx = 338 + col_i * 344
        for j, (num, place, text, src) in enumerate(col):
            yy = 688 + j * 18
            line = '%d %s - %s (%s)' % (num, place, text, src)
            draw_text(cv, bx, yy, 1, INK, line)
    # date check
    cv.frame(8, 954, W - 16, 44, RED, 2)
    draw_text(cv, 14, 959, 1, RED, 'DATE CHECK')
    hdr = ('FIRST REPORTED THURSDAY 19 OR FRIDAY 20 NOV, SO NOT SHOWN HERE '
           'AS SATURDAY NEWS:')
    draw_text(cv, 14 + text_w('DATE CHECK  ', 1), 959, 1, INK, hdr)
    draw_block(cv, 14, 972, W - 28, 1, INK, DATE_CHECK, lh=10, max_lines=2)
    # footer
    draw_text(cv, 8, 1004, 1, INK,
              'EVERY STORY HERE HAPPENED, OR WAS FIRST REPORTED, ON SATURDAY '
              '21 NOVEMBER 2026 IN AT LEAST ONE TIME ZONE.')
    draw_text(cv, 8, 1015, 1, (60, 60, 60),
              'SOURCES: ESA, AP, REUTERS, FT, WSJ, ATP TOUR, DFAT, MUNICH EYE, '
              'ASIATODAY. ORIGINAL DRAWINGS, MADE IN CODE. ONE IMAGE, ONE DAY.')
    return cv


def main():
    cv = build()
    out = os.path.join(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output'),
                       'entry.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(png_bytes(cv))
    print('wrote', out)


if __name__ == '__main__':
    main()



