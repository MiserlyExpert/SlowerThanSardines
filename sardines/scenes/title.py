"""Title and help screens."""
import math

import pygame

from .. import audio, gfx, model, render
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
        from .hangar import HangarScene
        self.app.reset(HangarScene(self.app))

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
        audio.set_mood('title')
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
        gfx.draw_sea(s, t, top=150)
        pygame.draw.line(s, P["foam"], (0, 150), (W, 150))
        ox = W // 2 - self.ship.gw * 8 - 16
        oy = 206 - render.WATERLINE + int(math.sin(t * 1.3) * 2)
        render.draw_ship(s, self.ship, ox, oy, t)
        # title
        title_y = 26 + int(math.sin(t * 2) * 2)
        gfx.text_outline(s, "SLOWER THAN", W // 2, title_y, P['white'], 40, align='center')
        gfx.text_outline(s, "SARDINES", W // 2, title_y + 26, P['gold'], 52, align='center')
        gfx.text(s, "a roguelike about fish, freedom and taxes", W // 2, title_y + 62, P['ink'], align='center')
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, mouse)
        gfx.text(s, f"v{VERSION}    F11 fullscreen    M music", W - 6, H - 12, P['lblue'], align='right')


HELP = [
    ("THE GOAL", "You are the Free Fishers, rebels against the Sardine Tax. Sail five seas and sink HMS "
                 "Insufferable, the Crown's gigantic flagship. The Royal Armada is chasing you the whole way."),
    ("THE CHART", "Click a connected waypoint to sail there. Each leg costs 1 Rum. Fog banks take 2 days to "
                  "cross, so the Armada gains twice as fast. Reach the far right of each sea to move on."),
    ("BATTLE", "SPACE pauses. Click a cannon (or press 1-4), then click an enemy room to aim. Cannons fire "
               "by themselves when loaded. Right-click a cannon to unpower it."),
    ("CREW", "Click crew to select (Shift adds, A selects all). Right-click a room to send them. Crew man "
             "stations, repair them, fight fires and patch holes in the hull."),
    ("HANDS", "Your crew's Hands work the stations. Click a station to give it a Hand, right-click to take "
              "one away. Lose crew and you lose their Hands."),
    ("BOARDING", "Needs an Armory (install one at a port shipyard). Send crew to your TOP DECK, select "
                 "them and press Board. They land on the enemy's top deck and fight their way down. "
                 "Recall brings home anyone standing on the enemy's top deck."),
    ("PORTS", "Islands on the chart have harbors: buy supplies and cannons, trade goods between ports, "
              "hire crew, and upgrade any room or fit modules into empty slots."),
    ("TIPS", "Captains belong at the Helm. Drunks belong on the Gun Deck, and in any fistfight. "
             "Holes in the hull drain it slowly: patch them. Pirates are everywhere and like nobody."),
]


class HelpScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.btn = gfx.Button((W // 2 - 50, 320, 100, 22), "Got it", self.app.pop, key=pygame.K_ESCAPE)

    def handle(self, e):
        self.btn.handle(e)

    def draw(self, s):
        gfx.dim(s)
        gfx.panel(s, (50, 14, W - 100, 336), 'parch')
        gfx.text(s, "HOW TO PLAY", W // 2, 26, P['dred'], 24, align='center')
        y = 52
        for head, body in HELP:
            gfx.text(s, head, 68, y, P['dred'])
            y = gfx.paragraph(s, body, 140, y, W - 210, P['ink'])
            y += 4
        self.btn.draw(s, pygame.mouse.get_pos())
