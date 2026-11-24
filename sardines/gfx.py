"""Palette, text, panels, buttons, and pixel-art sprites (all defined in code)."""
import math
import random

import pygame

from .config import W, H


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


P = {k: hexc(v) for k, v in dict(
    night='#0a1428', deep='#0e2a4f', sea='#164a7a', sea2='#2367a0', foam='#cfeaf5', sky='#7fb7d9',
    ink='#2b1d14', black='#14101a', white='#f4f1e8', grey='#6e6a78', lgrey='#a9a6b3', dgrey='#3b3846',
    wood0='#2e1a10', wood1='#4f2e1b', wood2='#7a4a2a', wood3='#a8743f', deck='#c79a5f', deck2='#b48850',
    parch='#ead7a8', parch2='#cfb47c', parch3='#a8895a',
    red='#d9453b', dred='#8c2a24', orange='#f08a2c', yellow='#f6d55c', gold='#e8b33a',
    green='#5fbf4f', dgreen='#2f6e3a', teal='#3fb8af', blue='#3a7bd5', lblue='#8fd3ff', purple='#7a4ea3',
    fog='#d8dee6', navy='#13213b', navy2='#1c2f52',
).items()}

SKINS = [hexc('#f2c09a'), hexc('#d49a6a'), hexc('#a86b45'), hexc('#6e432a')]

# ---------------------------------------------------------------------------
# Text (custom pixel font, see font.py). Sizes: S/M -> 1x, L -> 2x, XL -> 3x, XXL -> 4x.
# ---------------------------------------------------------------------------
from . import font as pfont

S, M, L, XL, XXL = 14, 16, 24, 40, 52
LINE = 10  # line spacing for 1x text


def scale_for(size):
    return 1 if size <= 18 else 2 if size <= 30 else 3 if size <= 44 else 4


def line_h(size=16):
    return LINE * scale_for(size)


def cap_h(size=16):
    return pfont.CAP_H * scale_for(size)


def render(s, size=16, color=None):
    return pfont.render(s, color or P['white'], scale_for(size))


def text(surf, s, x, y, color=None, size=16, shadow=None, align='left'):
    sc = scale_for(size)
    img = pfont.render(s, color or P['white'], sc)
    if align == 'center':
        x -= img.get_width() // 2
    elif align == 'right':
        x -= img.get_width()
    if shadow:
        surf.blit(pfont.render(s, shadow, sc), (x + sc, y + sc))
    surf.blit(img, (x, y))
    return img.get_width()


def text_outline(surf, s, x, y, color, size, outline=None, align='left'):
    """Big title text with a chunky one-pixel (scaled) outline and drop shadow."""
    outline = outline or P['ink']
    sc = scale_for(size)
    w = text_w(s, size)
    if align == 'center':
        x -= w // 2
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (2, 2), (1, 2), (2, 1)):
        text(surf, s, x + dx * sc, y + dy * sc, outline, size)
    text(surf, s, x, y, color, size)


def text_w(s, size=16):
    return pfont.width(s, scale_for(size))


def wrap(s, width, size=16):
    lines = []
    for para in s.split('\n'):
        if not para:
            lines.append('')
            continue
        cur = ''
        for word in para.split(' '):
            t = (cur + ' ' + word) if cur else word
            if text_w(t, size) <= width:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def paragraph(surf, s, x, y, width, color=None, size=16, line=None, align='left', shadow=None):
    """Draw wrapped text; returns the y below the last line."""
    line = line or line_h(size) + 1
    for ln in wrap(s, width, size):
        xx = x + width // 2 if align == 'center' else x
        text(surf, ln, xx, y, color, size, shadow=shadow, align=align)
        y += line
    return y


