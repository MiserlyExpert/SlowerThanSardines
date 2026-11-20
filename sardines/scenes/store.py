"""Port market."""
import random

import pygame

from .. import audio, data, gfx
from ..app import Scene
from ..config import H, MAX_CREW, W
from ..gfx import P
from .hud import draw_resources, tooltip

QUIPS = [
    "'Everything's for sale. Except the parrot. The parrot is for rent.'",
    "'No refunds. No returns. No questions. Especially no questions.'",
    "'Cannonballs! Get yer cannonballs! Gently used! Fired only once!'",
    "'Rum's fresh. Fresh-ish. It was fresh at one point, definitely.'",
]
HIRE_PRICE = dict(captain=70, drunk=45, deckhand=40, monkey=40, carpenter=50, surgeon=50, cook=50)


def gen_store(gs):
    rng = gs.rng
    weapons = rng.sample(sorted(set(data.LOOT_WEAPONS)), 3)
    hires = [rng.choice(data.HIREABLE) for _ in range(2)]
    from ..model import Crew
    return dict(weapons=[dict(key=k, sold=False) for k in weapons],
                hires=[dict(crew=Crew(c, side='player', rng=rng), sold=False) for c in hires],
                quip=rng.choice(QUIPS))


class StoreScene(Scene):
    overlay = True

    def __init__(self, app, node):
        super().__init__(app)
        if node.store is None:
            node.store = gen_store(self.gs)
        self.store = node.store
        self.msg = self.store['quip']
        self.tip = None
        self.build()

    def buy(self, price, fn):
        if self.gs.doubloons < price:
            self.msg = "'Come back when you've got the coin, sunshine.'"
            return
        res = fn()
        if res is False:
            return
        self.gs.doubloons -= price
        audio.play('win')
        self.build()

    def build(self):
        gs = self.gs
        ship = gs.ship
        self.buttons = []
        self.tips = []
        x, y = 40, 70
        missing = ship.hull_max - ship.hull

        def add(label, price, fn, ok=True, tip=None, col=0):
            nonlocal y
            bx = 40 if col == 0 else 330
            by = y if col == 0 else self._y2
            b = gfx.Button((bx, by, 270, 20), f"{label}  -  {price}g", lambda: self.buy(price, fn),
                           enabled=ok and gs.doubloons >= price, size=16)
            self.buttons.append(b)
            if tip:
                self.tips.append((b.rect, tip))
            if col == 0:
                y += 24
            else:
                self._y2 += 24

        def addv(attr, n):
            def f():
                setattr(gs, attr, getattr(gs, attr) + n)
            return f

        def repair(n):
            def f():
                ship.hull = min(ship.hull_max, ship.hull + n)
            return f

        self._y2 = 70
        add("1 Rum", 4, addv('rum', 1))
        add("5 Rum", 18, addv('rum', 5))
        add("1 Cannonball", 6, addv('balls', 1))
        add("4 Cannonballs", 20, addv('balls', 4))
        add("Patch 1 Hull", 3, repair(1), ok=missing > 0)
        if missing > 1:
            add(f"Repair all hull (+{missing})", 3 * missing - missing // 4, repair(missing))
        for item in self.store['weapons']:
            d = data.WEAPONS[item['key']]
            if item['sold']:
                continue

            def bw(item=item):
                gs.add_weapon(item['key'])
                item['sold'] = True
            add(f"{d['name']}", d['cost'], bw, col=1, tip=f"{d['name']}: {d['desc']} "
                f"{d['shots']} shot(s), {d['dmg']} dmg, {d['charge']:.0f}s, {d['power']} power.")
        for item in self.store['hires']:
            c = item['crew']
            if item['sold']:
                continue

            def bh(item=item):
                if len(gs.crew) >= MAX_CREW:
                    self.msg = "'Your ship's full, mate. Any more and she'll sink.'"
                    return False
                gs.ship.place(item['crew'], None, gs.rng)
                item['sold'] = True
            add(f"Hire {c.name} ({c.title})", HIRE_PRICE.get(c.cls, 45), bh, col=1, tip=c.d['desc'],
                ok=len(gs.crew) < MAX_CREW)
        self.buttons.append(gfx.Button((W // 2 - 60, H - 34, 120, 22), "Leave port", self.leave,
                                       key=pygame.K_ESCAPE))

    def leave(self):
        self.gs.sector.node.cleared = True
        self.app.pop()

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def draw(self, s):
        gfx.dim(s, 160)
        gfx.panel(s, (20, 30, W - 40, H - 40), 'parch')
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        draw_resources(s, self.gs)
        gfx.text(s, "PORT MARKET", W // 2, 36, P['dred'], 24, align='center')
        gfx.text(s, self.msg, W // 2, 54, P['ink'], 16, align='center')
        gfx.text(s, f"Hull {self.gs.ship.hull}/{self.gs.ship.hull_max}   Crew {len(self.gs.crew)}/{MAX_CREW}   "
                 f"Cannons {len(self.gs.ship.weapons)}/4 (extras go to the hold)", W // 2, H - 52, P['ink'], 14,
                 align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
        for rect, tip in self.tips:
            if rect.collidepoint(m):
                tooltip(s, tip, m, 220)
