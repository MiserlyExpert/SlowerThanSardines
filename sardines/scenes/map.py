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
    'port': "A port with a market and a tavern.",
    'exit': "The way onward to the next sea.",
}


class MapScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.hover = None
        self.travel = None
        self.buttons = [
            gfx.Button((W - 236, H - 24, 110, 20), "Shipwright (S)", self.shipwright, key=pygame.K_s),
            gfx.Button((W - 120, H - 24, 114, 20), "How to Play (H)", self.help, key=pygame.K_h),
        ]

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
                self.travel = (self.gs.sector.cur, n, 0.0)

    def node_at(self, pos):
        for nd in self.gs.sector.nodes:
            if math.hypot(nd.x - pos[0], nd.y - pos[1]) <= 9:
                return nd.idx
        return None

    def update(self, dt):
        self.t += dt
        self.hover = self.node_at(pygame.mouse.get_pos())
        if self.travel:
            a, b, tt = self.travel
            tt += dt
            if tt >= 0.7:
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
        self.app.push(EventScene(self.app, ev, notes=notes))

    # ------------------------------------------------------------------
    def draw(self, s):
        gs = self.gs
        sec = gs.sector
        t = self.t
        s.fill(P['parch'])
        for x in range(0, W, 32):
            pygame.draw.line(s, P['parch2'], (x, 26), (x, H - 30))
        for y in range(26, H - 30, 32):
            pygame.draw.line(s, P['parch2'], (0, y), (W, y))
        # little doodled waves
        rng = random.Random(sec.idx * 13)
        for _ in range(40):
            x, y = rng.randint(10, W - 20), rng.randint(40, H - 40)
            pygame.draw.lines(s, P['parch3'], False, [(x, y), (x + 3, y - 2), (x + 6, y), (x + 9, y - 2)])
        # fog banks
        for cx, cy, r in sec.fogs:
            fr = random.Random(cx * 7 + cy)
            fog = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
            for _ in range(14):
                dx, dy = fr.randint(-r // 2, r // 2), fr.randint(-r // 2, r // 2)
                rr = fr.randint(r // 2, r - 4)
                drift = int(math.sin(t * 0.6 + dx) * 3)
                pygame.draw.circle(fog, (150, 160, 175, 55), (r + 15 + dx + drift, r + 15 + dy), rr)
            s.blit(fog, (cx - r - 15, cy - r - 15))
        # the Black Tide
        fx = int(sec.fleet_x)
        if fx > 0:
            tide = pygame.Surface((fx + 12, H - 56), pygame.SRCALPHA)
            tide.fill((120, 20, 30, 70))
            for y in range(0, H - 56, 6):
                jag = int(math.sin(t * 2 + y * 0.3) * 4)
                pygame.draw.rect(tide, (120, 20, 30, 70), (fx, y, 6 + jag, 6))
            s.blit(tide, (0, 26))
            pygame.draw.line(s, P['dred'], (fx, 26), (fx, H - 30), 1)
            for y in range(50, H - 40, 60):
                s.blit(gfx.icon('skull'), (max(4, fx - 14), y + int(math.sin(t * 2 + y) * 2)))
        # edges
        nbrs = sec.neighbours()
        for a, bs in sec.edges.items():
            for b in bs:
                if a < b:
                    na, nb = sec.nodes[a], sec.nodes[b]
                    hot = (a == sec.cur or b == sec.cur)
                    col = P['ink'] if hot else P['parch3']
                    d = math.hypot(nb.x - na.x, nb.y - na.y)
                    steps = int(d / 5)
                    for i in range(0, steps, 2):
                        x1 = na.x + (nb.x - na.x) * i / steps
                        y1 = na.y + (nb.y - na.y) * i / steps
                        x2 = na.x + (nb.x - na.x) * (i + 1) / steps
                        y2 = na.y + (nb.y - na.y) * (i + 1) / steps
                        pygame.draw.line(s, col, (x1, y1), (x2, y2), 2 if hot else 1)
        # nodes
        for nd in sec.nodes:
            reach = nd.idx in nbrs
            r = 6
            if reach:
                r = 6 + int(abs(math.sin(t * 3)) * 2)
            col = P['parch3'] if nd.visited else P['white']
            if sec.overrun(nd):
                col = P['red']
            pygame.draw.circle(s, P['ink'], (nd.x, nd.y), r + 1)
            pygame.draw.circle(s, col, (nd.x, nd.y), r)
            if nd.kind == 'port':
                s.blit(gfx.icon('anchor'), (nd.x - 3, nd.y - 3))
            elif nd.kind == 'exit':
                gfx.text(s, "EXIT" if not sec.final else "ARMADA", nd.x, nd.y - 18, P['dred'], 16,
                         align='center')
                pygame.draw.polygon(s, P['dred'], [(nd.x - 3, nd.y - 4), (nd.x + 4, nd.y), (nd.x - 3, nd.y + 4)])
            elif nd.kind == 'distress' and not nd.visited:
                gfx.text(s, "!", nd.x, nd.y - 5, P['dred'], 16, align='center')
            elif not nd.visited and nd.kind == 'event':
                gfx.text(s, "?", nd.x, nd.y - 5, P['ink'], 16, align='center')
            if self.hover == nd.idx:
                pygame.draw.circle(s, P['dred'], (nd.x, nd.y), r + 4, 1)
        # player ship marker
        cur = sec.node
        px, py = cur.x, cur.y
        if self.travel:
            a, b, tt = self.travel
            na, nb = sec.nodes[a], sec.nodes[b]
            k = tt / 0.7
            px, py = na.x + (nb.x - na.x) * k, na.y + (nb.y - na.y) * k
        bob = math.sin(t * 3) * 1.5
        self._boat(s, int(px), int(py - 14 + bob))
        # top bar
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        pygame.draw.line(s, P['black'], (0, 24), (W, 24))
        draw_resources(s, gs)
        gfx.text(s, f"SEA {sec.idx + 1}/5: {sec.name.upper()}", W - 6, 6, P['gold'], 16, align='right')
        gfx.text(s, sec.blurb, 8, 28, P['ink'], 14)
        # bottom bar: crew
        pygame.draw.rect(s, P['navy'], (0, H - 28, W, 28))
        x = 6
        for c in gs.crew:
            s.blit(gfx.crew_sprite(c.cls, c.skin), (x, H - 23))
            gfx.bar(s, x - 1, H - 9, 10, 2, c.hp / c.max_hp, P['green'])
            x += 14
        days = (sec.node.x - sec.fleet_x) / FLEET_STEP
        tide = "THE BLACK TIDE IS HERE!" if days <= 0 else f"Black Tide ~{max(1, int(days))} day(s) behind"
        gfx.text(s, f"Gusto {gs.ship.gusto}   Crew {len(gs.crew)}/8", x + 6, H - 24, P['lgrey'], 14)
        gfx.text(s, tide, x + 6, H - 13, P['red'] if days < 2 else P['lgrey'], 14)
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, mouse)
        # tooltip
        if self.hover is not None and not self.travel:
            nd = sec.nodes[self.hover]
            lines = [KIND_TIP.get(nd.kind, '')] if not nd.visited or nd.kind in ('port', 'exit') else ["Visited."]
            if nd.fog:
                lines.append("FOG BANK: passage takes 2 days; evasion halved in battle.")
            if sec.overrun(nd):
                lines.append("Overrun by the Black Tide! Expect a warship.")
            if self.hover in nbrs:
                lines.append("Click to sail here (1 Rum)." if gs.rum else "Click to sail here SOBER (no rum!).")
            elif self.hover != sec.cur:
                lines.append("Too far. Sail to a connected waypoint.")
            wrapped = []
            for l in lines:
                wrapped += gfx.wrap(l, 200, 14)
            tooltip(s, wrapped, mouse)

    def _boat(self, s, x, y):
        pygame.draw.polygon(s, P['wood1'], [(x - 7, y), (x + 7, y), (x + 4, y + 4), (x - 4, y + 4)])
        pygame.draw.line(s, P['wood0'], (x, y), (x, y - 10))
        pygame.draw.polygon(s, P['white'], [(x + 1, y - 10), (x + 7, y - 2), (x + 1, y - 2)])
        pygame.draw.polygon(s, P['white'], [(x - 1, y - 8), (x - 5, y - 2), (x - 1, y - 2)])
        pygame.draw.rect(s, P['blue'], (x, y - 13, 4, 3))


class PauseMenu(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        cx = W // 2
        self.buttons = [
            gfx.Button((cx - 70, 140, 140, 22), "Resume", self.app.pop, key=pygame.K_ESCAPE),
            gfx.Button((cx - 70, 168, 140, 22), "Quit to Title", self.title),
            gfx.Button((cx - 70, 196, 140, 22), "Quit Game", self.quit),
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
        gfx.panel(s, (W // 2 - 90, 108, 180, 120), 'parch')
        gfx.text(s, "PAUSED", W // 2, 116, P['ink'], 24, align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
