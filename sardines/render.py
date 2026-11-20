"""Drawing ships, rooms and crew."""
import math
import random

import pygame

from . import gfx
from .config import T
from .gfx import P


def hull_poly(ship, ox, oy):
    SW, SH = ship.gw * T, ship.gh * T
    p = 8
    pts = [(-p - 4, 6 - p), (-p + 4, -p), (SW + p, -p), (SW + p + 26, SH / 2), (SW + p, SH + p),
           (-p + 4, SH + p), (-p - 4, SH + p - 6)]
    if ship.facing < 0:
        pts = [(SW - x, y) for x, y in pts]
    return [(ox + x, oy + y) for x, y in pts]


def draw_hull(surf, ship, ox, oy, t):
    SW, SH = ship.gw * T, ship.gh * T
    f = ship.facing
    enemy = ship.side == 'enemy'
    # wake foam
    for i in range(6):
        wx = ox + (-24 - i * 9 if f > 0 else SW + 24 + i * 9)
        wy = oy + SH / 2 + math.sin(t * 3 + i) * (3 + i)
        pygame.draw.line(surf, P['foam'], (wx, wy - 6 - i), (wx + 4 * -f, wy - 6 - i))
        pygame.draw.line(surf, P['foam'], (wx, wy + 6 + i), (wx + 4 * -f, wy + 6 + i))
    # yards & rolled sails poking out of the hull (top-down masts)
    for frac in (0.3, 0.62):
        mx = ox + (SW * frac if f > 0 else SW * (1 - frac))
        pygame.draw.line(surf, P['wood1'], (mx, oy - 18), (mx, oy + SH + 18), 3)
        pygame.draw.line(surf, P['white'], (mx + 2 * -f, oy - 16), (mx + 2 * -f, oy + SH + 16), 2)
    # bowsprit
    bx = ox + (SW + 34 if f > 0 else -34)
    pygame.draw.line(surf, P['wood1'], (ox + (SW + 26 if f > 0 else -26), oy + SH / 2), (bx + 10 * f, oy + SH / 2 - 2), 2)
    poly = hull_poly(ship, ox, oy)
    pygame.draw.polygon(surf, P['wood1'] if not enemy else (70, 40, 34), poly)
    inner = hull_poly(ship, ox, oy)
    cx = ox + SW / 2
    cy = oy + SH / 2
    inner = [(cx + (x - cx) * 0.94, cy + (y - cy) * 0.86) for x, y in inner]
    pygame.draw.polygon(surf, P['wood2'] if not enemy else (110, 62, 46), inner)
    pygame.draw.polygon(surf, P['wood0'], poly, 2)
    # gunports
    guns = ship.sys_room.get('guns')
    if guns is not None:
        r = ship.rooms[guns]
        for i in range(max(1, len(ship.weapons))):
            gx = ox + r.gx * T + 5 + i * 8
            for gy in (oy - 6, oy + SH + 3):
                pygame.draw.rect(surf, P['black'], (gx, gy, 5, 3))
    # flag at the stern
    fx = ox + (-14 if f > 0 else SW + 14)
    fy = oy + SH / 2
    wave = int(math.sin(t * 6) * 1.5)
    pygame.draw.line(surf, P['wood0'], (fx, fy - 2), (fx - 6 * f, fy - 2))
    flag = pygame.Rect(0, 0, 10, 7)
    flag.midright = (fx - 6 * f, fy - 2 + wave) if f > 0 else (0, 0)
    if f < 0:
        flag.midleft = (fx - 6 * f, fy - 2 + wave)
    if enemy:
        pygame.draw.rect(surf, P['black'], flag)
        surf.set_at((flag.centerx, flag.centery - 1), P['white'])
        surf.set_at((flag.centerx - 1, flag.centery), P['white'])
        surf.set_at((flag.centerx + 1, flag.centery), P['white'])
    else:
        pygame.draw.rect(surf, P['blue'], flag)
        pygame.draw.line(surf, P['gold'], flag.midleft, flag.midright)
        pygame.draw.line(surf, P['gold'], flag.midtop, flag.midbottom)


