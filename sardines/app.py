"""Main loop and scene stack."""
import os
import sys

import pygame

from . import audio, gfx
from .config import FPS, H, TITLE, W


class Scene:
    overlay = False

    def __init__(self, app):
        self.app = app

    @property
    def gs(self):
        return self.app.gs

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


class App:
    def __init__(self):
        pygame.init()
        try:
            self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        try:
            pygame.display.set_icon(pygame.transform.scale(gfx.crew_sprite('drunk', 1), (32, 40)))
        except pygame.error:
            pass
        audio.init()
        audio.start_music()
        self.clock = pygame.time.Clock()
        self.stack = []
        self.gs = None
        self.t = 0.0
        self.running = True

    # -- stack --
    def push(self, scene):
        self.stack.append(scene)

    def pop(self):
        if self.stack:
            self.stack.pop()

    def replace(self, scene):
        self.pop()
        self.push(scene)

    def reset(self, scene):
        self.stack = [scene]

    @property
    def top(self):
        return self.stack[-1]

    def draw_below(self, scene, surf):
        i = self.stack.index(scene)
        if i > 0:
            below = self.stack[i - 1]
            if below.overlay:
                self.draw_below(below, surf)
            below.draw(surf)

    def draw(self):
        top = self.top
        if top.overlay:
            self.draw_below(top, self.screen)
        top.draw(self.screen)

    # -- loop --
    def step(self, dt, events=()):
        self.t += dt
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                audio.toggle_music()
            else:
                self.top.handle(e)
        self.top.update(dt)
        self.draw()

    def run(self):
        from .scenes.title import TitleScene
        self.push(TitleScene(self))
        while self.running and self.stack:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.step(dt, pygame.event.get())
            pygame.display.flip()
        pygame.quit()


def main():
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    App().run()
