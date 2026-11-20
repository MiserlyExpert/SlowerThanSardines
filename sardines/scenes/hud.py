"""Shared HUD pieces."""
import pygame

from .. import gfx
from ..gfx import P


def draw_resources(surf, gs, x=8, y=8):
    ship = gs.ship
    gfx.text(surf, "HULL", x, y, P['white'], shadow=P['black'])
    px = x + 26
    per = 4 if ship.hull_max <= 34 else 3
    for i in range(ship.hull_max):
        col = P['green'] if i < ship.hull else P['dgrey']
        if i < ship.hull and ship.hull <= ship.hull_max * 0.33:
            col = P['red']
        elif i < ship.hull and ship.hull <= ship.hull_max * 0.66:
            col = P['yellow']
        pygame.draw.rect(surf, col, (px + i * (per + 1), y - 1, per, 9))
    px += ship.hull_max * (per + 1) + 12
    for ic, val in (('coin', gs.doubloons), ('rum', gs.rum), ('ball', gs.balls)):
        surf.blit(gfx.icon(ic), (px, y + 1))
        gfx.text(surf, str(val), px + 9, y, P['white'], shadow=P['black'])
        px += 9 + gfx.text_w(str(val)) + 12
    return px


def tooltip(surf, lines, pos, width=200):
    if isinstance(lines, str):
        lines = gfx.wrap(lines, width - 10)
    lh = gfx.LINE + 1
    h = len(lines) * lh + 8
    w = max(gfx.text_w(l) for l in lines) + 12 if lines else 20
    x, y = pos[0] + 12, pos[1] + 12
    if x + w > 638:
        x = pos[0] - w - 6
    if y + h > 358:
        y = pos[1] - h - 6
    gfx.panel(surf, (x, y, w, h), 'dark')
    for i, l in enumerate(lines):
        gfx.text(surf, l, x + 6, y + 5 + i * lh, P['white'])
