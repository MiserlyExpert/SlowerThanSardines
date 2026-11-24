"""Side-view ship rendering: hull, masts and sails, cutaway decks, ladders, hazards and animated crew.

Coordinates: (ox, oy) is the top-left of a ship's room grid. Row 0 is the crow's nest, row 1 the open
top deck (its floor is the main deck), rows 2+ are below decks. Crew x/y are their feet.
"""
import math
import random

import pygame

from . import data, gfx, people
from .config import RH, TOP_ROW, TW
from .gfx import P

FACTION = {
    'rebel': dict(a=(92, 58, 34), b=(110, 70, 40), stripe=(63, 184, 175), copper=(56, 120, 110),
                  rail=(168, 116, 63), flag='rebel'),
    'crown': dict(a=(30, 44, 84), b=(38, 56, 104), stripe=(232, 179, 58), copper=(184, 115, 51),
                  rail=(232, 226, 208), flag='crown'),
    'pirate': dict(a=(48, 32, 26), b=(60, 42, 32), stripe=(140, 42, 36), copper=(40, 30, 28),
                   rail=(90, 58, 34), flag='pirate'),
    'tavern': dict(a=(100, 32, 30), b=(124, 42, 38), stripe=(232, 179, 58), copper=(184, 115, 51),
                   rail=(168, 116, 63), flag='tavern'),
    'smuggler': dict(a=(26, 42, 46), b=(34, 56, 60), stripe=(240, 138, 44), copper=(30, 34, 36),
                     rail=(90, 70, 50), flag='smuggler'),
    'ghost': dict(a=(60, 76, 72), b=(72, 92, 86), stripe=(127, 201, 163), copper=(40, 60, 56),
                  rail=(110, 138, 128), flag='ghost'),
}
ROOM_TINT = {
    'helm': (232, 179, 58), 'sails': (120, 190, 240), 'guns': (217, 69, 59), 'bulwark': (240, 138, 44),
    'sickbay': (95, 191, 79), 'nest': (170, 120, 220), 'quarters': (150, 90, 200), 'galley': (240, 150, 60),
    'mess': (220, 180, 90), 'hold': (180, 150, 100), 'magazine': (160, 30, 30), 'brig': (120, 120, 140),
    'bar': (230, 170, 50), 'cellar': (150, 100, 60), 'crypt': (100, 170, 150), 'lookout': (170, 120, 220),
    'deck': (200, 200, 200),
}
ROOM_TINT.update({'armory': (200, 60, 60), 'chartroom': (80, 170, 220), 'empty': (40, 40, 50)})
ROOM_LABEL = {
    'helm': 'HELM', 'sails': 'SAILS', 'guns': 'GUN DECK', 'bulwark': 'BULWARKS', 'sickbay': 'SICK BAY',
    'nest': 'NEST', 'quarters': 'QUARTERS', 'galley': 'GALLEY', 'mess': 'MESS', 'hold': 'HOLD',
    'magazine': 'POWDER', 'brig': 'BRIG', 'bar': 'BAR', 'cellar': 'CELLAR', 'crypt': 'CRYPT',
    'lookout': 'LOOKOUT', 'deck': 'FORECASTLE', 'armory': 'ARMORY', 'chartroom': 'CHART ROOM',
    'empty': 'EMPTY',
}

WALL = (140, 96, 58)
WALL2 = (124, 84, 50)
BEAM = (56, 34, 20)
SAIL = (238, 230, 208)
SAIL2 = (206, 194, 166)
DECK_Y = (TOP_ROW + 1) * RH          # local y of the main deck (floor of the open top deck)
WATERLINE = DECK_Y + RH // 2 + 1      # local y of the sea surface against the hull


def fac(ship):
    return FACTION.get(getattr(ship, 'faction', 'pirate'), FACTION['pirate'])


def _extents(ship):
    ex = {}
    for r in ship.rooms:
        x0, x1 = r.gx * TW, (r.gx + r.w) * TW
        if r.gy in ex:
            ex[r.gy] = (min(ex[r.gy][0], x0), max(ex[r.gy][1], x1))
        else:
            ex[r.gy] = (x0, x1)
    return ex


def hull_poly(ship, ox=0, oy=0):
    cache = getattr(ship, '_hull_poly', None)
    if cache is None:
        ex = _extents(ship)
        L1, R1 = ex[TOP_ROW]
        below = [ex[r] for r in sorted(ex) if r > TOP_ROW]
        n = len(below)
        right = [(R1 + 3, DECK_Y - 9), (R1 + 20, DECK_Y - 14)]
        left = [(L1 - 9, DECK_Y + 3), (L1 - 7, DECK_Y - 11)]
        for i, (L, R) in enumerate(below):
            right.append((R + 16 - i * 7, DECK_Y + RH * i + RH * 0.5))
            left.insert(0, (L - 7 + i * 2, DECK_Y + RH * i + RH * 0.5))
        bottom = DECK_Y + RH * n + 7
        right.append((below[-1][1] - 2, bottom))
        left.insert(0, (below[-1][0] + 8, bottom))
        cache = ship._hull_poly = right + left
    return [(ox + x, oy + y) for x, y in cache]


def hull_bounds(ship, ox, oy):
    pts = hull_poly(ship, ox, oy)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return pygame.Rect(min(xs), oy, max(xs) - min(xs), max(ys) - oy)


def gun_xs(ship):
    """x positions (local) of each cannon inside the gun deck."""
    gr = ship.sys_room.get('guns')
    if gr is None:
        return []
    r = ship.rooms[gr]
    n = max(1, len(ship.weapons))
    return [r.gx * TW + (i + 0.5) * r.w * TW / n for i in range(n)]


def cannon_pos(ship, ox, oy, i):
    """Screen position of cannon i's muzzle."""
    xs = gun_xs(ship)
    if not xs:
        return ox + ship.gw * TW // 2, oy + DECK_Y + 10
    gr = ship.rooms[ship.sys_room['guns']]
    return ox + xs[min(i, len(xs) - 1)] + 7 * aim_dir(ship), oy + gr.floor_y - 6