# ---------------------------------------------------------------------------
# Panels and buttons
# ---------------------------------------------------------------------------
def panel(surf, rect, kind='parch'):
    r = pygame.Rect(rect)
    if kind == 'parch':
        pygame.draw.rect(surf, P['parch'], r)
        pygame.draw.rect(surf, P['parch2'], r.inflate(-4, -4), 1)
        pygame.draw.rect(surf, P['ink'], r, 1)
        for cx, cy in (r.topleft, (r.right - 1, r.top), (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1)):
            surf.set_at((cx, cy), P['parch3'])
    elif kind == 'wood':
        pygame.draw.rect(surf, P['wood1'], r)
        pygame.draw.line(surf, P['wood2'], (r.left + 1, r.top + 1), (r.right - 2, r.top + 1))
        pygame.draw.rect(surf, P['wood0'], r, 1)
    elif kind == 'dark':
        pygame.draw.rect(surf, P['navy'], r)
        pygame.draw.rect(surf, P['navy2'], r.inflate(-2, -2), 1)
        pygame.draw.rect(surf, P['black'], r, 1)
    return r


CHOICE_LINE = 11


class Button:
    def __init__(self, rect, label, cb=None, enabled=True, key=None, kind='wood', size=16, tip=None):
        self.rect = pygame.Rect(rect)
        self.label, self.cb, self.enabled, self.key = label, cb, enabled, key
        self.kind, self.size, self.tip = kind, size, tip

    def draw(self, surf, mouse):
        hover = self.enabled and self.rect.collidepoint(mouse)
        r = self.rect
        if self.kind == 'wood':
            base = P['wood3'] if hover else P['wood2']
            if not self.enabled:
                base = P['dgrey']
            pygame.draw.rect(surf, base, r)
            pygame.draw.line(surf, P['deck'] if self.enabled else P['grey'], (r.left + 1, r.top + 1),
                             (r.right - 2, r.top + 1))
            pygame.draw.line(surf, P['wood0'], (r.left + 1, r.bottom - 2), (r.right - 2, r.bottom - 2))
            pygame.draw.rect(surf, P['black'], r, 1)
            col = P['white'] if self.enabled else P['lgrey']
            text(surf, self.label, r.centerx, r.centery - cap_h(self.size) // 2, col,
                 self.size, shadow=P['wood0'], align='center')
        elif self.kind == 'choice':
            if hover:
                pygame.draw.rect(surf, P['parch2'], r)
            col = P['ink'] if self.enabled else P['parch3']
            if hover:
                col = P['dred']
            y = r.top + 3
            for line in wrap(self.label, r.width - 8, self.size):
                text(surf, line, r.left + 4, y, col, self.size)
                y += CHOICE_LINE

    def handle(self, e):
        if not self.enabled:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            from . import audio
            audio.play('click')
            if self.cb:
                self.cb()
            return True
        if e.type == pygame.KEYDOWN and self.key is not None and e.key == self.key:
            from . import audio
            audio.play('click')
            if self.cb:
                self.cb()
            return True
        return False


def bar(surf, x, y, w, h, frac, col, back=None, border=None):
    back = back or P['black']
    pygame.draw.rect(surf, back, (x, y, w, h))
    fw = int(max(0, min(1, frac)) * w)
    if fw:
        pygame.draw.rect(surf, col, (x, y, fw, h))
    if border:
        pygame.draw.rect(surf, border, (x - 1, y - 1, w + 2, h + 2), 1)


# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------
LEGS_A = ["..pppp..", "..p..p..", "..b..b.."]
LEGS_B = ["..pppp..", "...pp...", "...bb..."]