def draw_rooms(surf, ship, ox, oy, t, hover=None, targets=(), show_sys=True, rng=random):
    for r in ship.rooms:
        rect = pygame.Rect(ox + r.gx * T, oy + r.gy * T, r.w * T, r.h * T)
        pygame.draw.rect(surf, P['deck'], rect)
        for y in range(rect.top + 4, rect.bottom, 5):
            pygame.draw.line(surf, P['deck2'], (rect.left + 1, y), (rect.right - 2, y))
        # tile grid dots
        for tx, ty in r.tiles():
            surf.set_at((ox + tx * T, oy + ty * T), P['deck2'])
        if r.sys and show_sys:
            s = ship.sys[r.sys]
            tint = None
            if s.damage >= s.level:
                tint = P['red']
            elif s.damage > 0:
                tint = P['orange']
            ic = gfx.icon(r.sys, tint)
            surf.blit(ic, (rect.centerx - ic.get_width() // 2, rect.centery - ic.get_height() // 2))
        # water
        if r.water > 1:
            hh = int(rect.height * r.water / 100)
            ws = pygame.Surface((rect.width, hh), pygame.SRCALPHA)
            ws.fill((40, 110, 200, 150))
            for x in range(0, rect.width, 6):
                yy = int(1 + math.sin(t * 4 + x * 0.4))
                pygame.draw.line(ws, (170, 220, 250, 200), (x, yy), (x + 3, yy))
            surf.blit(ws, (rect.left, rect.bottom - hh))
        # breach
        if r.breach:
            bx, by = rect.left + rect.width // 2 + 4, rect.top + rect.height // 2 + 3
            pygame.draw.circle(surf, P['black'], (bx, by), 4)
            pygame.draw.circle(surf, P['wood0'], (bx, by), 4, 1)
            for i in range(3):
                a = t * 7 + i * 2.1
                surf.set_at((int(bx + math.cos(a) * 6), int(by - 3 - abs(math.sin(a)) * 5)), P['lblue'])
        # fire
        if r.fire > 0:
            n = int(4 + r.fire / 6)
            fr = random.Random(int(t * 10) + r.idx * 97)
            for _ in range(n):
                fx = fr.randint(rect.left + 2, rect.right - 4)
                fy = fr.randint(rect.top + 4, rect.bottom - 3)
                hgt = fr.randint(2, 5)
                pygame.draw.line(surf, P['orange'], (fx, fy), (fx, fy - hgt), 2)
                surf.set_at((fx, fy - hgt - 1), P['yellow'])
        pygame.draw.rect(surf, P['wood0'], rect, 1)
        if hover == r.idx:
            pygame.draw.rect(surf, P['yellow'], rect, 1)
        if r.idx in targets:
            c = rect.center
            col = P['red']
            pygame.draw.rect(surf, col, rect.inflate(-4, -4), 1)
            pygame.draw.line(surf, col, (c[0] - 5, c[1]), (c[0] + 5, c[1]))
            pygame.draw.line(surf, col, (c[0], c[1] - 5), (c[0], c[1] + 5))
    # doors
    done = set()
    for (a, b), (dx, dy) in ship.doors.items():
        if (b, a) in done:
            continue
        done.add((a, b))
        ra, rb = ship.rooms[a], ship.rooms[b]
        vertical = ra.gx + ra.w == rb.gx or rb.gx + rb.w == ra.gx
        if vertical:
            pygame.draw.rect(surf, P['wood3'], (ox + dx - 1, oy + dy - 4, 3, 8))
        else:
            pygame.draw.rect(surf, P['wood3'], (ox + dx - 4, oy + dy - 1, 8, 3))


def draw_crew(surf, ship, ox, oy, t, selected=(), visible_sides=('player', 'enemy')):
    for c in sorted(ship.crew, key=lambda c: c.y):
        if not c.alive or c.side not in visible_sides:
            continue
        frame = int(c.walk_t * 6) % 2 if c.moving else 0
        bob = -1 if (c.moving and frame) else 0
        if c.task == 'fight':
            bob = -1 if int(t * 8 + c.uid) % 2 else 0
        flip = (c.side == 'enemy')
        spr = gfx.crew_sprite(c.cls, c.skin, frame, flip)
        wob = 0
        if c.cls == 'drunk':
            wob = int(round(math.sin(c.anim * 2.3) * 1.2))
        x = int(ox + c.x - 4 + wob)
        y = int(oy + c.y - 6 + bob)
        if c in selected:
            pygame.draw.rect(surf, P['green'], (x - 2, y - 2, 12, 14), 1)
        surf.blit(spr, (x, y))
        if c.task == 'fight' and int(t * 6) % 2:
            surf.set_at((x + (9 if not flip else -2), y + 5), P['white'])
            surf.set_at((x + (10 if not flip else -3), y + 4), P['white'])
        if c.task in ('repair', 'patch', 'fire') and int(t * 4 + c.uid) % 2:
            surf.set_at((x + 4, y - 3), P['yellow'])
        if c.hp < c.max_hp:
            col = P['green'] if c.side == 'player' else P['red']
            gfx.bar(surf, x - 1, y - 4, 10, 2, c.hp / c.max_hp, col)


def draw_barks(surf, ship, ox, oy, visible_sides=('player', 'enemy')):
    for c in ship.crew:
        if c.alive and c.bark and c.bark_t > 0 and c.side in visible_sides:
            img = gfx.render(c.bark, 14, P['ink'])
            w = img.get_width() + 6
            x = int(ox + c.x - w // 2)
            y = int(oy + c.y - 22)
            x = max(2, min(x, 640 - w - 2))
            r = pygame.Rect(x, y, w, img.get_height() + 2)
            pygame.draw.rect(surf, P['white'], r)
            pygame.draw.rect(surf, P['ink'], r, 1)
            pygame.draw.line(surf, P['white'], (ox + c.x, r.bottom), (ox + c.x, r.bottom + 3))
            surf.blit(img, (r.left + 3, r.top + 2))


def room_at(ship, ox, oy, pos):
    x, y = pos[0] - ox, pos[1] - oy
    for r in ship.rooms:
        if r.contains(x, y):
            return r.idx
    return None


def crew_at(ship, ox, oy, pos, side='player'):
    for c in ship.crew:
        if c.alive and c.side == side and abs(ox + c.x - pos[0]) <= 5 and -8 <= (oy + c.y - pos[1]) <= 7:
            return c
    return None