def aim_dir(ship):
    return 1 if ship.side == 'player' else -1


# ---------------------------------------------------------------------------
# Static hull image (planks, copper, stripes), cached per ship
# ---------------------------------------------------------------------------
def _hull_surface(ship):
    surf = getattr(ship, '_hull_surf', None)
    if surf is not None:
        return surf
    fx = fac(ship)
    pts = hull_poly(ship, 20, 40)
    w = max(p[0] for p in pts) + 40
    h = max(p[1] for p in pts) + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        col = fx['a'] if (y // 4) % 2 else fx['b']
        if y - 40 > WATERLINE + 3:
            col = fx['copper']
            if (y // 4) % 2:
                col = tuple(max(0, c - 10) for c in col)
        pygame.draw.line(body, col, (0, y), (w, y))
    for x in range(0, w, 23):                       # butt joints of the planks
        for y in range(0, h, 4):
            body.set_at(((x + (y // 4) * 9) % w, y), tuple(max(0, c - 18) for c in fx['a']))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), pts)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(body, (0, 0))
    pygame.draw.polygon(surf, P['black'], pts, 1)
    # wale stripes
    for yy, thick in ((DECK_Y + 41, 2), (DECK_Y + 40 + RH - 3, 1)):
        xs = [x for x in range(w) if mask.get_at((x, yy))[3]]
        if xs:
            pygame.draw.line(surf, fx['stripe'], (xs[0] + 1, yy), (xs[-1] - 1, yy), thick)
    ship._hull_surf = surf
    return surf


# ---------------------------------------------------------------------------
# Masts, sails, rigging (behind everything)
# ---------------------------------------------------------------------------
def draw_rigging(surf, ship, ox, oy, t):
    fx = fac(ship)
    sails = ship.sys.get('sails')
    unfurled = (sails.eff() > 0) if sails else True
    ex = _extents(ship)
    L1, R1 = ex[TOP_ROW]
    deck = oy + DECK_Y
    nest = next((r for r in ship.rooms if r.gy == 0), None)
    bow = (ox + R1 + 20, deck - 14)
    tip = (bow[0] + 26, bow[1] - 10)
    pygame.draw.line(surf, P['wood0'], bow, tip, 3)
    pygame.draw.line(surf, P['wood2'], (bow[0], bow[1] - 1), (tip[0], tip[1] - 1), 1)
    tops = []
    for k, col in enumerate(ship.masts):
        mx = ox + int((col + 0.5) * TW)
        main = nest is not None and nest.has_col(col)
        top = oy - 16 if main else oy + (0 if k == 1 else 6)
        tops.append((mx, top))
        # stays: lines to bow and stern
        pygame.draw.line(surf, (60, 44, 30), (mx, top + 2), tip if k <= 1 else (ox + L1 - 6, deck - 10))
        # square sails seen side-on: each one bellies forward, towards the bow, filled by the wind astern
        aft_most = k == min(range(len(ship.masts)), key=lambda j: ship.masts[j])
        if aft_most and len(ship.masts) > 1:
            # a fore-and-aft spanker on the aftmost mast, seen flat from the side
            gy, by_ = top + 8, deck - 13
            span = int(TW * 1.6)
            sway = math.sin(t * 1.8 + k) * 1.2
            if unfurled:
                poly = [(mx - 1, gy), (mx - span, gy + 5), (mx - span - 3 + sway, by_), (mx - 1, by_)]
                pygame.draw.polygon(surf, SAIL, poly)
                pygame.draw.polygon(surf, SAIL2, [(mx - 1, gy + 2), (mx - 6, gy + 3), (mx - 7, by_), (mx - 1, by_)])
                for yy in range(gy + 6, by_, 5):
                    pygame.draw.line(surf, SAIL2, (mx - 2, yy), (mx - span + 1 + (yy - gy) // 8, yy))
                pygame.draw.polygon(surf, (150, 140, 118), poly, 1)
            pygame.draw.line(surf, P['wood0'], (mx, gy), (mx - span, gy + 5), 2)          # gaff
            pygame.draw.line(surf, P['wood0'], (mx, by_), (mx - span - 3, by_), 2)       # boom
        else:
            yards = [top + 5, top + 5 + (deck - top - 18) // 2, deck - 15]
            depth = (19 if main else 15)
            for i in range(2):
                y0, y1 = yards[i], yards[i + 1]
                wob = 1 + 0.12 * math.sin(t * 2.2 + k * 1.3 + i)
                if unfurled:
                    d = depth * wob * (0.85 if i == 0 else 1.0)
                    curve = []
                    n = 10
                    for j in range(n + 1):
                        u = j / n
                        curve.append((mx + d * math.sin(math.pi * (0.15 + 0.7 * u)) ** 1.2, y0 + (y1 - y0) * u))
                    poly = [(mx - 2, y0)] + curve + [(mx - 2, y1)]
                    pygame.draw.polygon(surf, SAIL, poly)
                    inner = [(mx - 1, y0 + 1)] + [(mx + (x - mx) * 0.45, y) for x, y in curve] + [(mx - 1, y1 - 1)]
                    pygame.draw.polygon(surf, SAIL2, inner)
                    for j in range(1, 4):                     # reef bands
                        yy = y0 + (y1 - y0) * j / 4
                        xx = mx + d * math.sin(math.pi * (0.15 + 0.7 * j / 4)) ** 1.2
                        pygame.draw.line(surf, SAIL2, (mx, yy), (xx - 1, yy))
                    pygame.draw.lines(surf, (150, 140, 118), False, curve, 1)
                else:
                    pygame.draw.rect(surf, SAIL, (mx - 2, y0 + 1, 6, 3))
                    pygame.draw.rect(surf, SAIL2, (mx - 2, y0 + 3, 6, 1))
                # yards are seen end-on: short stubs either side of the mast
                pygame.draw.line(surf, P['wood0'], (mx - 3, y0), (mx + 4, y0), 2)
            pygame.draw.line(surf, P['wood0'], (mx - 3, yards[2]), (mx + 4, yards[2]), 2)
        pygame.draw.line(surf, P['wood0'], (mx, top), (mx, deck), 3)
        pygame.draw.line(surf, P['wood3'], (mx - 1, top), (mx - 1, deck), 1)
        # shrouds to the rails
        for sx in (mx - 14, mx + 14):
            pygame.draw.line(surf, (60, 44, 30), (mx, top + 8), (sx, deck - 8))
    # jib from the foremast to the bowsprit
    if tops:
        fm = max(tops, key=lambda p: p[0])
        jib = [(fm[0] + 2, fm[1] + 6), (tip[0] - 2, tip[1] + 2), (fm[0] + 4, deck - 14)]
        if unfurled:
            belly = math.sin(t * 2.3) * 1.5
            jib[2] = (jib[2][0] + 6 + belly, jib[2][1])
            pygame.draw.polygon(surf, SAIL, jib)
            pygame.draw.polygon(surf, (150, 140, 118), jib, 1)
        # flag on the tallest mast
        mm = min(tops, key=lambda p: p[1])
        gfx_flag(surf, mm[0], mm[1] - 1, fx['flag'], t)


def gfx_flag(surf, x, y, kind, t):
    w, h = 12, 7
    pygame.draw.line(surf, P['wood0'], (x, y), (x, y + h + 2))
    for i in range(w):
        wave = int(round(math.sin(t * 7 - i * 0.6) * (0.3 + i * 0.12)))
        for j in range(h):
            if kind == 'rebel':
                col = (47, 110, 58)
                if j in (3, 4) and 3 <= i <= 8 or (i == 9 and j in (2, 5)):
                    col = (210, 220, 228)
            elif kind == 'crown':
                col = (38, 56, 140)
                if j == 3 or i == 4:
                    col = (220, 50, 50)
                elif j in (2, 4) or i in (3, 5):
                    col = (240, 240, 240)
            elif kind == 'pirate':
                col = (20, 16, 26)
                if (i, j) in ((5, 2), (6, 2), (4, 3), (5, 3), (6, 3), (7, 3), (5, 4), (6, 4)):
                    col = (240, 240, 240)
            elif kind == 'tavern':
                col = (124, 42, 38)
                if 4 <= i <= 7 and 2 <= j <= 6:
                    col = (232, 179, 58) if j > 2 else (244, 241, 232)
            elif kind == 'smuggler':
                col = (24, 24, 30) if (i // 2) % 2 else (240, 138, 44)
            else:
                col = (110, 150, 130) if (i + j) % 3 else (60, 80, 70)
            surf.set_at((x + 1 + i, y + j + wave), col)


# ---------------------------------------------------------------------------
# Room interiors
# ---------------------------------------------------------------------------
def _tint(surf, rect, key, alpha):
    col = ROOM_TINT.get(key)
    if col:
        t = pygame.Surface(rect.size, pygame.SRCALPHA)
        t.fill((*col, alpha))
        surf.blit(t, rect.topleft)


def _wall(surf, rect, lit):
    pygame.draw.rect(surf, WALL, rect)
    for x in range(rect.left + 3, rect.right, 7):
        pygame.draw.line(surf, WALL2, (x, rect.top), (x, rect.bottom - 1))
    pygame.draw.line(surf, (96, 62, 36), (rect.left, rect.top), (rect.right - 1, rect.top), 2)   # ceiling shadow
    pygame.draw.line(surf, (110, 74, 44), (rect.left, rect.top + 2), (rect.right - 1, rect.top + 2))
    if lit:
        lx = rect.left + 6
        pygame.draw.line(surf, BEAM, (lx, rect.top + 2), (lx, rect.top + 5))
        pygame.draw.rect(surf, (60, 50, 40), (lx - 1, rect.top + 5, 3, 4))
        surf.set_at((lx, rect.top + 7), (255, 220, 120))
        glow = pygame.Surface((26, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 210, 130, 40), glow.get_rect())
        surf.blit(glow, (lx - 13, rect.top))


def _cannon(surf, x, y, d, recoil=0.0, dark=False):
    """A cannon on its carriage, side-on, pointing in direction d. (x, y) = floor under the carriage."""
    x = x - d * int(3 * recoil)
    pygame.draw.rect(surf, P['wood1'], (x - 5, y - 4, 10, 3))
    pygame.draw.circle(surf, P['wood0'], (x - 3, y - 1), 1)
    pygame.draw.circle(surf, P['wood0'], (x + 3, y - 1), 1)
    barrel = (40, 40, 48) if not dark else (25, 25, 30)
    pygame.draw.line(surf, barrel, (x - 4 * d, y - 6), (x + 7 * d, y - 6), 3)
    surf.set_at((x - 5 * d, y - 6), barrel)
    surf.set_at((x + 7 * d, y - 7), (90, 90, 100))


def draw_room_props(surf, ship, r, ox, oy, t):
    """Furniture and fittings, drawn against the back wall."""
    x0, y0 = ox + r.gx * TW, oy + r.gy * RH
    w = r.w * TW
    fy = oy + r.floor_y + 1
    k = r.sys or r.kind
    rnd = random.Random(r.idx * 7 + ship.gw)
    if k == 'helm':
        cx = x0 + w - 12
        ang = math.sin(t * 0.8) * 0.6
        pygame.draw.line(surf, P['wood1'], (cx, fy - 1), (cx, fy - 9), 2)
        pygame.draw.circle(surf, P['wood2'], (cx, fy - 11), 5, 1)
        for i in range(4):
            a = ang + i * math.pi / 4
            pygame.draw.line(surf, P['wood2'], (cx - math.cos(a) * 7, fy - 11 - math.sin(a) * 7),
                             (cx + math.cos(a) * 7, fy - 11 + math.sin(a) * 7))
        pygame.draw.rect(surf, P['wood1'], (x0 + 6, fy - 6, 4, 6))          # binnacle
        surf.set_at((x0 + 7, fy - 7), P['yellow'])
    elif k == 'sails':
        for i in range(0, w - 8, 9):
            pygame.draw.circle(surf, (190, 160, 100), (x0 + 6 + i, fy - 3), 2, 1)
        pygame.draw.line(surf, P['wood1'], (x0 + 4, fy - 8), (x0 + w - 4, fy - 8))
        for i in range(x0 + 6, x0 + w - 4, 5):
            pygame.draw.line(surf, P['wood2'], (i, fy - 10), (i, fy - 6))
    elif k == 'deck':
        cx = x0 + w // 2
        pygame.draw.rect(surf, P['wood1'], (cx - 4, fy - 7, 8, 7))      # capstan
        pygame.draw.line(surf, P['wood3'], (cx - 7, fy - 6), (cx + 7, fy - 6))
        pygame.draw.circle(surf, P['gold'], (x0 + w - 8, fy - 13), 3)      # ship's bell
        pygame.draw.line(surf, P['wood1'], (x0 + w - 8, fy - 17), (x0 + w - 8, fy - 15))
        pygame.draw.rect(surf, (70, 70, 80), (x0 + 4, fy - 5, 4, 5))      # anchor chain bitts
    elif k == 'nest':
        pass
    elif k == 'guns':
        recoil = getattr(ship, 'recoil', {})
        d = aim_dir(ship)
        for i, gx in enumerate(gun_xs(ship)):
            # gunport in the hull behind each cannon
            pygame.draw.rect(surf, (20, 40, 70), (ox + gx + 4 * d - 3, fy - 15, 7, 6))
            pygame.draw.rect(surf, BEAM, (ox + gx + 4 * d - 3, fy - 15, 7, 6), 1)
            _cannon(surf, int(ox + gx), fy, d, max(0.0, recoil.get(i, 0)) / 0.35)
        for i in range(3):
            pygame.draw.circle(surf, (40, 40, 48), (x0 + 4 + i * 3, fy - 1), 1)
    elif k == 'bulwark':
        pygame.draw.rect(surf, P['wood2'], (x0 + 4, fy - 6, 16, 2))         # workbench
        pygame.draw.line(surf, P['wood1'], (x0 + 5, fy - 4), (x0 + 5, fy))
        pygame.draw.line(surf, P['wood1'], (x0 + 18, fy - 4), (x0 + 18, fy))
        for i in range(3):
            pygame.draw.line(surf, P['wood3'], (x0 + w - 18, fy - 2 - i * 2), (x0 + w - 4, fy - 2 - i * 2), 2)
        pygame.draw.line(surf, (150, 150, 160), (x0 + 10, fy - 16), (x0 + 16, fy - 16), 2)    # saw on the wall
    elif k == 'sickbay':
        for bx in range(x0 + 3, x0 + w - 12, 18):
            pygame.draw.rect(surf, P['wood1'], (bx, fy - 5, 14, 5))
            pygame.draw.rect(surf, P['white'], (bx + 1, fy - 6, 12, 2))
            pygame.draw.rect(surf, (200, 200, 220), (bx + 1, fy - 7, 3, 2))
        cx = x0 + w - 8
        pygame.draw.rect(surf, P['white'], (cx - 3, oy + r.gy * RH + 4, 7, 7))
        pygame.draw.line(surf, P['red'], (cx, oy + r.gy * RH + 5), (cx, oy + r.gy * RH + 9))
        pygame.draw.line(surf, P['red'], (cx - 2, oy + r.gy * RH + 7), (cx + 2, oy + r.gy * RH + 7))
    elif k == 'quarters':
        pygame.draw.rect(surf, P['dred'], (x0 + 3, fy - 5, 14, 5))         # bed
        pygame.draw.rect(surf, P['white'], (x0 + 3, fy - 6, 4, 2))
        pygame.draw.rect(surf, P['wood2'], (x0 + w - 16, fy - 7, 12, 2))   # desk
        pygame.draw.line(surf, P['wood1'], (x0 + w - 15, fy - 5), (x0 + w - 15, fy))
        pygame.draw.line(surf, P['wood1'], (x0 + w - 6, fy - 5), (x0 + w - 6, fy))
        flick = int(t * 8) % 2
        surf.set_at((x0 + w - 8, fy - 9 - flick), P['yellow'])
        pygame.draw.rect(surf, P['gold'], (x0 + w // 2 - 4, y0 + 4, 9, 7), 1)     # portrait
        pygame.draw.line(surf, (160, 170, 180), (x0 + w // 2 - 2, y0 + 7), (x0 + w // 2 + 2, y0 + 7))
    elif k in ('galley',):
        pygame.draw.rect(surf, (50, 50, 58), (x0 + 4, fy - 8, 12, 8))     # stove
        pygame.draw.rect(surf, P['orange'] if int(t * 6) % 2 else P['red'], (x0 + 7, fy - 4, 6, 2))
        pygame.draw.rect(surf, (90, 90, 100), (x0 + 6, fy - 11, 8, 3))     # pot
        for i in range(3):
            sy = (t * 10 + i * 5) % 12
            surf.set_at((int(x0 + 9 + math.sin(t * 3 + i) * 2), int(fy - 13 - sy)), (200, 200, 205))
        for i in range(2):
            pygame.draw.line(surf, P['wood2'], (x0 + w - 18, y0 + 6 + i * 6), (x0 + w - 4, y0 + 6 + i * 6))
            for j in range(3):
                surf.set_at((x0 + w - 16 + j * 4, y0 + 5 + i * 6), P['lblue'] if j % 2 else P['wood3'])
    elif k in ('mess', 'bar'):
        pygame.draw.rect(surf, P['wood2'], (x0 + 4, fy - 7, w - 8, 2))     # long table / bar
        for i in range(x0 + 6, x0 + w - 6, 10):
            pygame.draw.line(surf, P['wood1'], (i, fy - 5), (i, fy))
            surf.set_at((i + 3, fy - 8), P['gold'] if k == 'bar' else P['white'])
        if k == 'bar':
            for i in range(3):
                bx = x0 + 6 + i * 9
                pygame.draw.circle(surf, P['wood1'], (bx, y0 + 9), 3)
                surf.set_at((bx, y0 + 12), P['gold'])
    elif k in ('hold', 'cellar', 'crypt', 'magazine', 'lookout'):
        stuff = {'hold': ['crate', 'barrel', 'sack', 'crate'], 'cellar': ['barrel', 'barrel', 'barrel'],
                 'crypt': ['coffin', 'coffin'], 'magazine': ['keg', 'keg', 'keg', 'balls'],
                 'lookout': []}[k]
        x = x0 + 3
        for kind in stuff:
            if x > x0 + w - 8:
                break
            x += _floor_prop(surf, kind, x, fy, rnd) + 2
    elif k == 'armory':
        for i in range(min(4, w // 12)):                      # cutlasses on the wall, crossed
            cx = x0 + 8 + i * 12
            pygame.draw.line(surf, (200, 200, 210), (cx - 3, y0 + 13), (cx + 3, y0 + 21))
            pygame.draw.line(surf, (200, 200, 210), (cx + 3, y0 + 13), (cx - 3, y0 + 21))
            surf.set_at((cx - 3, y0 + 21), P['gold'])
            surf.set_at((cx + 3, y0 + 21), P['gold'])
        hx = x0 + w - 10                                    # grappling hook and coiled line
        pygame.draw.line(surf, (90, 90, 100), (hx, y0 + 12), (hx, y0 + 20), 2)
        pygame.draw.arc(surf, (90, 90, 100), (hx - 4, y0 + 17, 8, 7), math.pi, 2 * math.pi, 1)
        pygame.draw.circle(surf, (190, 160, 100), (hx, fy - 3), 3, 1)
    elif k == 'chartroom':
        tx = x0 + w // 2
        pygame.draw.rect(surf, P['wood2'], (tx - 12, fy - 9, 24, 2))
        pygame.draw.rect(surf, P['parch'], (tx - 10, fy - 11, 20, 2))
        pygame.draw.line(surf, P['dred'], (tx - 6, fy - 11), (tx + 4, fy - 11))
        pygame.draw.line(surf, P['wood1'], (tx - 11, fy - 7), (tx - 11, fy))
        pygame.draw.line(surf, P['wood1'], (tx + 10, fy - 7), (tx + 10, fy))
        pygame.draw.circle(surf, P['gold'], (x0 + 7, y0 + 16), 4, 1)             # compass rose
        surf.set_at((x0 + 7, y0 + 13), P['red'])
    elif k == 'empty':
        for i in range(3):                                   # cobwebs and dust
            surf.set_at((x0 + 2 + i, y0 + 3 + i), (190, 190, 200))
            surf.set_at((x0 + 2 + i * 2, y0 + 3), (190, 190, 200))
        pygame.draw.line(surf, (90, 70, 50), (x0 + w // 2 - 6, fy - 1), (x0 + w // 2 + 6, fy - 1))
    elif k == 'brig':
        for i in range(x0 + 3, x0 + w - 2, 3):
            pygame.draw.line(surf, (90, 90, 100), (i, y0 + 3), (i, fy - 1))
        pygame.draw.line(surf, (90, 90, 100), (x0 + 2, y0 + 3), (x0 + w - 2, y0 + 3))


def _floor_prop(surf, kind, x, fy, rnd):
    if kind == 'crate':
        pygame.draw.rect(surf, P['wood0'], (x, fy - 8, 8, 8))
        pygame.draw.rect(surf, P['wood3'], (x + 1, fy - 7, 6, 6))
        pygame.draw.line(surf, P['wood1'], (x + 1, fy - 7), (x + 6, fy - 2))
        return 8
    if kind == 'barrel':
        pygame.draw.rect(surf, P['wood1'], (x, fy - 9, 7, 9))
        pygame.draw.rect(surf, P['wood2'], (x + 1, fy - 9, 5, 9))
        pygame.draw.line(surf, P['wood0'], (x, fy - 7), (x + 6, fy - 7))
        pygame.draw.line(surf, P['wood0'], (x, fy - 2), (x + 6, fy - 2))
        return 7
    if kind == 'sack':
        pygame.draw.ellipse(surf, (190, 165, 110), (x, fy - 6, 7, 6))
        surf.set_at((x + 3, fy - 7), P['wood1'])
        return 7
    if kind == 'keg':
        pygame.draw.rect(surf, P['wood0'], (x, fy - 6, 6, 6))
        pygame.draw.rect(surf, P['dred'], (x + 1, fy - 5, 4, 4))
        surf.set_at((x + 2, fy - 4), P['black'])
        return 6
    if kind == 'balls':
        for dx, dy in ((0, 0), (3, 0), (6, 0), (1, -2), (4, -2), (2, -4)):
            pygame.draw.circle(surf, (50, 50, 60), (x + dx + 1, fy - 2 + dy), 1)
        return 9
    if kind == 'coffin':
        pygame.draw.polygon(surf, P['wood0'], [(x, fy - 3), (x + 4, fy - 6), (x + 14, fy - 6), (x + 16, fy - 3),
                                               (x + 14, fy), (x + 4, fy)])
        pygame.draw.line(surf, P['wood2'], (x + 4, fy - 5), (x + 14, fy - 5))
        return 16
    return 4


def _ladder(surf, x, ytop, ybot, rope=False):
    col = (120, 92, 52) if rope else P['wood3']
    a, b = x + 5, x + TW - 6
    if rope:
        for i in range(0, int(ybot - ytop), 4):
            pygame.draw.line(surf, col, (a - 1, ybot - i), (b + 1, ybot - i))
        pygame.draw.line(surf, col, (a - 1, ybot), (a + 3, ytop))
        pygame.draw.line(surf, col, (b + 1, ybot), (b - 3, ytop))
        return
    pygame.draw.line(surf, P['wood0'], (a, ytop - 6), (a, ybot), 2)
    pygame.draw.line(surf, P['wood0'], (b, ytop - 6), (b, ybot), 2)
    for y in range(int(ytop) - 4, int(ybot), 5):
        pygame.draw.line(surf, col, (a + 2, y), (b - 1, y))


def draw_structure(surf, ship, ox, oy, t, interior=True):
    """Back walls, props, ladders and stairs, then floors and bulkheads."""
    fx = fac(ship)
    hatches = {}
    for kind, col, up, lo in ship.links:
        hatches.setdefault(up, []).append((col, 2 if kind == 'stairs' else 1))
    for r in ship.rooms:
        rect = pygame.Rect(ox + r.gx * TW, oy + r.gy * RH, r.w * TW, RH)
        if not r.open_air and interior:
            _wall(surf, rect, lit=(r.idx % 2 == 0) and r.kind != 'empty')
            _tint(surf, rect, r.sys or r.kind, 46 if r.kind != 'empty' else 110)
        elif r.open_air:
            _tint(surf, pygame.Rect(rect.left, rect.bottom - 8, rect.width, 6), r.sys or r.kind, 70)
        if interior or r.open_air:
            draw_room_props(surf, ship, r, ox, oy, t)
    # ladders, stairs and rigging
    for kind, col, up, lo in ship.links:
        U, Lr = ship.rooms[up], ship.rooms[lo]
        if not interior and not U.open_air and kind != 'rigging':
            continue
        if kind == 'rigging':
            _ladder(surf, ox + col * TW, oy + U.floor_y + 2, oy + Lr.floor_y, rope=True)
        elif kind == 'ladder':
            if interior:
                _ladder(surf, ox + col * TW, oy + U.floor_y + 2, oy + Lr.floor_y + 1)
        else:
            if interior:
                x0, y0 = ox + col * TW + 2, oy + U.floor_y + 2
                x1, y1 = ox + (col + 2) * TW - 2, oy + Lr.floor_y
                pygame.draw.line(surf, P['wood0'], (x0, y0), (x1, y1), 2)
                n = 6
                for i in range(1, n):
                    sx = x0 + (x1 - x0) * i / n
                    sy = y0 + (y1 - y0) * i / n
                    pygame.draw.line(surf, P['wood3'], (sx - 2, sy), (sx + 2, sy))
    # floors (with hatches) and bulkheads (with doorways)
    for r in ship.rooms:
        if r.gy == 0:
            continue
        y = oy + r.floor_y + 1
        x0, x1 = ox + r.gx * TW, ox + (r.gx + r.w) * TW
        gaps = [(ox + c * TW + 1, ox + (c + span) * TW - 1) for c, span in hatches.get(r.idx, [])]
        segs = [(x0, x1)]
        for g0, g1 in gaps:
            new = []
            for a, b in segs:
                if g1 <= a or g0 >= b:
                    new.append((a, b))
                else:
                    if g0 > a:
                        new.append((a, g0))
                    if g1 < b:
                        new.append((g1, b))
            segs = new
        top = r.gy == TOP_ROW
        for a, b in segs:
            pygame.draw.rect(surf, P['deck2'] if top else BEAM, (a, y - 1, b - a, 3))
            if top:
                pygame.draw.line(surf, P['deck'], (a, y - 1), (b - 1, y - 1))
        for g0, g1 in gaps:
            pygame.draw.line(surf, P['black'], (g0, y + 1), (g1, y + 1))
    if interior:
        for r in ship.rooms:
            if r.open_air:
                continue
            for x in (r.gx, r.gx + r.w):
                xx = ox + x * TW
                y0 = oy + r.gy * RH
                neighbour = any(o.gy == r.gy and (o.gx == x or o.gx + o.w == x) and o is not r
                                for o in ship.rooms)
                if neighbour:   # doorway: bulkhead only above the door
                    pygame.draw.rect(surf, BEAM, (xx - 1, y0, 3, RH - 25))
                    pygame.draw.line(surf, P['wood3'], (xx - 3, y0 + RH - 25), (xx + 3, y0 + RH - 25))
                else:
                    pygame.draw.rect(surf, BEAM, (xx - 1, y0, 3, RH))
    # top deck rail and crow's nest platform
    ex = _extents(ship)
    L1, R1 = ex[TOP_ROW]
    ry = oy + DECK_Y - 9
    pygame.draw.line(surf, fx['rail'], (ox + L1 - 6, ry), (ox + R1 + 4, ry), 2)
    for x in range(ox + L1 - 5, ox + R1 + 4, 5):
        pygame.draw.line(surf, fx['rail'], (x, ry), (x, oy + DECK_Y))


def draw_nest_basket(surf, ship, ox, oy):
    for r in ship.rooms:
        if r.gy == 0:
            x, y = ox + r.gx * TW - 3, oy + r.floor_y - 5
            pygame.draw.rect(surf, P['wood1'], (x, y, r.w * TW + 6, 8))
            pygame.draw.rect(surf, P['wood0'], (x, y, r.w * TW + 6, 8), 1)
            pygame.draw.line(surf, P['wood3'], (x + 1, y + 1), (x + r.w * TW + 4, y + 1))


def draw_hazards(surf, ship, ox, oy, t, interior=True):
    wl_row = ship.waterline_row()
    for r in ship.rooms:
        rect = pygame.Rect(ox + r.gx * TW, oy + r.gy * RH, r.w * TW, RH)
        if r.breach and interior:
            bx = rect.left + rect.width // 2 + ((r.idx * 7) % 9) - 4
            by = rect.top + 8
            pygame.draw.polygon(surf, (10, 25, 50), [(bx - 4, by - 2), (bx, by - 5), (bx + 4, by - 1),
                                                     (bx + 3, by + 4), (bx - 2, by + 5), (bx - 5, by + 2)])
            if True:
                for i in range(7):      # the sea spraying in
                    k = ((t * 3 + i / 7) % 1)
                    px = bx + (i - 3) * 1.5 * k * 3
                    py = by + k * k * (r.floor_y + oy - by)
                    surf.set_at((int(px), int(py)), P['lblue'] if i % 2 else P['foam'])
        if r.fire > 0:
            fr = random.Random(int(t * 12) + r.idx * 97)
            n = int(3 + r.fire / 8)
            for _ in range(n):
                fx = fr.randint(rect.left + 2, rect.right - 3)
                h = fr.randint(3, 4 + int(r.fire / 12))
                base = oy + r.floor_y
                pygame.draw.line(surf, P['red'], (fx, base), (fx, base - h), 2)
                pygame.draw.line(surf, P['orange'], (fx, base - 1), (fx, base - h + 1), 1)
                surf.set_at((fx, base - h - 1), P['yellow'])
            for i in range(3):
                sy = (t * 14 + i * 6) % (RH - 4)
                surf.set_at((int(rect.centerx + math.sin(t * 2 + i) * 5), int(rect.top + RH - 6 - sy)),
                            (90, 90, 96))


def draw_exterior(surf, ship, ox, oy, t):
    """The near side of the hull, covering the decks (enemy ships seen without a telescope)."""
    hs = _hull_surface(ship)
    clip = pygame.Rect(0, DECK_Y + 40, hs.get_width(), hs.get_height())
    surf.blit(hs, (ox - 20, oy + DECK_Y), clip)
    d = aim_dir(ship)
    gr = ship.sys_room.get('guns')
    if gr is not None:
        fy = oy + ship.rooms[gr].floor_y
        for gx in gun_xs(ship):
            px = ox + gx + 4 * d
            pygame.draw.rect(surf, P['black'], (px - 3, fy - 10, 7, 6))
            pygame.draw.circle(surf, (40, 40, 48), (int(px), fy - 7), 2)
    for r in ship.rooms:
        if r.open_air or r.sys == 'guns':
            continue
        for i in range(r.w):
            if (i + r.idx) % 2 == 0:
                px, py = ox + (r.gx + i + 0.5) * TW, oy + r.gy * RH + 9
                lit = (int(t * 0.5 + i + r.idx) % 4) != 0
                pygame.draw.circle(surf, P['black'], (int(px), py), 2)
                surf.set_at((int(px), py), P['yellow'] if lit else (40, 40, 48))


def draw_room_labels(surf, ship, ox, oy):
    for r in ship.rooms:
        key = r.sys or r.kind
        label = ROOM_LABEL.get(key, key.upper())
        rect = pygame.Rect(ox + r.gx * TW, oy + r.gy * RH, r.w * TW, RH)
        lvl = getattr(r, 'level', 1) if not r.sys else ship.sys[r.sys].level
        if gfx.text_w(label) + 6 > rect.width - (12 if r.sys else 0):
            continue
        col = ROOM_TINT.get(key, (220, 220, 220)) if key != 'empty' else (130, 130, 140)
        w = gfx.text_w(label) + 4
        bg = pygame.Surface((w, 9), pygame.SRCALPHA)
        bg.fill((12, 10, 16, 150))
        surf.blit(bg, (rect.left + 2, rect.top + 2))
        gfx.text(surf, label, rect.left + 4, rect.top + 3, tuple(min(255, v + 40) for v in col))
        for i in range(min(lvl, 8) if lvl > 1 else 0):
            surf.set_at((rect.left + 4 + i * 2, rect.top + 12), P['gold'])


def draw_room_overlay(surf, ship, ox, oy, interior, hover=None, targets=()):
    for r in ship.rooms:
        rect = pygame.Rect(ox + r.gx * TW, oy + r.gy * RH, r.w * TW, RH)
        if not interior and not r.open_air:
            for x in range(rect.left, rect.right, 4):
                surf.set_at((x, rect.top), (200, 200, 210))
                surf.set_at((x, rect.bottom - 1), (200, 200, 210))
            for y in range(rect.top, rect.bottom, 4):
                surf.set_at((rect.left, y), (200, 200, 210))
                surf.set_at((rect.right - 1, y), (200, 200, 210))
        if r.sys:
            s = ship.sys[r.sys]
            tint = P['red'] if s.damage >= s.level else (P['orange'] if s.damage > 0 else None)
            ic = gfx.icon(r.sys, tint)
            surf.blit(ic, (rect.right - 11, rect.top + 2))
        if hover == r.idx:
            pygame.draw.rect(surf, P['yellow'], rect, 1)
        if r.idx in targets:
            c = rect.center
            pygame.draw.rect(surf, P['red'], rect.inflate(-2, -2), 1)
            pygame.draw.circle(surf, P['red'], c, 4, 1)
            pygame.draw.line(surf, P['red'], (c[0] - 6, c[1]), (c[0] + 6, c[1]))
            pygame.draw.line(surf, P['red'], (c[0], c[1] - 6), (c[0], c[1] + 6))


def draw_sea_front(surf, ship, ox, oy, t, alpha=255):
    """The sea laps at the very bottom of the hull, so the ship floats without hiding any deck."""
    b = hull_bounds(ship, ox, oy)
    low = max(r.floor_y for r in ship.rooms) + oy + 5
    h = b.bottom - low + 6
    if h <= 0:
        return
    pygame.draw.rect(surf, P['deep'], (b.left - 6, low + 2, b.width + 12, h))
    for x in range(b.left - 6, b.right + 6, 2):
        yy = low + int(math.sin(t * 2.6 + x * 0.12) * 1.6)
        pygame.draw.line(surf, P['sea2'], (x, yy + 1), (x, low + 3))
        if (x // 2 + int(t * 5)) % 7 == 0:
            surf.set_at((x, yy), P['foam'])


# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------
def draw_crew(surf, ship, ox, oy, t, selected=(), visible_sides=('player', 'enemy'), hover_crew=None):
    for c in sorted(ship.crew, key=lambda c: (c.y, c.uid)):
        if not c.alive or c.side not in visible_sides:
            continue
        draw_one(surf, c, ox + c.x, oy + c.y, t, c in selected, c is hover_crew)


def crew_pose(c):
    mode = getattr(c, 'mode', 'stand')
    act = getattr(c, 'act_t', 0.0)
    if mode == 'climb' and c.moving:
        return 'climb', int(c.walk_t * 6) % 2
    if c.moving:
        return 'walk', int(c.walk_t * 9) % 4
    k = int(act * 4 + c.uid) % 2
    task = c.task
    if task in ('repair', 'patch', 'sabotage'):
        return 'repair', k
    if task == 'fight':
        return 'fight', int(act * 5 + c.uid) % 2
    if task == 'fire':
        return 'bucket', k
    if task == 'man' and c.ship is not None:
        sysn = c.ship.rooms[c.room].sys
        if sysn == 'sails':
            return 'haul', int(act * 2 + c.uid) % 2
        if sysn == 'nest':
            return 'spyglass', 0
        if sysn == 'guns':
            return 'gun', int(act * 1.5 + c.uid) % 2
    return 'stand', 0


def draw_one(surf, c, fx_, fy_, t, selected=False, hover=False):
    x, y = int(fx_), int(fy_)
    pose, frame = crew_pose(c)
    facing = getattr(c, 'facing', 1)
    if c.task == 'fight' and c.foe is not None and not c.moving:
        facing = 1 if c.foe.x > c.x else -1
    if pose == 'stand' and c.task == 'man' and c.ship is not None and c.ship.rooms[c.room].sys == 'helm':
        facing = 1
    spr = people.sprite(c.cls, c.skin, pose, frame, facing)
    wob = 0
    if c.cls == 'drunk' and pose in ('stand', 'walk'):
        wob = int(round(math.sin(c.anim * 2.1) * 1.3))
    bob = -1 if (pose == 'stand' and int(c.anim * 1.1 + c.uid) % 4 == 0) else 0
    sx, sy = x - people.W // 2 + wob, y - people.FEET_Y - 1 + bob
    if selected or hover:
        col = P['green'] if selected else P['yellow']
        mask = pygame.mask.from_surface(spr)
        for px_, py_ in mask.outline():
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surf.set_at((sx + px_ + dx, sy + py_ + dy), col)
    surf.blit(spr, (sx, sy))
    # little effects
    act = getattr(c, 'act_t', 0.0)
    hx = x + 7 * facing
    if pose == 'repair' and frame == 1 and int(act * 10) % 2:
        surf.set_at((hx + 2 * facing, y - 8), P['yellow'])
        surf.set_at((hx + 3 * facing, y - 9), P['white'])
    if pose == 'bucket':
        k = (act * 2.5 + c.uid * 0.3) % 1
        for i in range(5):
            surf.set_at((int(hx + facing * (k * 12 + i)), int(y - 12 + k * k * 10 + i)), P['lblue'])
    if pose == 'fight' and int(act * 12) % 4 == 0:
        surf.set_at((hx + 5 * facing, y - 12), P['yellow'])
    if c.hp < c.max_hp or selected:
        col = P['green'] if c.side == 'player' else P['red']
        gfx.bar(surf, x - 6, sy - 3, 12, 2, max(0.0, c.hp / c.max_hp), col)


def c_skin(c):
    return gfx.SKINS[c.skin % 4]


def draw_barks(surf, ship, ox, oy, visible_sides=('player', 'enemy')):
    for c in ship.crew:
        if c.alive and c.bark and c.bark_t > 0 and c.side in visible_sides:
            img = gfx.render(c.bark, 14, P['ink'])
            w = img.get_width() + 6
            x = int(ox + c.x - w // 2)
            y = int(oy + c.y - 32)
            x = max(2, min(x, 638 - w))
            r = pygame.Rect(x, y, w, img.get_height() + 3)
            pygame.draw.rect(surf, P['white'], r)
            pygame.draw.rect(surf, P['ink'], r, 1)
            px = int(ox + c.x)
            pygame.draw.polygon(surf, P['white'], [(px - 2, r.bottom - 1), (px + 2, r.bottom - 1), (px, r.bottom + 3)])
            surf.blit(img, (r.left + 3, r.top + 2))


# ---------------------------------------------------------------------------
# Whole ship
# ---------------------------------------------------------------------------
def draw_ship(surf, ship, ox, oy, t, interior=True, selected=(), hover=None, targets=(),
              crew_sides=('player', 'enemy'), sea=True, overlay=True, hover_crew=None):
    draw_rigging(surf, ship, ox, oy, t)
    hs = _hull_surface(ship)
    surf.blit(hs, (ox - 20, oy - 40))
    draw_structure(surf, ship, ox, oy, t, interior)
    if interior:
        draw_hazards(surf, ship, ox, oy, t, True)
    else:
        draw_exterior(surf, ship, ox, oy, t)
        draw_hazards(surf, ship, ox, oy, t, False)
    vis = crew_sides
    if not interior:   # without a telescope you only see your own boarders
        vis = tuple(s for s in crew_sides if s != ship.side)
    if overlay and interior:
        draw_room_labels(surf, ship, ox, oy)
    draw_crew(surf, ship, ox, oy, t, selected, visible_sides=vis, hover_crew=hover_crew)
    draw_nest_basket(surf, ship, ox, oy)
    if overlay:
        draw_room_overlay(surf, ship, ox, oy, interior, hover, targets)
    if sea:
        draw_sea_front(surf, ship, ox, oy, t)


# legacy helpers used by menus
def draw_hull(surf, ship, ox, oy, t, wake=True):
    draw_ship(surf, ship, ox, oy, t)


def draw_rooms(surf, ship, ox, oy, t, hover=None, targets=(), show_sys=True):
    pass


def room_at(ship, ox, oy, pos):
    x, y = pos[0] - ox, pos[1] - oy
    for r in ship.rooms:
        if r.contains(x, y):
            return r.idx
    return None


def crew_at(ship, ox, oy, pos, side='player'):
    for c in ship.crew:
        if c.alive and c.side == side and abs(ox + c.x - pos[0]) <= 7 and -21 <= (pos[1] - (oy + c.y)) <= 2:
            return c
    return None
