"""Upgrades, cannon loadout and crew roster."""
import pygame

from .. import audio, data, gfx, model
from ..app import Scene
from ..config import H, MAX_WEAPONS, W
from ..gfx import P
from .hud import draw_resources, tooltip


def upgrade_cost(name, level):
    return int(data.SYSTEMS[name]['cost'] * level * 0.75) + 5


def gusto_cost(gusto):
    return 25 + 4 * max(0, gusto - 8)


class ShipwrightScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.msg = "The shipwright sucks his teeth. 'Ooh. Who did your joinery?'"
        self.build()

    def build(self):
        gs, ship = self.gs, self.gs.ship
        self.buttons = []
        self.tips = []
        y = 88
        for name in data.SYS_ORDER:
            s = ship.sys.get(name)
            if not s:
                continue
            mx = data.SYSTEMS[name]['max']
            if s.level < mx:
                cost = upgrade_cost(name, s.level)
                b = gfx.Button((150, y, 76, 18), f"+1  {cost}g", lambda n=name, c=cost: self.upgrade(n, c),
                               enabled=gs.doubloons >= cost, size=14)
                self.buttons.append(b)
            self.tips.append((pygame.Rect(30, y, 118, 18), data.SYSTEMS[name]['desc']))
            y += 22
        cost = gusto_cost(ship.gusto)
        self.buttons.append(gfx.Button((150, y + 6, 76, 18), f"+1  {cost}g", lambda c=cost: self.gusto(c),
                                       enabled=gs.doubloons >= cost, size=14))
        self.tips.append((pygame.Rect(30, y + 6, 118, 18),
                          "Gusto is the crew's collective effort. More bars = more systems powered. "
                          "Upgrading involves a shanty singer and a lot of coffee."))
        self.gusto_y = y + 6
        # cannons
        y = 88
        for i, w in enumerate(ship.weapons):
            b = gfx.Button((246, y, 170, 18), f"{w.name}  (stow)", lambda i=i: self.stow(i),
                           enabled=len(ship.weapons) > 1, size=14)
            self.buttons.append(b)
            self.tips.append((b.rect, w.d['desc'] + "  [" + ' '.join(data.weapon_tags(w.d)) + "]"))
            y += 22
        y = 214
        for i, key in enumerate(gs.cargo):
            d = data.WEAPONS[key]
            b = gfx.Button((246, y, 112, 18), f"{d['name']}", lambda i=i: self.equip(i),
                           enabled=len(ship.weapons) < MAX_WEAPONS, size=14)
            self.buttons.append(b)
            self.tips.append((b.rect, f"Click to equip. {d['desc']}"))
            sell = d['cost'] // 2
            self.buttons.append(gfx.Button((360, y, 56, 18), f"sell {sell}", lambda i=i, v=sell: self.sell(i, v),
                                           size=14))
            y += 22
        self.buttons.append(gfx.Button((W // 2 - 50, H - 34, 100, 22), "Done", self.app.pop,
                                       key=pygame.K_ESCAPE))

    def upgrade(self, name, cost):
        gs = self.gs
        gs.doubloons -= cost
        gs.ship.sys[name].level += 1
        audio.play('win')
        self.msg = f"{data.SYSTEMS[name]['title']} upgraded. 'Lovely bit of work, that. If I say so myself.'"
        self.build()

    def gusto(self, cost):
        self.gs.doubloons -= cost
        self.gs.ship.gusto += 1
        audio.play('win')
        self.msg = "+1 Gusto. The crew is now slightly more motivated. Only slightly."
        self.build()

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

    def sell(self, i, v):
        self.gs.cargo.pop(i)
        self.gs.doubloons += v
        audio.play('click')
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
        gfx.dim(s, 160)
        gfx.panel(s, (20, 30, W - 40, H - 40), 'parch')
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        draw_resources(s, gs)
        gfx.text(s, "SHIPWRIGHT", W // 2, 38, P['dred'], 24, align='center')
        gfx.text(s, self.msg, W // 2, 58, P['ink'], align='center')
        gfx.text(s, "SYSTEMS", 30, 76, P['dred'])
        y = 88
        for name in data.SYS_ORDER:
            sy = ship.sys.get(name)
            if not sy:
                continue
            mx = data.SYSTEMS[name]['max']
            s.blit(gfx.icon(name), (30, y + 4))
            gfx.text(s, data.SYSTEMS[name]['title'], 42, y + 1, P['ink'])
            for j in range(mx):
                pygame.draw.rect(s, P['dgreen'] if j < sy.level else P['parch2'], (42 + j * 13, y + 11, 11, 4))
            y += 22
        gfx.text(s, f"Gusto: {ship.gusto}", 30, self.gusto_y + 5, P['ink'])
        gfx.text(s, f"CANNONS ({len(ship.weapons)}/{MAX_WEAPONS})", 246, 76, P['dred'])
        gfx.text(s, "THE HOLD (click to equip)", 246, 202, P['dred'])
        if not gs.cargo:
            gfx.text(s, "Empty, apart from a suspicious smell.", 246, 214, P['parch3'])
        gfx.text(s, f"CREW ({len(gs.crew)}/8)", 436, 76, P['dred'])
        y = 86
        for c in gs.crew:
            gfx.portrait(s, c.cls, c.skin, 436, y, 2)
            gfx.text(s, f"{c.name}", 466, y + 4, P['ink'])
            gfx.text(s, f"{c.title}", 466, y + 14, P['wood2'])
            gfx.bar(s, 560, y + 15, 50, 4, c.hp / c.max_hp, P['dgreen'] if c.hp > c.max_hp * .35 else P['red'])
            y += 29
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
        for rect, tip in self.tips:
            if rect.collidepoint(m):
                tooltip(s, tip, m, 220)
        for i, c in enumerate(gs.crew):
            if pygame.Rect(436, 86 + i * 29, 180, 28).collidepoint(m):
                tooltip(s, c.d['desc'], m, 200)