CREW_SPR = {
    'captain': ["..hhhh..", "hhhyyhhh", "..sese..", "..ssss..", ".cccccc.", "sccyyccs", ".cccccc."],
    'drunk': ["..hhhh..", ".hhhhhh.", "..sese..", "..srrs..", ".ccccccw", "sccccccg", ".ccccccg"],
    'deckhand': [".hhhhh..", ".hhhhhh.", "..sese..", "..ssss..", ".cwcwcw.", "swcwcwcs", ".cwcwcw."],
    'monkey': ["........", "...hh...", "..hhhh..", "..sese..", "..ssss..", ".sccccs.", "..cccc.."],
    'carpenter': ["..hhhh..", ".hhhhhh.", "..sese..", "..ssss..", ".cwwwwkk", "scwwwwsn", ".cwwwwcn"],
    'surgeon': ["..hhhh..", ".hhrhhh.", "..sese..", "..ssss..", ".cccccc.", "sccrcccs", ".cccccc."],
    'cook': ["..wwww..", ".wwwwww.", "..sese..", "..ssss..", ".cccccc.", "sccccccs", ".cccccc."],
    'pirate': ["..hhhh..", ".hhhhhhh", "..sese..", "..dddd..", ".cccccc.", "sccccccs", ".cccccc."],
    'brute': ["..hhhh..", ".hhhhhhh", ".ssesse.", ".dddddd.", "cccccccc", "sccccccs", "cccccccc"],
    'ghost': ["..hhhh..", ".hhhhhh.", "..sese..", "..ssss..", ".cccccc.", "s.cccc.s", ".cccccc."],
    'marine': ["..hhhh..", ".hhhhhh.", "..sese..", "..ssss..", ".cwccwc.", "sccwwccs", ".cwccwc."],
    'admiral': [".hhhhhh.", "hhhyyhhh", "w.sese.w", "w.ssss.w", "yccccccy", "sccyyccs", ".cccccc."],
    'merchant': ["..hhhh..", ".hhhhhh.", "..sese..", ".ddssdd.", "cccyyccc", "sccccccs", "cccccccc"],
}
CREW_LEGS = {
    'brute': (["pppppppp", ".pp..pp.", ".bb..bb."], ["pppppppp", "..pp.pp.", "..bb.bb."]),
    'ghost': (["..c..c..", "..c..c..", ".c....c."], ["..c..c..", ".c...c..", "c.....c."]),
    'drunk': (["..pppp..", ".p...p..", ".b...b.."], ["..pppp..", "...p.p..", "..b...b."]),
}
CREW_PAL = {
    'captain': dict(h='#1d1a2e', c='#2a4a9a', p='#e8e2d0'),
    'drunk': dict(h='#b0413e', c='#6b5a3a', p='#3d3b5c'),
    'deckhand': dict(h='#3a7bd5', c='#2b5fa8', p='#3d3b5c'),
    'monkey': dict(h='#3b3846', c='#9c6b3a', p='#4f2e1b'),
    'carpenter': dict(h='#7a4a2a', c='#5c7a3a', p='#4f2e1b'),
    'surgeon': dict(h='#f4f1e8', c='#e6e2d6', p='#3d3b5c'),
    'cook': dict(h='#f4f1e8', c='#ece6d2', p='#6e6a78'),
    'pirate': dict(h='#c0392b', c='#3b3846', p='#4f2e1b'),
    'brute': dict(h='#14101a', c='#7a2a2a', p='#2e1a10'),
    'ghost': dict(h='#4f6b5a', c='#7fc9a3', p='#7fc9a3'),
    'marine': dict(h='#14101a', c='#c0392b', p='#e8e2d0'),
    'admiral': dict(h='#14101a', c='#1d2f6b', p='#e8e2d0'),
    'merchant': dict(h='#3f8f4a', c='#7a4ea3', p='#4f2e1b'),
}
COMMON = dict(e='#14101a', y='#e8b33a', w='#f4f1e8', r='#d9453b', g='#3f8f4a', k='#3b3846',
              n='#7a4a2a', d='#2e1a10', b='#2e1a10')

_spr_cache = {}


def make_sprite(rows, colors):
    w, h = len(rows[0]), len(rows)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.' and ch in colors:
                s.set_at((x, y), colors[ch])
    return s


