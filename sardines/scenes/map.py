"""The sea chart."""
import math
import random

import pygame

from .. import audio, gfx
from ..app import Scene
from ..config import H, W
from ..gfx import P
from ..sector import FLEET_STEP
from .hud import draw_resources, tooltip

KIND_TIP = {
    'start': "Where you came in.",
    'event': "Unknown waters. Could be anything. Probably crabs.",
    'distress': "Distress signal! Someone needs help (or wants you to think so).",
    'port': "An island harbor: market, trade, tavern and shipyard. Nobody asks questions. Nobody pays taxes.",
    'exit': "The way onward to the next sea.",
}
TRAVEL_TIME = 1.6
TOP, BOTTOM = 26, H - 30


class MapScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.hover = None
        self.travel = None
        self.facing = 1
        self.wake = []
        self.buttons = [
            gfx.Button((W - 230, H - 25, 108, 20), "Ship & Cargo [S]", self.shipwright, key=pygame.K_s),
            gfx.Button((W - 116, H - 25, 110, 20), "How to Play [H]", self.help, key=pygame.K_h),
        ]
        self._doodles = None

    # ------------------------------------------------------------------
    def shipwright(self):
        from .shipwright import ShipwrightScene
        self.app.push(ShipwrightScene(self.app))

    def help(self):
        from .title import HelpScene
        self.app.push(HelpScene(self.app))

    def handle(self, e):
        if self.travel:
            return
        for b in self.buttons:
            if b.handle(e):
                return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.push(PauseMenu(self.app))
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            n = self.node_at(e.pos)
            if n is not None and self.gs.can_jump(n):
                audio.play('bell')
                a = self.gs.sector.nodes[self.gs.sector.cur]
                b = self.gs.sector.nodes[n]
                if b.x != a.x:
                    self.facing = 1 if b.x > a.x else -1
                self.travel = (self.gs.sector.cur, n, 0.0)

    def node_at(self, pos):
        for nd in self.gs.sector.nodes:
            if math.hypot(nd.x - pos[0], nd.y - pos[1]) <= 10:
                return nd.idx
        return None

    def boat_pos(self):
        sec = self.gs.sector
        if self.travel:
            a, b, tt = self.travel
            na, nb = sec.nodes[a], sec.nodes[b]
            k = tt / TRAVEL_TIME
            k = k * k * (3 - 2 * k)  # ease in and out
            return na.x + (nb.x - na.x) * k, na.y + (nb.y - na.y) * k
        return sec.node.x, sec.node.y

    def update(self, dt):
        self.t += dt
        audio.set_mood('sea')
        self.hover = self.node_at(pygame.mouse.get_pos())
        for w in self.wake:
            w[2] -= dt
        self.wake = [w for w in self.wake if w[2] > 0]
        if self.travel:
            a, b, tt = self.travel
            tt += dt
            x, y = self.boat_pos()
            if int(tt * 14) != int((tt - dt) * 14):
                self.wake.append([x - 9 * self.facing, y + 2, 1.4])
            if tt >= TRAVEL_TIME:
                self.travel = None
                self.arrive(b)
            else:
                self.travel = (a, b, tt)

    def arrive(self, idx):
        from .event import EventScene
        from .endings import GameOverScene
        ev, notes = self.gs.jump(idx)
        if not self.gs.crew:
            self.gs.cause = 'sober'
            self.app.push(GameOverScene(self.app))
            return
        if ev.get('id') == 'port':
            from .harbor import HarborScene
            self.app.push(HarborScene(self.app, self.gs.sector.node))
            if notes:
                self.app.push(EventScene(self.app, dict(id='portnotes', text="You sail into the harbor.",
                                                        choices=[dict(text="Tie up at the dock.", out={})]),
                                         notes=notes))
            return
        self.app.push(EventScene(self.app, ev, notes=notes))

    # ------------------------------------------------------------------
    def _draw_chart(self, s, sec, t):
        s.fill(P['parch'])
        for x in range(0, W, 32):
            pygame.draw.line(s, P['parch2'], (x, TOP), (x, BOTTOM))
        for y in range(TOP + 6, BOTTOM, 32):
            pygame.draw.line(s, P['parch2'], (0, y), (W, y))
        if self._doodles is None or self._doodles[0] != sec.idx:
            rng = random.Random(sec.idx * 13 + 5)
            self._doodles = (sec.idx, [(rng.randint(10, W - 24), rng.randint(TOP + 22, BOTTOM - 10),
                                        rng.random() * 6) for _ in range(46)])
        # doodled waves that gently roll
        for x, y, ph in self._doodles[1]:
            dx = math.sin(t * 0.7 + ph) * 3
            a = math.sin(t * 2 + ph)
            pts = [(x + dx + i * 3, y + (a if i % 2 else -a) * 1.5) for i in range(5)]
            pygame.draw.lines(s, P['parch3'], False, pts)
        # compass rose
        cx, cy = 34, BOTTOM - 30
        pygame.draw.circle(s, P['parch3'], (cx, cy), 15, 1)
        pygame.draw.polygon(s, P['dred'], [(cx, cy - 14), (cx + 3, cy), (cx - 3, cy)])
        pygame.draw.polygon(s, P['ink'], [(cx, cy + 14), (cx + 3, cy), (cx - 3, cy)])
        pygame.draw.polygon(s, P['ink'], [(cx - 14, cy), (cx, cy - 3), (cx, cy + 3)])
        pygame.draw.polygon(s, P['ink'], [(cx + 14, cy), (cx, cy - 3), (cx, cy + 3)])
        gfx.text(s, "N", cx - 2, cy - 25, P['dred'])

    def draw(self, s):
        gs = self.gs
        sec = gs.sector
        t = self.t
        self._draw_chart(s, sec, t)
        # fog banks
        for cx, cy, r in sec.fogs:
            fr = random.Random(cx * 7 + cy)
            fog = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
            for _ in range(14):
                dx, dy = fr.randint(-r // 2, r // 2), fr.randint(-r // 2, r // 2)
                rr = fr.randint(r // 2, r - 4)
                drift = int(math.sin(t * 0.6 + dx) * 3)
                pygame.draw.circle(fog, (150, 160, 175, 50), (r + 15 + dx + drift, r + 15 + dy), rr)
            s.blit(fog, (cx - r - 15, cy - r - 15))
            gfx.text(s, "fog", cx, cy - 4, (120, 128, 140), align='center')
        # the Royal Armada
        fx = int(sec.fleet_x)
        if fx > 0:
            band = pygame.Surface((fx + 12, BOTTOM - TOP), pygame.SRCALPHA)
            band.fill((38, 56, 140, 60))
            for y in range(0, BOTTOM - TOP, 6):
                jag = int(math.sin(t * 2 + y * 0.3) * 4)
                pygame.draw.rect(band, (38, 56, 140, 60), (fx, y, 6 + jag, 6))
            s.blit(band, (0, TOP))
            pygame.draw.line(s, P['red'], (fx, TOP), (fx, BOTTOM), 1)
            pygame.draw.line(s, P['white'], (fx - 1, TOP), (fx - 1, BOTTOM), 1)
            for y in range(TOP + 30, BOTTOM - 10, 50):
                s.blit(gfx.icon('crown'), (max(3, fx - 13), y + int(math.sin(t * 2 + y) * 2)))
            if fx > 70:
                gfx.text(s, "ROYAL ARMADA", fx - 4, TOP + 6, P['blue'], align='right')
        # routes
        nbrs = sec.neighbours()
        for a, bs in sec.edges.items():
            for b in bs:
                if a < b:
                    na, nb = sec.nodes[a], sec.nodes[b]
                    hot = (a == sec.cur or b == sec.cur) and not self.travel
                    col = P['ink'] if hot else P['parch3']
                    d = math.hypot(nb.x - na.x, nb.y - na.y)
                    steps = max(2, int(d / 5))
                    off = (t * 4) % 2 if hot else 0
                    for i in range(0, steps, 2):
                        k0, k1 = (i + off) / steps, min(1, (i + 1 + off) / steps)
                        pygame.draw.line(s, col, (na.x + (nb.x - na.x) * k0, na.y + (nb.y - na.y) * k0),
                                         (na.x + (nb.x - na.x) * k1, na.y + (nb.y - na.y) * k1), 2 if hot else 1)
        # islands with harbors
        for nd in sec.nodes:
            if nd.kind == 'port' and nd.store is None:
                from .harbor import gen_port
                nd.store = gen_port(gs)
            if nd.kind == 'port':
                self._island(s, nd.x, nd.y, t, nd.idx)
        # waypoints
        for nd in sec.nodes:
            reach = nd.idx in nbrs and not self.travel
            r = 6 + (int(abs(math.sin(t * 3)) * 2) if reach else 0)
            col = P['parch3'] if nd.visited else P['white']
            if sec.overrun(nd):
                col = (150, 170, 220)
            pygame.draw.circle(s, P['ink'], (nd.x, nd.y), r + 1)
            pygame.draw.circle(s, col, (nd.x, nd.y), r)
            if nd.kind == 'port':
                s.blit(gfx.icon('anchor'), (nd.x - 3, nd.y - 3))
                if nd.store and 'name' in nd.store:
                    gfx.text(s, nd.store['name'], nd.x, nd.y + 14, P['ink'], align='center')
            elif nd.kind == 'exit':
                lbl = "EXIT" if not sec.final else "HMS INSUFFERABLE"
                gfx.text(s, lbl, min(nd.x, W - 4), nd.y - 18, P['dred'], align='right' if sec.final else 'center')
                pygame.draw.polygon(s, P['dred'], [(nd.x - 3, nd.y - 4), (nd.x + 4, nd.y), (nd.x - 3, nd.y + 4)])
            elif nd.kind == 'distress' and not nd.visited:
                gfx.text(s, "!", nd.x, nd.y - 3, P['dred'], align='center')
            elif not nd.visited and nd.kind == 'event':
                gfx.text(s, "?", nd.x + 1, nd.y - 3, P['ink'], align='center')
            if self.hover == nd.idx:
                pygame.draw.circle(s, P['dred'], (nd.x, nd.y), r + 4, 1)
        # wake left on the chart
        for x, y, life in self.wake:
            k = life / 1.4
            col = P['parch3'] if k < 0.5 else P['ink']
            pygame.draw.line(s, col, (x - 2, y + (1 - k) * 2), (x + 1, y - (1 - k)))
        # our ship
        bx, by = self.boat_pos()
        gfx.draw_boat(s, int(bx), int(by - 6), self.facing, t)
        self._bars(s, gs, sec, nbrs)

    def _island(self, s, x, y, t, seed):
        rng = random.Random(seed * 31 + 7)
        w = rng.randint(30, 40)
        # shallows, beach, grass
        pygame.draw.ellipse(s, (150, 196, 200), (x - w // 2 - 6, y - 8, w + 12, 22))
        pygame.draw.ellipse(s, (226, 204, 150), (x - w // 2, y - 6, w, 16))
        pygame.draw.ellipse(s, (110, 160, 90), (x - w // 2 + 4, y - 8, w - 8, 10))
        # a palm tree and two little houses
        px = x - w // 2 + 6
        pygame.draw.line(s, P['wood1'], (px, y - 4), (px + 2, y - 16), 2)
        for a in range(4):
            ang = -2.8 + a * 0.75 + math.sin(t + a) * 0.08
            pygame.draw.line(s, (50, 120, 60), (px + 2, y - 16), (px + 2 + math.cos(ang) * 7, y - 15 + math.sin(ang) * 4))
        for hx, col in ((x + 6, (180, 70, 50)), (x + 13, (70, 90, 140))):
            pygame.draw.rect(s, (236, 220, 190), (hx - 3, y - 10, 6, 5))
            pygame.draw.polygon(s, col, [(hx - 4, y - 10), (hx, y - 14), (hx + 4, y - 10)])
        # dock
        pygame.draw.line(s, P['wood1'], (x + w // 2 - 4, y + 4), (x + w // 2 + 6, y + 4), 2)

    def _bars(self, s, gs, sec, nbrs):
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        pygame.draw.line(s, P['black'], (0, 24), (W, 24))
        draw_resources(s, gs)
        gfx.text(s, f"SEA {sec.idx + 1}/5  {sec.name.upper()}", W - 8, 9, P['gold'], align='right')
        gfx.text(s, sec.blurb, 8, TOP + 5, P['ink'])
        pygame.draw.rect(s, P['navy'], (0, BOTTOM, W, H - BOTTOM))
        pygame.draw.line(s, P['black'], (0, BOTTOM), (W, BOTTOM))
        x = 8
        for c in gs.crew:
            from .. import people
            s.blit(people.sprite(c.cls, c.skin, 'stand', 0, 1), (x - 3, BOTTOM + 3))
            gfx.bar(s, x - 1, BOTTOM + 25, 10, 2, c.hp / c.max_hp, P['green'] if c.hp > c.max_hp * .35 else P['red'])
            x += 14
        days = (sec.node.x - sec.fleet_x) / FLEET_STEP
        tide = "THE ARMADA IS HERE!" if days <= 0 else f"Armada ~{max(1, int(days))} day{'s' if days >= 2 else ''} behind"
        gfx.text(s, f"Hands {gs.ship.gusto}   Crew {len(gs.crew)}/8   Cargo {gs.cargo_used()}/{gs.cargo_cap()}",
                 x + 8, BOTTOM + 6, P['lgrey'])
        gfx.text(s, tide, x + 8, BOTTOM + 17, P['red'] if days < 2 else P['lgrey'])
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, mouse)
        if self.hover is not None and not self.travel:
            nd = sec.nodes[self.hover]
            lines = [KIND_TIP.get(nd.kind, '')] if not nd.visited or nd.kind in ('port', 'exit') else ["Visited."]
            if nd.fog:
                lines.append("FOG BANK: takes 2 days to cross. Evasion halved in battle.")
            if sec.overrun(nd):
                lines.append("Overrun by the Royal Armada! Expect a frigate.")
            if self.hover in nbrs:
                lines.append("Click to sail here (1 Rum)." if gs.rum else "Click to sail here SOBER (no rum!).")
            elif self.hover != sec.cur:
                lines.append("Too far. Sail to a connected waypoint.")
            tooltip(s, ' '.join(lines), mouse, 210)


class PauseMenu(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        cx = W // 2
        self.buttons = [
            gfx.Button((cx - 70, 146, 140, 22), "Resume", self.app.pop, key=pygame.K_ESCAPE),
            gfx.Button((cx - 70, 174, 140, 22), "Quit to Title", self.title),
            gfx.Button((cx - 70, 202, 140, 22), "Quit Game", self.quit),
        ]

    def title(self):
        from .title import TitleScene
        self.app.reset(TitleScene(self.app))

    def quit(self):
        self.app.running = False

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def draw(self, s):
        gfx.dim(s)
        gfx.panel(s, (W // 2 - 90, 108, 180, 128), 'parch')
        gfx.text(s, "PAUSED", W // 2, 120, P['ink'], 24, align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
