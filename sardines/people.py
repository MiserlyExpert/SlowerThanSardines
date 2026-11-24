"""Side-profile crew sprites, drawn pixel by pixel so every class gets every pose.

Each sprite is a 16x22 canvas. The body occupies a 12x18 box at (2, 3); feet touch the bottom
row of the box. Poses: 'stand', 'walk' (4 frames), 'climb' (back view, 2 frames), plus actions
'repair', 'fight', 'bucket', 'haul', 'spyglass', 'gun' (2 frames each).
"""
import pygame

W, H = 16, 22
OX, OY = 2, 3          # body box offset inside the canvas
FEET_Y = OY + 17       # canvas row of the soles

SKINS = [(242, 192, 154), (212, 154, 106), (168, 107, 69), (110, 67, 42)]
HAIRS = [(59, 42, 32), (140, 90, 40), (30, 26, 30), (200, 190, 170)]


def c(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


LOOK = {
    'captain': dict(hat='tricorn', hat_col='#1d1a2e', trim='#e8b33a', coat='#2a4a9a', coat2='#e8b33a',
                    pants='#e8e2d0', boots='#14101a', buttons=True),
    'drunk': dict(hat='beanie', hat_col='#b0413e', coat='#6b5a3a', coat2='#f4f1e8', pants='#3d3b5c',
                  boots='#2e1a10', red_nose=True, bottle=True, stubble=True),
    'deckhand': dict(hat='cap', hat_col='#3a7bd5', coat='#f4f1e8', coat2='#2b5fa8', pants='#3d3b5c',
                     boots='#2e1a10', stripes=True),
    'monkey': dict(hat='hair', coat='#9c6b3a', coat2='#f4f1e8', pants='#4f2e1b', boots='#2e1a10', small=True),
    'carpenter': dict(hat='cap', hat_col='#7a4a2a', coat='#5c7a3a', coat2='#ece6d2', pants='#4f2e1b',
                      boots='#2e1a10', apron=True, beard='#8a5a30'),
    'surgeon': dict(hat='hair', hair_col='#c8c8c8', coat='#e6e2d6', coat2='#d9453b', pants='#3d3b5c',
                    boots='#14101a', glasses=True, cross=True),
    'cook': dict(hat='chef', hat_col='#f4f1e8', coat='#ece6d2', coat2='#c9c2ad', pants='#6e6a78',
                 boots='#2e1a10', apron=True, big=True),
    'pirate': dict(hat='bandana', hat_col='#c0392b', coat='#3b3846', coat2='#7a2a2a', pants='#4f2e1b',
                   boots='#14101a', beard='#2e1a10', patch=True),
    'brute': dict(hat='bandana', hat_col='#14101a', coat='#7a2a2a', coat2='#4a1818', pants='#2e1a10',
                  boots='#14101a', beard='#2e1a10', big=True),
    'ghost': dict(hat='tricorn', hat_col='#4f6b5a', trim='#7fc9a3', coat='#7fc9a3', coat2='#4f8a6a',
                  pants='#7fc9a3', boots='#4f8a6a', ghost=True),
    'marine': dict(hat='bearskin', hat_col='#14101a', coat='#c0392b', coat2='#f4f1e8', pants='#e8e2d0',
                   boots='#14101a', crossbelts=True),
    'admiral': dict(hat='bicorne', hat_col='#14101a', trim='#e8b33a', coat='#1d2f6b', coat2='#e8b33a',
                    pants='#e8e2d0', boots='#14101a', epaulette=True, wig=True, big=True, buttons=True),
    'merchant': dict(hat='cap', hat_col='#3f8f4a', coat='#7a4ea3', coat2='#e8b33a', pants='#4f2e1b',
                     boots='#2e1a10', big=True, beard='#6b4a2a'),
}
INK = (20, 16, 26)
_cache = {}


class _Canvas:
    def __init__(self, ghost):
        self.s = pygame.Surface((W, H), pygame.SRCALPHA)
        self.ghost = ghost

    def px(self, x, y, col):
        if 0 <= x < W and 0 <= y < H:
            if self.ghost:
                col = (*col[:3], 170)
            self.s.set_at((x, y), col)

    def rect(self, x, y, w, h, col):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, col)


def sprite(cls, skin=0, pose='stand', frame=0, facing=1):
    key = (cls, skin, pose, frame, facing)
    img = _cache.get(key)
    if img is None:
        img = _draw(cls, skin, pose, frame)
        if facing < 0:
            img = pygame.transform.flip(img, True, False)
        _cache[key] = img
    return img


