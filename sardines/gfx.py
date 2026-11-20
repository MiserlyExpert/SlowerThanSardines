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
# Text
# ---------------------------------------------------------------------------
_fonts = {}
_text_cache = {}


def font(size):
    f = _fonts.get(size)
    if f is None:
        f = _fonts[size] = pygame.font.Font(None, size)
    return f


def render(s, size=16, color=None):
    color = color or P['white']
    key = (s, size, color)
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) > 4000:
            _text_cache.clear()
        img = _text_cache[key] = font(size).render(s, False, color)
    return img


def text(surf, s, x, y, color=None, size=16, shadow=None, align='left'):
    img = render(s, size, color)
    if align == 'center':
        x -= img.get_width() // 2
    elif align == 'right':
        x -= img.get_width()
    if shadow:
        surf.blit(render(s, size, shadow), (x + 1, y + 1))
    surf.blit(img, (x, y))
    return img.get_width()


def text_w(s, size=16):
    return font(size).size(s)[0]


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
            text(surf, self.label, r.centerx, r.centery - font(self.size).get_height() // 2 + 1, col,
                 self.size, shadow=P['wood0'], align='center')
        elif self.kind == 'choice':
            if hover:
                pygame.draw.rect(surf, P['parch2'], r)
            col = P['ink'] if self.enabled else P['parch3']
            if hover:
                col = P['dred']
            y = r.top + 2
            for line in wrap(self.label, r.width - 4, self.size):
                text(surf, line, r.left + 2, y, col, self.size)
                y += 12

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
    'dread': [".hhhhhh.", "hhhwwhhh", "..sese..", "..dddd..", ".cccccc.", "sccyyccs", ".cccccc."],
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
    'dread': dict(h='#14101a', c='#5a1a3a', p='#14101a'),
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


def crew_sprite(cls, skin=0, frame=0, flip=False):
    key = (cls, skin, frame, flip)
    spr = _spr_cache.get(key)
    if spr is None:
        cols = {k: hexc(v) for k, v in COMMON.items()}
        cols.update({k: hexc(v) for k, v in CREW_PAL.get(cls, CREW_PAL['pirate']).items()})
        cols['s'] = hexc('#e8eef0') if cls == 'ghost' else SKINS[skin % 4]
        legs = CREW_LEGS.get(cls, (LEGS_A, LEGS_B))[frame % 2]
        rows = CREW_SPR.get(cls, CREW_SPR['pirate']) + legs
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
    'anchor': ["...k...", "..k.k..", "...k...", ".kkkkk.", "...k...", "k..k..k", ".kkkkk."],
    'rum': [".dddd.", "dyyyyd", "dddddd", "dddddd", "dyyyyd", ".dddd."],
    'coin': [".yyyy.", "yyddyy", "ydyyyy", "ydyyyy", "yyddyy", ".yyyy."],
    'ball': [".gggg.", "ggwggg", "gwgggg", "gggggg", "gggggg", ".gggg."],
    'heart': [".rr.rr.", "rrrrrrr", "rrrrrrr", ".rrrrr.", "..rrr..", "...r..."],
    'bolt': ["...yy", "..yy.", ".yyyy", "..yy.", ".yy..", "yy..."],
}
ICON_COLS = dict(g='#a9a6b3', n='#4f2e1b', y='#e8b33a', w='#f4f1e8', k='#2b2836', r='#d9453b', u='#3a7bd5', d='#a8743f')
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
    surf.fill(P['deep'], (0, top, W, H - top))
    for row in range(top + 4, H, 11):
        k = row // 11
        speed = 10 * (1 + (k % 3) * 0.35)
        off = (t * speed + k * 37) % 44
        c = P['sea'] if k % 2 else P['sea2']
        for x in range(-44, W + 44, 44):
            xx = int(x + off) if k % 2 else int(x - off + 22)
            yy = row + int(math.sin(t * 1.4 + x * 0.05 + k) * 1.5)
            pygame.draw.line(surf, c, (xx, yy), (xx + 7, yy))
            pygame.draw.line(surf, c, (xx + 2, yy - 1), (xx + 4, yy - 1))


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


def dim(surf, alpha=140):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((5, 10, 20, alpha))
    surf.blit(s, (0, 0))
