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
        "The Plucky Sardine has been tinned. The Admiral has her figurehead mounted above his fireplace.",
        "Your ship is now a reef. The fish are thrilled. The tax collectors are already taxing them.",
        "Down she went. The Crown declares a national holiday. The brass band plays for six hours.",
    ],
    'crew': [
        "Your crew has gone to the great tavern in the sky. The ship drifts on, empty, still technically "
        "in arrears on her fish licence.",
        "With no one left aboard, the ship drifts. A seagull takes command. It does surprisingly well.",
    ],
    'sober': [
        "No rum, no crew left standing. Sobriety: deadlier than cannons. The Armada sends a sympathy card.",
    ],
}


class GameOverScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.text = random.choice(EPITAPHS.get(self.gs.cause or 'sunk', EPITAPHS['sunk']))
        self.buttons = [gfx.Button((W // 2 - 130, 290, 120, 22), "New Voyage", self.again, key=pygame.K_RETURN),
                        gfx.Button((W // 2 + 10, 290, 120, 22), "Title Screen", self.title,
                                   key=pygame.K_ESCAPE)]
        audio.play('lose')
        audio.set_mood('quiet')

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
        gfx.text(s, "LOST AT SEA", W // 2 + 4, 44, P['black'], 52, align='center')
        gfx.text(s, "LOST AT SEA", W // 2, 40, P['red'], 52, align='center')
        y = gfx.paragraph(s, self.text, W // 2 - 200, 92, 400, P['white'], align='center', line=12)
        st = self.gs.stats
        y += 10
        for line in (f"Seas reached: {st['sea']}/5      Legs sailed: {st['jumps']}",
                     f"Battles won: {st['wins']}      Doubloons plundered: {st['doubloons']}"):
            gfx.text(s, line, W // 2, y, P['gold'], align='center')
            y += 12
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
        self.buttons = [gfx.Button((W // 2 - 60, 322, 120, 22), "Title Screen", self.title,
                                   key=pygame.K_RETURN)]
        audio.play('win')
        audio.set_mood('title')

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
        gfx.text(s, "VIVA LA SARDINE!", W // 2 + 3, 19, P['ink'], 40, align='center')
        gfx.text(s, "VIVA LA SARDINE!", W // 2, 16, P['gold'], 40, align='center')
        body = ("HMS Insufferable goes down in a magnificent fireball, which the band plays straight through, "
                "out of professional pride. Admiral Crumpet-Smythe is last seen rowing away in a gilded "
                "lifeboat, still holding his teacup, pinky finger extended, furious.\n\n"
                "Without its flagship (and its tax office, and its ballroom) the Crown hastily repeals the "
                "Sardine Tax. Fishermen everywhere celebrate. The sardines, as usual, are not consulted.\n\n"
                "The crew of the Plucky Sardine become legends. Tavern songs are written about you. They "
                "rhyme 'sardine' with 'sardine' a lot. Nobody minds.")
        lines = gfx.wrap(body, 500)
        gfx.panel(s, (W // 2 - 262, 56, 524, len(lines) * 11 + 18), 'parch')
        y = 66
        for line in lines:
            gfx.text(s, line, W // 2, y, P['ink'], align='center')
            y += 11
        st = self.gs.stats
        gfx.text(s, f"Legs sailed: {st['jumps']}    Battles won: {st['wins']}    Doubloons: {st['doubloons']}    "
                 f"Crew surviving: {len(self.gs.crew)}", W // 2, 300, P['gold'], shadow=P['black'],
                 align='center')
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
