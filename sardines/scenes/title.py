"""Title and help screens."""
import math

import pygame

from .. import gfx, model, render
from ..app import Scene
from ..config import H, TITLE, VERSION, W
from ..gfx import P


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.ship = model.make_player_ship()
        cx = W // 2
        self.buttons = [
            gfx.Button((cx - 70, 252, 140, 22), "New Voyage", self.new_game, key=pygame.K_RETURN),
            gfx.Button((cx - 70, 278, 140, 22), "How to Play", self.help, key=pygame.K_h),
            gfx.Button((cx - 70, 304, 140, 22), "Abandon Ship", self.quit, key=pygame.K_ESCAPE),
        ]

    def new_game(self):
        from ..state import GameState
        from .map import MapScene
        from .event import EventScene
        from ..events import INTRO
        self.app.gs = GameState()
        self.app.reset(MapScene(self.app))
        self.app.push(EventScene(self.app, INTRO))

    def help(self):
        self.app.push(HelpScene(self.app))

    def quit(self):
        self.app.running = False

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt
        for c in self.ship.crew:
            c.anim += dt

    def draw(self, s):
        t = self.t
        s.fill(P['sky'])
        for i in range(5):  # clouds
            cx = int((i * 151 + t * (6 + i)) % (W + 120)) - 60
            cy = 22 + (i * 37) % 60
            for dx, r in ((0, 10), (12, 14), (26, 10), (8, 8)):
                pygame.draw.circle(s, P['white'], (cx + dx, cy), r)
        gfx.draw_sea(s, t, top=120)
        pygame.draw.line(s, P['foam'], (0, 120), (W, 120))
        ox = W // 2 - self.ship.gw * 9
        oy = 146 + int(math.sin(t * 1.3) * 2)
        render.draw_hull(s, self.ship, ox, oy, t)
        render.draw_rooms(s, self.ship, ox, oy, t)
        render.draw_crew(s, self.ship, ox, oy, t)
        # title
        title_y = 30 + int(math.sin(t * 2) * 2)
        gfx.text(s, TITLE.upper(), W // 2 + 2, title_y + 2, P['ink'], 52, align='center')
        gfx.text(s, TITLE.upper(), W // 2, title_y, P['gold'], 52, align='center')
        gfx.text(s, "a roguelike about a very important napkin", W // 2, title_y + 40, P['ink'], 16,
                 align='center')
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, mouse)
        gfx.text(s, f"v{VERSION}   F11 fullscreen   M music", W - 4, H - 12, P['lblue'], 14, align='right')


HELP = [
    ("THE GOAL", "Deliver the Napkin of Destiny to the Royal Armada, five seas away, before the Black Tide "
                 "pirate fleet catches you. Each leg of sailing costs 1 Rum."),
    ("THE CHART", "Click a connected waypoint to sail there. Fog banks take 2 days to cross, letting the "
                  "Black Tide gain twice as fast. Reach the far right of each sea to move on."),
    ("BATTLE", "SPACE pauses. Click a cannon (or press 1-4) then click an enemy room to target it. "
               "Cannons auto-fire when loaded. Right-click a cannon to unpower it."),
    ("CREW", "Left-click crew to select (Shift adds). Right-click a room on your ship to send them. "
             "Crew in a system room man it, repair it, fight fires and patch leaks."),
    ("POWER", "Gusto bars power your systems. Left-click a system bar to add power, right-click to remove."),
    ("TIPS", "Captains belong at the Helm. Drunks belong on the Gun Deck, and in any fistfight. "
             "Flooding puts out fires. Fog halves everyone's evasion."),
]


class HelpScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.btn = gfx.Button((W // 2 - 50, 322, 100, 20), "Got it", self.app.pop, key=pygame.K_ESCAPE)

    def handle(self, e):
        self.btn.handle(e)

    def draw(self, s):
        gfx.dim(s)
        gfx.panel(s, (60, 20, W - 120, 330), 'parch')
        gfx.text(s, "HOW TO PLAY", W // 2, 30, P['ink'], 24, align='center')
        y = 52
        for head, body in HELP:
            gfx.text(s, head, 76, y, P['dred'], 16)
            y += 12
            for line in gfx.wrap(body, W - 160, 16):
                gfx.text(s, line, 76, y, P['ink'], 16)
                y += 11
            y += 5
        self.btn.draw(s, pygame.mouse.get_pos())
