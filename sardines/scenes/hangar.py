"""Choose your ship and starting crew (like FTL's hangar)."""
import math
import random

import pygame

from .. import audio, data, gfx, model, profile, render
from ..app import Scene
from ..config import H, T, W
from ..gfx import P
from .hud import tooltip


SLOT = 84


class HangarScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.idx = 0
        self.rng = random.Random()
        self.crew = []
        self.preview = None
        self.select(0)

    # ------------------------------------------------------------------
    @property
    def key(self):
        return data.SHIP_ORDER[self.idx]

    @property
    def d(self):
        return data.SHIPS[self.key]

    @property
    def unlocked(self):
        return profile.is_unlocked(self.key)

    def allowed(self):
        return data.BASE_CREW + self.d.get('extra_crew', [])

    def select(self, idx):
        self.idx = idx % len(data.SHIP_ORDER)
        self.crew = list(self.d['crew'])
        self.skins = [self.rng.randrange(4) for _ in self.crew]
        self._rebuild()

    def _rebuild(self):
        self.preview = model.make_player_ship(random.Random(3), self.key, self.crew)
        for c, sk in zip(self.preview.crew, self.skins):
            c.skin = sk
        self.buttons = [
            gfx.Button((14, 70, 22, 40), "<", lambda: self.select(self.idx - 1), key=pygame.K_LEFT),
            gfx.Button((W - 36, 70, 22, 40), ">", lambda: self.select(self.idx + 1), key=pygame.K_RIGHT),
            gfx.Button((W - 150, H - 32, 136, 24), "Set Sail!", self.start, enabled=self.unlocked,
                       key=pygame.K_RETURN),
            gfx.Button((14, H - 32, 90, 24), "Back", self.back, key=pygame.K_ESCAPE),
        ]
        x0 = self.crew_x0()
        for i in range(len(self.crew)):
            x = x0 + i * SLOT
            self.buttons.append(gfx.Button((x, 266, 16, 16), "<", lambda i=i: self.cycle(i, -1),
                                           enabled=self.unlocked, size=14))
            self.buttons.append(gfx.Button((x + 64, 266, 16, 16), ">", lambda i=i: self.cycle(i, 1),
                                           enabled=self.unlocked, size=14))

    def crew_x0(self):
        n = len(self.crew)
        return W // 2 - (n * SLOT - 4) // 2

    def cycle(self, i, step):
        opts = self.allowed()
        cur = self.crew[i]
        j = opts.index(cur) if cur in opts else 0
        self.crew[i] = opts[(j + step) % len(opts)]
        self.skins[i] = self.rng.randrange(4)
        self._rebuild()

    def start(self):
        from ..events import INTRO
        from ..state import GameState
        from .event import EventScene
        from .map import MapScene
        profile.record(voyages=1)
        self.app.gs = GameState(ship_key=self.key, crew=list(self.crew))
        self.app.reset(MapScene(self.app))
        self.app.push(EventScene(self.app, INTRO))

    def back(self):
        from .title import TitleScene
        self.app.reset(TitleScene(self.app))

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt
        for c in self.preview.crew:
            c.anim += dt

    # ------------------------------------------------------------------
    def draw(self, s):
        t, d, ship = self.t, self.d, self.preview
        for y in range(26, 120):
            k = (y - 26) / 94
            pygame.draw.line(s, (int(110 + 80 * k), int(160 + 60 * k), int(205 + 30 * k)), (0, y), (W, y))
        gfx.draw_sea(s, t, 120)
        pygame.draw.rect(s, P['navy'], (0, 0, W, 26))
        pygame.draw.line(s, P['black'], (0, 26), (W, 26))
        gfx.text(s, "THE SHIPYARD", 10, 7, P['gold'], 24)
        n_un = sum(1 for k in data.SHIP_ORDER if profile.is_unlocked(k))
        gfx.text(s, f"Ships unlocked: {n_un}/{len(data.SHIP_ORDER)}", W - 10, 10, P['lgrey'], align='right')

        dots = len(data.SHIP_ORDER)
        for i in range(dots):
            col = P['gold'] if i == self.idx else (P['lgrey'] if profile.is_unlocked(data.SHIP_ORDER[i]) else P['dgrey'])
            pygame.draw.rect(s, col, (W // 2 - dots * 6 + i * 12, 56, 8, 3))
        # the ship
        ox = W // 2 - (ship.gw * T) // 2 - 16
        oy = 138 - render.WATERLINE + int(math.sin(t * 1.3) * 1.5)
        render.draw_ship(s, ship, ox, oy, t, crew_sides=('player',) if self.unlocked else ())
        if not self.unlocked:
            sh = pygame.Surface((W, 150), pygame.SRCALPHA)
            sh.fill((5, 10, 20, 170))
            s.blit(sh, (0, 62))
            gfx.text(s, "LOCKED", W // 2 + 2, 98, P['black'], 40, align='center')
            gfx.text(s, "LOCKED", W // 2, 96, P['red'], 40, align='center')
            gfx.text(s, "To unlock: " + d['unlock'][2], W // 2, 128, P['white'], align='center')
        # ship name plate, over the masts
        gfx.text_outline(s, d['name'].upper(), W // 2, 34, P['white'] if self.unlocked else P['grey'], 24,
                         align='center')
        # info panel
        gfx.panel(s, (14, 202, W - 28, 116), 'parch')
        gfx.paragraph(s, d['blurb'], 26, 210, 300, P['ink'])
        y = 210
        stats = [("Hull", d['hull']), ("Hands", self.preview.gusto), ("Rum", d['rum']), ("Balls", d['balls'])]
        x = 350
        for k, v in stats:
            x += gfx.text(s, k, x, y, P['wood2']) + 3
            x += gfx.text(s, str(v), x, y, P['ink']) + 10
        y = 221
        for wk in d['weapons'][:3]:
            wd = data.WEAPONS[wk]
            gfx.text(s, wd['name'], 350, y, P['ink'])
            x = 450
            for tag in data.weapon_tags(wd)[:3]:
                x += draw_tag(s, tag, x, y) + 3
            y += 9
        gfx.text(s, "STARTING CREW: use the arrows to choose", 26, 236, P['dred'])
        x0 = self.crew_x0()
        m = pygame.mouse.get_pos()
        tip = None
        for i, cls in enumerate(self.crew):
            x = x0 + i * SLOT
            r = gfx.portrait(s, cls, self.skins[i], x + 21, 248, 3, t=t)
            gfx.text(s, data.CREW[cls]['title'], x + 40, 302, P['ink'], align='center')
            if r.collidepoint(m):
                tip = f"{data.CREW[cls]['title']}, {data.HANDS.get(cls, 3)} Hands. {data.CREW[cls]['desc']}"
        for b in self.buttons:
            b.draw(s, m)
        if tip:
            tooltip(s, tip, m, 200)


def draw_tag(s, tag, x, y):
    col = gfx.hexc(data.TAG_COLORS.get(tag, '#a8743f'))
    w = gfx.text_w(tag) + 4
    pygame.draw.rect(s, col, (x, y - 1, w, 9))
    gfx.text(s, tag, x + 2, y, P['white'])
    return w
