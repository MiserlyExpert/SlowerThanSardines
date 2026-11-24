"""Ship & Cargo: your loadout, rooms, crew and cargo. (Buying happens in port.)"""
import pygame

from .. import audio, data, gfx, model, people
from ..app import Scene
from ..config import H, MAX_WEAPONS, W
from ..gfx import P
from .hud import draw_resources, tooltip


class ShipwrightScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.build()

    def build(self):
        gs, ship = self.gs, self.gs.ship
        self.buttons, self.tips = [], []
        y = 78
        for i, w in enumerate(ship.weapons):
            b = gfx.Button((210, y, 190, 16), f"{w.name}  (stow)", lambda i=i: self.stow(i),
                           enabled=len(ship.weapons) > 1, size=14)
            self.buttons.append(b)
            self.tips.append((b.rect, f"{w.d['desc']} [{' '.join(data.weapon_tags(w.d))}] Click to move it to "
                                      f"the spares."))
            y += 19
        y = 182
        for i, key in enumerate(gs.cargo):
            d = data.WEAPONS[key]
            b = gfx.Button((210, y, 190, 16), f"{d['name']}  (fit)", lambda i=i: self.equip(i),
                           enabled=len(ship.weapons) < MAX_WEAPONS, size=14)
            self.buttons.append(b)
            self.tips.append((b.rect, d['desc']))
            y += 19
        self.buttons.append(gfx.Button((W // 2 - 50, H - 30, 100, 22), "Done", self.app.pop, key=pygame.K_ESCAPE))

    def stow(self, i):
        ship = self.gs.ship
        w = ship.weapons[i]
        ship.unpower_weapon(w)
        ship.weapons.pop(i)
        self.gs.cargo.append(w.key)
        self.build()

    def equip(self, i):
        ship = self.gs.ship
        key = self.gs.cargo.pop(i)
        w = model.Weapon(key)
        ship.weapons.append(w)
        ship.power_weapon(w)
        self.build()

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
            self.app.pop()
            return
        for b in self.buttons:
            if b.handle(e):
                return

    def draw(self, s):
        gs, ship = self.gs, self.gs.ship
        gfx.dim(s, 170)
        gfx.panel(s, (14, 28, W - 28, H - 34), 'parch')
        pygame.draw.rect(s, P['navy'], (0, 0, W, 22))
        draw_resources(s, gs, y=7)
        gfx.text(s, ship.name.upper(), W // 2, 36, P['dred'], 24, align='center')
        gfx.text(s, "Upgrades, modules, trading and hiring happen in port.", W // 2, 54, P['wood2'], align='center')
        # rooms
        gfx.text(s, "ROOMS", 26, 66, P['dred'])
        y = 78
        for r in ship.rooms:
            if r.sys:
                lvl, mx, title = ship.sys[r.sys].level, data.SYSTEMS[r.sys]['max'], data.SYSTEMS[r.sys]['title']
            elif r.kind == 'empty':
                lvl, mx, title = 0, 0, "(empty slot)"
            else:
                lvl, mx, title = r.level, data.MODULES[r.kind]['max'], data.MODULES[r.kind]['title']
            gfx.text(s, title, 26, y, P['ink'] if r.kind != 'empty' else P['parch3'])
            for i in range(mx):
                pygame.draw.rect(s, P['dgreen'] if i < lvl else P['parch2'], (130 + i * 7, y + 2, 5, 4))
            y += 11
        # cannons
        gfx.text(s, f"CANNONS FITTED ({len(ship.weapons)}/{MAX_WEAPONS})", 210, 66, P['dred'])
        gfx.text(s, "SPARE CANNONS", 210, 170, P['dred'])
        if not gs.cargo:
            gfx.text(s, "None.", 210, 182, P['parch3'])
        # cargo
        gfx.text(s, f"CARGO ({gs.cargo_used()}/{gs.cargo_cap()})", 420, 66, P['dred'])
        y = 78
        for k, g in data.GOODS.items():
            s.blit(gfx.icon(k), (420, y))
            gfx.text(s, f"{g['title']}: {gs.goods[k]}", 432, y, P['ink'] if gs.goods[k] else P['parch3'])
            y += 11
        # crew
        gfx.text(s, f"CREW ({len(gs.crew)}/8)  Hands {ship.gusto}", 420, 134, P['dred'])
        y = 146
        for c in gs.crew:
            s.blit(people.sprite(c.cls, c.skin, 'stand', 0, 1), (420, y - 6))
            gfx.text(s, f"{c.name}", 438, y, P['ink'])
            gfx.text(s, f"{c.title}, {data.HANDS.get(c.cls, 3)} Hands", 438, y + 9, P['wood2'])
            gfx.bar(s, 560, y + 4, 50, 3, c.hp / c.max_hp, P['dgreen'] if c.hp > c.max_hp * .35 else P['red'])
            y += 22
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
        for rect, tip in self.tips:
            if rect.collidepoint(m):
                tooltip(s, tip, m, 220)