def crew_sprite(cls, skin=0, frame=0, flip=False, pose='stand'):
    """pose: 'stand' (frame 0/1 = legs) or 'climb' (seen from behind, frame 0/1 = which arm is up)."""
    key = (cls, skin, frame, flip, pose)
    spr = _spr_cache.get(key)
    if spr is None:
        cols = {k: hexc(v) for k, v in COMMON.items()}
        cols.update({k: hexc(v) for k, v in CREW_PAL.get(cls, CREW_PAL['pirate']).items()})
        cols['s'] = hexc('#e8eef0') if cls == 'ghost' else SKINS[skin % 4]
        cols['H'] = hexc('#3b2a20') if cls not in ('ghost', 'surgeon') else cols['s']
        legs = CREW_LEGS.get(cls, (LEGS_A, LEGS_B))[frame % 2]
        rows = CREW_SPR.get(cls, CREW_SPR['pirate']) + legs
        if pose == 'climb':
            rows = list(rows)
            rows[2] = ''.join('H' if ch in 'ser' else ch for ch in rows[2])
            rows[3] = ''.join('H' if ch in 'serd' else ch for ch in rows[3])
            rows[5] = ''.join('c' if ch == 's' else ch for ch in rows[5])
            arm = list(rows[1 if frame % 2 == 0 else 3])
            arm[0] = 's'
            rows[1 if frame % 2 == 0 else 3] = ''.join(arm)
            arm = list(rows[3 if frame % 2 == 0 else 1])
            arm[7] = 's'
            rows[3 if frame % 2 == 0 else 1] = ''.join(arm)
        spr = make_sprite(rows, cols)
        if flip:
            spr = pygame.transform.flip(spr, True, False)
        _spr_cache[key] = spr
    return spr


ICON_ROWS = {
    'helm': ["....n....", ".n.nnn.n.", "..nn.nn..", ".nn...nn.", "nnn.y.nnn", ".nn...nn.", "..nn.nn..",
             ".n.nnn.n.", "....n...."],
    'sails': ["....n....", "..wwnww..", ".wwwnwww.", ".wwwnwww.", ".wwwnwww.", "..wwnww..", "....n....",
              "nnnnnnnnn", ".nnnnnnn."],
    'guns': [".........", ".........", ".kkkkkkk.", "kkkkkkkkk", ".kkkkkkk.", "..nn.nn..", ".nnnnnnn.",
             "..k...k..", "........."],
    'bulwark': [".nnnnnnn.", "nnyyyyynn", "nnynnnynn", "nnynnnynn", "nnyyyyynn", ".nnnnnnn.", "..nnnnn..",
                "...nnn...", "....n...."],
    'sickbay': [".........", "...rrr...", "...rrr...", ".rrrrrrr.", ".rrrrrrr.", ".rrrrrrr.", "...rrr...",
                "...rrr...", "........."],
    'nest': [".........", ".........", "...www...", ".wwkkkww.", "wwkkukkww", ".wwkkkww.", "...www...",
             ".........", "........."],
    'skull': [".wwwww.", "wwwwwww", "wkwwwkw", "wkwwwkw", "wwwkwww", ".wwwww.", ".w.w.w."],
    'crown': ["y..y..y", "yy.y.yy", "yyyyyyy", "yryyyuy", "yyyyyyy"],
    'fish': ["......", ".wwww.", "wwkwwg", ".wwww.", "......", "......"],
    'spice': [".rr...", "rrrr..", ".nnnn.", "nyyyyn", ".nnnn.", "......"],
    'silk': ["uuuuu.", "ulluu.", "uuuuu.", ".uuuuu", ".uullu", ".uuuuu"],
    'tea': ["..G...", ".GGG..", "nnnnnn", "nyyyyn", "nnnnnn", ".nnnn."],
    'hand': [".s.s.s", ".s.s.s", "ssssss", "ssssss", ".ssss.", ".ssss."],
    'anchor': ["...k...", "..k.k..", "...k...", ".kkkkk.", "...k...", "k..k..k", ".kkkkk."],
    'rum': [".dddd.", "dyyyyd", "dddddd", "dddddd", "dyyyyd", ".dddd."],
    'coin': [".yyyy.", "yyddyy", "ydyyyy", "ydyyyy", "yyddyy", ".yyyy."],
    'ball': [".gggg.", "ggwggg", "gwgggg", "gggggg", "gggggg", ".gggg."],
    'heart': [".rr.rr.", "rrrrrrr", "rrrrrrr", ".rrrrr.", "..rrr..", "...r..."],
    'bolt': ["...yy", "..yy.", ".yyyy", "..yy.", ".yy..", "yy..."],
}
ICON_COLS = dict(G='#5fbf4f', l='#8fd3ff', s='#f2c09a', g='#a9a6b3', n='#4f2e1b', y='#e8b33a', w='#f4f1e8', k='#2b2836', r='#d9453b', u='#3a7bd5', d='#a8743f')
_icon_cache = {}