def portrait(cls, skin=0, scale=2):
    key = ('portrait', cls, skin, scale)
    img = _cache.get(key)
    if img is None:
        base = sprite(cls, skin, 'stand', 0, 1)
        img = pygame.transform.scale(base, (W * scale, H * scale))
        _cache[key] = img
    return img


def _draw(cls, skin, pose, frame):
    L = LOOK.get(cls, LOOK['pirate'])
    cv = _Canvas(L.get('ghost'))
    S = (232, 238, 240) if L.get('ghost') else SKINS[skin % 4]
    hair = c(L['hair_col']) if 'hair_col' in L else HAIRS[(skin * 3 + len(cls)) % 4]
    coat, coat2 = c(L['coat']), c(L['coat2'])
    pants, boots = c(L['pants']), c(L['boots'])
    big, small = L.get('big'), L.get('small')
    dy = 3 if small else 0                       # small folk stand lower
    bob = 0
    if pose == 'walk' and frame in (1, 3):
        bob = -1
    X = lambda x: OX + x
    Y = lambda y: OY + y + dy + bob
    back = pose == 'climb'

    # ---- legs & boots ----
    leg_len = 4 if small else 5
    if pose == 'walk':
        d = [2, 0, -2, 0][frame % 4]
        legs = [(5 - d // 2 - 1, 0), (5 + d // 2, 1)]
    elif pose == 'climb':
        up = frame % 2
        legs = [(4, -1 if up else 0), (6, 0 if up else -1)]
    else:
        legs = [(4, 0), (6, 1)]
    top = 12 if not small else 12
    for i, (lx, extra) in enumerate(legs):
        lift = extra if pose == 'climb' else 0
        shade = pants if i == 1 else tuple(max(0, v - 25) for v in pants)
        cv.rect(X(lx), Y(top + lift), 2, leg_len - (1 if small else 0), shade)
        by = OY + 17 + lift if not small else OY + 17 + lift
        if pose == 'walk' and frame in (1, 3):
            by -= 0
        bx = X(lx)
        cv.rect(bx, by + (0 if pose != 'walk' or frame not in (1, 3) else 0), 3 if not back else 2, 1, boots)

    # ---- torso ----
    tx, tw = (3, 7) if big else (4, 5)
    cv.rect(X(tx), Y(7), tw, 5, coat)
    cv.rect(X(tx), Y(11), tw, 1, tuple(max(0, v - 40) for v in coat))          # belt line
    if not back:
        if L.get('stripes'):
            for yy in (8, 10):
                cv.rect(X(tx), Y(yy), tw, 1, coat2)
        if L.get('apron'):
            cv.rect(X(tx + tw - 3), Y(8), 3, 5, c('#f4f1e8'))
        if L.get('buttons'):
            cv.px(X(tx + tw - 1), Y(8), coat2)
            cv.px(X(tx + tw - 1), Y(10), coat2)
        if L.get('crossbelts'):
            for i in range(4):
                cv.px(X(tx + i + 1), Y(7 + i), coat2)
        if L.get('cross'):
            cv.px(X(tx + 1), Y(8), coat2)
        if L.get('epaulette'):
            cv.rect(X(tx + 2), Y(7), 3, 1, coat2)
    # ---- head ----
    hx = 4 if not big else 4
    cv.rect(X(hx), Y(2), 5, 5, S)
    if back:
        cv.rect(X(hx), Y(2), 5, 4, hair)
    else:
        cv.px(X(hx + 5), Y(4), (220, 80, 70) if L.get('red_nose') else S)        # nose
        cv.px(X(hx + 3), Y(4), INK)                                               # eye
        cv.rect(X(hx), Y(2), 2, 3, hair)                                          # hair at the back
        if L.get('patch'):
            cv.px(X(hx + 3), Y(4), INK)
            cv.px(X(hx + 2), Y(3), INK)
        if L.get('glasses'):
            cv.px(X(hx + 4), Y(4), (150, 200, 230))
        if L.get('beard'):
            cv.rect(X(hx + 1), Y(6), 4, 1, c(L['beard']))
            cv.px(X(hx + 2), Y(5), c(L['beard']))
            cv.px(X(hx + 3), Y(5), c(L['beard']))
        elif L.get('stubble'):
            cv.px(X(hx + 3), Y(6), tuple(max(0, v - 50) for v in S))
        else:
            cv.px(X(hx + 4), Y(6), tuple(max(0, v - 35) for v in S))             # mouth
        if L.get('wig'):
            cv.rect(X(hx - 1), Y(3), 2, 4, (236, 236, 236))
    # ---- hats ----
    hat = L.get('hat')
    hc = c(L['hat_col']) if 'hat_col' in L else hair
    trim = c(L['trim']) if 'trim' in L else hc
    if hat == 'tricorn':
        cv.rect(X(hx - 1), Y(1), 7, 2, hc)
        cv.rect(X(hx + 1), Y(0), 3, 1, hc)
        cv.rect(X(hx - 1), Y(2), 7, 1, trim)
    elif hat == 'bicorne':
        cv.rect(X(hx - 2), Y(1), 9, 2, hc)
        cv.rect(X(hx), Y(-1), 5, 2, hc)
        cv.rect(X(hx - 2), Y(2), 9, 1, trim)
    elif hat == 'beanie':
        cv.rect(X(hx), Y(0), 5, 2, hc)
        cv.px(X(hx + 1), Y(-1), hc)
    elif hat == 'cap':
        cv.rect(X(hx), Y(1), 5, 1, hc)
        cv.rect(X(hx + (0 if back else 3)), Y(2), 3, 1, hc)
    elif hat == 'chef':
        cv.rect(X(hx), Y(-2), 5, 4, hc)
        cv.rect(X(hx - 1), Y(-3), 7, 2, hc)
    elif hat == 'bandana':
        cv.rect(X(hx), Y(1), 5, 2, hc)
        cv.px(X(hx - 1), Y(2), hc)
        cv.px(X(hx - 2), Y(3), hc)
    elif hat == 'bearskin':
        cv.rect(X(hx), Y(-3), 5, 5, hc)
        cv.px(X(hx + 2), Y(-4), hc)
    elif hat == 'hair':
        cv.rect(X(hx), Y(1), 5, 2, hair)
        if not back:
            cv.px(X(hx + 4), Y(1), hair)

    # ---- arms ----
    arm_col = coat if not L.get('stripes') else coat2
    hand = S
    def arm(x0, y0, x1, y1):
        """A 1px-wide sleeve from shoulder to hand, with the hand pixel at the end."""
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            xx = round(x0 + (x1 - x0) * i / n)
            yy = round(y0 + (y1 - y0) * i / n)
            cv.px(X(xx), Y(yy), arm_col)
            cv.px(X(xx) + 1, Y(yy), arm_col)
        cv.px(X(x1), Y(y1), hand)
        cv.px(X(x1) + 1, Y(y1), hand)

    sx, sy = (6, 8)
    if pose == 'climb':
        up = frame % 2
        arm(3, 8, 2, 3 if up else 6)
        arm(7, 8, 8, 6 if up else 3)
    elif pose == 'walk':
        s = [-1, 0, 1, 0][frame % 4]
        arm(sx, sy, sx + s, 11)
    elif pose == 'repair':
        if frame % 2 == 0:
            arm(sx, sy, 8, 5)
            cv.rect(X(9), Y(3), 2, 2, (120, 120, 130))     # hammer head up
            cv.px(X(9), Y(5), c('#7a4a2a'))
        else:
            arm(sx, sy, 9, 10)
            cv.rect(X(10), Y(10), 2, 2, (120, 120, 130))
    elif pose == 'fight':
        if frame % 2 == 0:
            arm(sx, sy, 8, 7)
            for i in range(4):
                cv.px(X(9 + i), Y(6 - i), (220, 220, 230))   # cutlass raised
        else:
            arm(sx, sy, 9, 9)
            for i in range(4):
                cv.px(X(10 + i), Y(9), (220, 220, 230))      # thrust
    elif pose == 'bucket':
        arm(sx, sy, 8 + frame % 2, 9 - frame % 2 * 2)
        cv.rect(X(9 + frame % 2), Y(9 - frame % 2 * 2), 2, 2, c('#7a4a2a'))
    elif pose == 'haul':
        arm(sx, sy, 7, 3 + (frame % 2) * 3)
    elif pose == 'spyglass':
        arm(sx, sy, 8, 4)
        cv.rect(X(8), Y(4), 4, 1, c('#e8b33a'))
    elif pose == 'gun':
        arm(sx, sy, 9 - frame % 2, 9)
        cv.rect(X(10 - frame % 2), Y(9), 3, 1, c('#7a4a2a'))   # rammer
    else:
        arm(sx, sy, sx, 11)
    if L.get('bottle') and pose in ('stand', 'walk'):
        cv.rect(X(7), Y(9), 1, 3, c('#3f8f4a'))
        cv.px(X(7), Y(8), c('#f4f1e8'))
    if L.get('apron') and cls == 'carpenter' and pose in ('stand', 'walk'):
        cv.px(X(8), Y(11), (120, 120, 130))
    # outline-ish shadow under feet
    return cv.s
