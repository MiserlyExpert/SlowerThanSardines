"""Game over and victory."""
import math
import random

import pygame

from .. import audio, gfx
from ..app import Scene
from ..config import H, W
from ..gfx import P

EPITAPHS = {
    'sunk': [
        "The HMS Questionable Decisions has made her final questionable decision.",
        "Your ship is now a reef. The fish are thrilled. The Queen is not.",
        "Down she went, napkin and all. Somewhere, a pirate is drying it on a radiator.",
    ],
    'crew': [
        "Your crew has gone to the great tavern in the sky. The ship sails on, empty, forever.",
        "With no one left aboard, the ship drifts. A seagull takes command. It does fine.",
    ],
    'sober': [
        "With no rum and no crew left standing, the ship drifts to a halt. Sobriety: deadlier than cannons.",
    ],
}


class GameOverScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.text = random.choice(EPITAPHS.get(self.gs.cause or 'sunk', EPITAPHS['sunk']))
        self.buttons = [gfx.Button((W // 2 - 130, 300, 120, 22), "New Voyage", self.again, key=pygame.K_RETURN),
                        gfx.Button((W // 2 + 10, 300, 120, 22), "Title Screen", self.title,
                                   key=pygame.K_ESCAPE)]
        audio.play('lose')

    def again(self):
        from .title import TitleScene
        t = TitleScene(self.app)
        t.new_game()

    def title(self):
        from .title import TitleScene
        self.app.reset(TitleScene(self.app))

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        gfx.draw_sea(s, self.t, 0)
        gfx.dim(s, 120)
        # sad little sinking mast
        mx, my = W // 2, 230 + int(self.t * 3) % 30
        pygame.draw.line(s, P['wood1'], (mx, my), (mx, my - 40), 3)
        pygame.draw.polygon(s, P['white'], [(mx + 2, my - 38), (mx + 18, my - 14), (mx + 2, my - 14)])
        pygame.draw.rect(s, P['deep'], (0, 232, W, 40))
        gfx.text(s, "LOST AT SEA", W // 2, 50, P['red'], 52, shadow=P['black'], align='center')
        y = 100
        for line in gfx.wrap(self.text, 440, 16):
            gfx.text(s, line, W // 2, y, P['white'], 16, align='center')
            y += 12
        st = self.gs.stats
        gfx.text(s, f"Seas reached: {st['sea']}/5    Legs sailed: {st['jumps']}    Battles won: {st['wins']}    "
                 f"Doubloons plundered: {st['doubloons']}", W // 2, 150, P['gold'], 16, align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)


class VictoryScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.confetti = [[random.uniform(0, W), random.uniform(-H, 0), random.uniform(20, 50),
                          random.choice([P['gold'], P['red'], P['white'], P['blue'], P['green']])]
                         for _ in range(160)]
        self.buttons = [gfx.Button((W // 2 - 60, 316, 120, 22), "Title Screen", self.title,
                                   key=pygame.K_RETURN)]
        audio.play('win')

    def title(self):
        from .title import TitleScene
        self.app.reset(TitleScene(self.app))

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt
        for c in self.confetti:
            c[1] += c[2] * dt
            c[0] += math.sin(self.t * 2 + c[2]) * 0.3
            if c[1] > H:
                c[1] = -5

    def draw(self, s):
        s.fill(P['sky'])
        gfx.draw_sea(s, self.t, 150)
        for x, y, v, col in self.confetti:
            pygame.draw.rect(s, col, (int(x), int(y), 2, 2))
        gfx.text(s, "THE NAPKIN IS DELIVERED!", W // 2 + 2, 32, P['ink'], 40, align='center')
        gfx.text(s, "THE NAPKIN IS DELIVERED!", W // 2, 30, P['gold'], 40, align='center')
        body = ("The Leviathan's Grin sinks with a final, furious gurgle. Barnacle Vane is last seen "
                "paddling away on a barrel, shaking his fist at the sky.\n\n"
                "The Royal Armada's Admiral unfolds the napkin with trembling hands. He reads it. He turns it "
                "over. He reads it again.\n\n'It's a drinks order,' he says. 'Two rums, a grog, and something "
                "called a Sloppy Kraken.'\n\nThen he notices the tiny map scribbled in the corner, next to a "
                "drawing of a skull. The Armada sets sail at dawn. You are given a medal, a pension, and "
                "a lifetime supply of napkins.")
        lines = gfx.wrap(body, 500, 16)
        gfx.panel(s, (W // 2 - 265, 66, 530, len(lines) * 11 + 16), 'parch')
        y = 74
        for line in lines:
            gfx.text(s, line, W // 2, y, P['ink'], 16, align='center')
            y += 11
        st = self.gs.stats
        gfx.text(s, f"Legs sailed: {st['jumps']}   Battles won: {st['wins']}   Doubloons: {st['doubloons']}   "
                 f"Crew surviving: {len(self.gs.crew)}", W // 2, 296, P['gold'], 16, shadow=P['black'],
                 align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