def icon(name, tint=None):
    key = (name, tint)
    img = _icon_cache.get(key)
    if img is None:
        cols = {k: hexc(v) for k, v in ICON_COLS.items()}
        if tint:
            cols = {k: tint for k in cols}
        img = _icon_cache[key] = make_sprite(ICON_ROWS[name], cols)
    return img


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------
def draw_sea(surf, t, top=0):
    """Animated sea: slow swells, bobbing wave crests that drift, and twinkling glints."""
    surf.fill(P['deep'], (0, top, W, H - top))
    # swells: broad bands of lighter water that roll slowly downward
    for k in range(6):
        y = top + int((k * 70 + t * 6) % (H - top + 70)) - 35
        for dy in range(0, 26, 2):
            yy = y + dy + int(math.sin(t * 0.8 + k + dy * 0.2) * 2)
            if top <= yy < H:
                pygame.draw.line(surf, (17, 49, 88), (0, yy), (W, yy))
    # crests
    for row in range(top + 5, H, 10):
        k = row // 10
        direction = 1 if k % 2 else -1
        speed = 7 + (k % 3) * 3
        off = (t * speed * direction + k * 53) % 48
        light = k % 3 == 0
        for x in range(-48, W + 48, 48):
            xx = int(x + off) + (k * 17) % 24
            ph = t * 2.2 + x * 0.09 + k * 1.7
            yy = row + int(round(math.sin(ph) * 1.6))
            ln = 5 + int((math.sin(ph * 0.5) + 1) * 2.5)
            c = P['sea2'] if light else P['sea']
            pygame.draw.line(surf, c, (xx, yy), (xx + ln, yy))
            pygame.draw.line(surf, c, (xx + 1, yy - 1), (xx + ln - 2, yy - 1))
            if light and math.sin(ph) > 0.6:
                surf.set_at((xx + ln // 2, yy - 2), P['foam'])
            pygame.draw.line(surf, P['night'], (xx + 1, yy + 1), (xx + ln - 1, yy + 1))
    # glints
    for i in range(26):
        gx = (i * 97 + int(t * 3) * 31) % W
        gy = top + (i * 53 + int(t * 3) * 17) % max(1, H - top)
        if (i + int(t * 6)) % 5 == 0:
            surf.set_at((gx, gy), P['foam'])
            surf.set_at((gx + 1, gy), P['lblue'])


_fog_layer = None


def fog_layer():
    global _fog_layer
    if _fog_layer is None:
        rng = random.Random(7)
        s = pygame.Surface((W * 2, H), pygame.SRCALPHA)
        for _ in range(160):
            r = rng.randint(30, 80)
            blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            for k in range(4):
                rr = r * (4 - k) // 4
                pygame.draw.circle(blob, (*P['fog'], 6 + k * 3), (r, r), rr)
            x = rng.randint(0, W * 2 - r * 2)
            s.blit(blob, (x, rng.randint(-r, H - r)))
            if x < r * 2:  # wrap seam
                s.blit(blob, (x + W * 2 - 2 * r, rng.randint(-r, H - r)))
        _fog_layer = s
    return _fog_layer


def draw_fog(surf, t, alpha_mul=1.0):
    layer = fog_layer()
    off = int(t * 8) % (W * 2)
    surf.blit(layer, (-off, 0))
    surf.blit(layer, (W * 2 - off, 0))


def draw_boat(surf, x, y, f, t, scale=1, flag='rebel'):
    """Side-view pixel sloop for the sea chart. (x, y) is the waterline centre; f = facing (+1 right)."""
    sc = scale
    bob = math.sin(t * 3) * 1.2
    y = y + bob
    hull = [(-11, -1), (11, -1), (8, 4), (-8, 4)]
    hull = [(x + hx * sc * f, y + hy * sc) for hx, hy in hull]
    bow = (x + 14 * sc * f, y - 3 * sc)
    pygame.draw.polygon(surf, P['wood1'], hull + [bow] if f > 0 else [bow] + hull)
    pygame.draw.polygon(surf, P['wood1'], [hull[1], bow, hull[2]] if f > 0 else [hull[0], bow, hull[3]])
    pygame.draw.line(surf, P['teal'], (x - 10 * sc, y + 1 * sc), (x + 10 * sc, y + 1 * sc))
    pygame.draw.lines(surf, P['wood0'], True, hull, 1)
    for i in (-6, -2, 2, 6):
        surf.set_at((int(x + i * sc * f), int(y + 2 * sc)), P['wood0'])
    # mast
    mx = x + 1 * sc * f
    pygame.draw.line(surf, P['wood0'], (mx, y - 1), (mx, y - 19 * sc), max(1, sc))
    # mainsail with a belly that breathes in the wind
    belly = 3 + math.sin(t * 2.2) * 1.0
    main = [(mx - 1 * f, y - 18 * sc), (mx - 1 * f, y - 3 * sc), (mx - (10 + belly) * sc * f, y - 3 * sc),
            (mx - (8 + belly) * sc * f, y - 11 * sc)]
    pygame.draw.polygon(surf, (240, 233, 212), main)
    pygame.draw.polygon(surf, (180, 168, 140), main, 1)
    pygame.draw.line(surf, (210, 200, 175), (mx - 5 * sc * f, y - 15 * sc), (mx - 5 * sc * f, y - 4 * sc))
    # jib
    jib = [(mx + 1 * f, y - 17 * sc), (mx + 1 * f, y - 3 * sc), (mx + (11 + belly * 0.6) * sc * f, y - 3 * sc)]
    pygame.draw.polygon(surf, (240, 233, 212), jib)
    pygame.draw.polygon(surf, (180, 168, 140), jib, 1)
    # boom & flag
    pygame.draw.line(surf, P['wood1'], (mx, y - 3 * sc), (mx - 11 * sc * f, y - 3 * sc))
    for i in range(6):
        wy = int(math.sin(t * 8 - i * 0.8) * 1)
        col = (47, 110, 58) if flag == 'rebel' else (38, 56, 140)
        for j in range(4):
            c = (200, 210, 220) if (flag == 'rebel' and j in (1, 2) and 1 <= i <= 3) else col
            surf.set_at((int(mx - i * f), int(y - 22 * sc + j + wy)), c)
    pygame.draw.line(surf, P['wood0'], (mx, y - 22 * sc), (mx, y - 18 * sc))


def portrait(surf, cls, skin, x, y, scale=3, bg=None, frame=None, t=0.0):
    """A framed crew portrait using the side-profile sprites. Returns its rect."""
    from . import people
    ps = max(1, scale // 2 + scale % 2)
    img = people.portrait(cls, skin, ps)
    w, h = people.W * ps + 6, people.H * ps + 4
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, bg or P['navy2'], r)
    pygame.draw.rect(surf, P['sea'], (x + 1, y + h - 6, w - 2, 5))
    bob = int(math.sin(t * 2 + skin) * 1) if t else 0
    surf.blit(img, (x + 3, y + 1 + bob))
    pygame.draw.rect(surf, frame or P['gold'], r, 1)
    pygame.draw.rect(surf, P['black'], r.inflate(2, 2), 1)
    return r


def dim(surf, alpha=140):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((5, 10, 20, alpha))
    surf.blit(s, (0, 0))
