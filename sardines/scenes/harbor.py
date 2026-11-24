"""A port: your ship sails into the harbor and ties up at the dock. Market, Trade, Tavern, Shipyard."""
import math
import random

import pygame

from .. import audio, data, gfx, people, profile, render
from ..app import Scene
from ..config import H, MAX_CREW, MAX_WEAPONS, RH, TW, W
from ..gfx import P
from .hud import draw_resources, tooltip
from .store import BROKE, HIRE_PITCH, HIRE_PRICE, QUIPS, THANKS

PORT_NAMES = ["Port Mackerel", "Saltmouth", "Barnacle Bay", "New Haddock", "Codsworth", "Herring Harbour",
              "Rumhaven", "Pilchard Point", "Old Kipper", "Smuggler's Rest", "Anchovy Cove", "Brinewick"]
PANEL_Y = 214
TABS = ['Market', 'Trade', 'Tavern', 'Shipyard']
SHIP_O = (14, 52)


def upgrade_cost(name, level):
    return int(data.SYSTEMS[name]['cost'] * level * 0.75) + 5


def module_cost(kind, level):
    return int(data.MODULES[kind]['cost'] * (0.6 + 0.5 * level))


def gen_port(gs):
    rng = gs.rng
    weapons = rng.sample(sorted(set(data.LOOT_WEAPONS)), 3)
    hires = [rng.choice(data.HIREABLE) for _ in range(3)]
    from ..model import Crew
    prices = {}
    for k, g in data.GOODS.items():
        prices[k] = max(2, int(g['price'] * rng.uniform(0.55, 1.6)))
    return dict(name=rng.choice(PORT_NAMES), weapons=[dict(key=k, sold=False) for k in weapons],
                hires=[dict(crew=Crew(c, side='player', rng=rng), sold=False) for c in hires],
                prices=prices, quip=rng.choice(QUIPS), keeper_skin=rng.randrange(4), seed=rng.randrange(1 << 20))


class HarborScene(Scene):
    def __init__(self, app, node):
        super().__init__(app)
        if node.store is None or 'prices' not in node.store:
            node.store = gen_port(self.gs)
        self.node = node
        self.port = node.store
        self.t = 0.0
        self.dock_t = 0.0
        self.tab = 'Market'
        self.msg = self.port['quip']
        self.sel_room = None
        self.locals = self._make_locals()
        audio.play('bell')
        audio.set_mood('port')
        self.build()

    def _make_locals(self):
        rng = random.Random(self.port['seed'])
        folk = []
        for _ in range(6):
            cls = rng.choice(['deckhand', 'merchant', 'cook', 'monkey', 'drunk', 'carpenter', 'pirate'])
            folk.append(dict(cls=cls, skin=rng.randrange(4), x=rng.uniform(360, 620), v=rng.choice([-1, 1]) *
                             rng.uniform(6, 14), pause=0.0))
        return folk

    # ------------------------------------------------------------------
    def buy(self, price, fn):
        if self.gs.doubloons < price:
            self.msg = random.choice(BROKE)
            audio.play('click')
            return
        if fn() is False:
            return
        self.gs.doubloons -= price
        audio.play('win')
        self.build()

    def build(self):
        gs, ship = self.gs, self.gs.ship
        self.buttons, self.tips = [], []
        for i, name in enumerate(TABS):
            b = gfx.Button((8 + i * 74, PANEL_Y + 2, 70, 16), name, (lambda n=name: self.set_tab(n)), size=14,
                           key=pygame.K_1 + i)
            b.active = self.tab == name
            self.buttons.append(b)
        self.buttons.append(gfx.Button((W - 104, PANEL_Y + 2, 96, 16), "Set sail", self.leave, size=14,
                                       key=pygame.K_ESCAPE))
        getattr(self, 'build_' + self.tab.lower())()

    def set_tab(self, name):
        self.tab = name
        self.sel_room = None if name != 'Shipyard' else self.sel_room
        self.build()

    def leave(self):
        self.node.cleared = True
        audio.set_mood('sea')
        self.app.pop()

    # -- tabs --------------------------------------------------------------
    def build_market(self):
        gs, ship = self.gs, self.gs.ship
        missing = ship.hull_max - ship.hull

        def addv(attr, n):
            def f():
                setattr(gs, attr, getattr(gs, attr) + n)
            return f

        def repair(n):
            def f():
                ship.hull = min(ship.hull_max, ship.hull + n)
            return f
        rows = [('rum', "1 Rum", 4, addv('rum', 1), True), ('rum', "5 Rum", 18, addv('rum', 5), True),
                ('ball', "2 Cannonballs", 11, addv('balls', 2), True),
                ('heart', "Patch 1 hull", 3, repair(1), missing > 0),
                ('heart', f"Repair all (+{missing})", max(1, 3 * missing - missing // 4), repair(missing), missing > 1)]
        self.rows = []
        y = PANEL_Y + 38
        for ic, label, price, fn, ok in rows:
            self.rows.append((ic, label, 12, y))
            self.buttons.append(gfx.Button((118, y - 2, 40, 13), f"{price}g", lambda p=price, f=fn: self.buy(p, f),
                                           enabled=ok and gs.doubloons >= price, size=14))
            y += 16
        self.cards = []
        y = PANEL_Y + 36
        for item in self.port['weapons']:
            d = data.WEAPONS[item['key']]
            self.cards.append((item, 172, y))
            if not item['sold']:
                def bw(item=item):
                    gs.add_weapon(item['key'])
                    item['sold'] = True
                    self.msg = random.choice(THANKS)
                self.buttons.append(gfx.Button((172 + 230, y + 2, 40, 13), f"{d['cost']}g",
                                               lambda p=d['cost'], f=bw: self.buy(p, f),
                                               enabled=gs.doubloons >= d['cost'], size=14))
                self.tips.append((pygame.Rect(172, y, 226, 26), f"{d['name']}: {d['desc']} {d['shots']} shot(s), "
                                  f"{d['dmg'] + d.get('hull', 0)} hull damage, loads in {d['charge']:.1f}s, "
                                  f"needs {d['power']} Hands."))
            y += 30
        # sell spare cannons from the hold
        y = PANEL_Y + 38
        self.spares = []
        for i, key in enumerate(gs.cargo[:5]):
            d = data.WEAPONS[key]
            v = d['cost'] // 2
            self.spares.append((d['name'], 456, y))
            self.buttons.append(gfx.Button((456 + 120, y - 2, 52, 13), f"sell {v}", (lambda i=i, v=v: self.sell(i, v)),
                                           size=14))
            y += 16

    def sell(self, i, v):
        self.gs.cargo.pop(i)
        self.gs.doubloons += v
        audio.play('click')
        self.msg = "Lovely bit of iron. I'll give it a polish and sell it back to you later."
        self.build()

    def build_trade(self):
        gs = self.gs
        self.trade_rows = []
        y = PANEL_Y + 40
        for k, g in data.GOODS.items():
            price = self.port['prices'][k]
            self.trade_rows.append((k, y))
            room = gs.cargo_cap() - gs.cargo_used()

            def b1(k=k):
                if gs.cargo_cap() - gs.cargo_used() <= 0:
                    self.msg = "Your hold's full, captain. Buy a Cargo Hold at the Shipyard."
                    return False
                gs.goods[k] += 1
            self.buttons.append(gfx.Button((300, y - 2, 52, 13), f"buy {price}", lambda p=price, f=b1: self.buy(p, f),
                                           enabled=gs.doubloons >= price and room > 0, size=14))
            self.buttons.append(gfx.Button((356, y - 2, 52, 13), f"sell {price}", (lambda k=k: self.sell_good(k, 1)),
                                           enabled=gs.goods[k] > 0, size=14))
            self.buttons.append(gfx.Button((412, y - 2, 52, 13), "sell all", (lambda k=k: self.sell_good(k, 99)),
                                           enabled=gs.goods[k] > 0, size=14))
            self.tips.append((pygame.Rect(12, y - 2, 280, 13), g['desc']))
            y += 17

    def sell_good(self, k, n):
        gs = self.gs
        n = min(n, gs.goods[k])
        gs.goods[k] -= n
        gs.doubloons += n * self.port['prices'][k]
        gs.stats['doubloons'] += n * self.port['prices'][k]
        audio.play('win')
        self.msg = random.choice(["A pleasure. Mostly yours.", "Sold! Don't tell the Revenue men.",
                                  "That'll do nicely."])
        self.build()

    def build_tavern(self):
        gs = self.gs
        self.hire_cards = []
        x = 12
        for item in self.port['hires']:
            c = item['crew']
            self.hire_cards.append((item, x))
            if not item['sold']:
                price = HIRE_PRICE.get(c.cls, 45)

                def bh(item=item):
                    if len(gs.crew) >= MAX_CREW:
                        self.msg = "Your ship's full, mate. Any more and she'll sink."
                        return False
                    gs.ship.place(item['crew'], None, gs.rng)
                    item['sold'] = True
                    self.msg = f"{item['crew'].name} grabs their bag and heads for the gangplank."
                    for n in profile.record(max_drunks=sum(1 for x_ in gs.crew if x_.cls == 'drunk')):
                        self.msg = f"NEW SHIP UNLOCKED: {n}!"
                self.buttons.append(gfx.Button((x + 128, PANEL_Y + 112, 60, 14), f"hire {price}g",
                                               lambda p=price, f=bh: self.buy(p, f),
                                               enabled=gs.doubloons >= price and len(gs.crew) < MAX_CREW, size=14))
            x += 204

        def round_():
            for c in gs.crew:
                c.hp = min(c.max_hp, c.hp + 30)
            self.msg = "A round for the crew! Everyone feels much better. Several feel much worse."
        self.buttons.append(gfx.Button((W - 180, PANEL_Y + 2, 72, 16), "Round 10g", lambda: self.buy(10, round_),
                                       enabled=gs.doubloons >= 10, size=14))

    def build_shipyard(self):
        gs, ship = self.gs, self.gs.ship
        self.yard = None
        if self.sel_room is None:
            return
        r = ship.rooms[self.sel_room]
        x, y = 12, PANEL_Y + 26
        if r.sys:
            s_ = ship.sys[r.sys]
            mx = data.SYSTEMS[r.sys]['max']
            self.yard = ('system', r)
            if s_.level < mx:
                cost = upgrade_cost(r.sys, s_.level)

                def up():
                    s_.level += 1
                    self.msg = f"{data.SYSTEMS[r.sys]['title']} upgraded to level {s_.level}. Lovely joinery."
                self.buttons.append(gfx.Button((x, PANEL_Y + 104, 150, 16), f"Upgrade to Lv{s_.level + 1}: {cost}g",
                                               lambda c=cost, f=up: self.buy(c, f), enabled=gs.doubloons >= cost,
                                               size=14))
        elif r.kind == 'empty':
            self.yard = ('empty', r)
            for i, (k, m) in enumerate(data.MODULES.items()):
                cost = m['cost']
                bx = 260 + (i % 2) * 186
                by = PANEL_Y + 26 + (i // 2) * 22

                def inst(k=k):
                    ship.install(self.sel_room, k)
                    ship._hull_surf = None
                    self.msg = f"A {data.MODULES[k]['title']} it is. Mind the sawdust."
                b = gfx.Button((bx, by, 180, 18), f"{m['title']}  {cost}g", lambda c=cost, f=inst: self.buy(c, f),
                               enabled=gs.doubloons >= cost, size=14)
                self.buttons.append(b)
                self.tips.append((b.rect, m['desc']))
        else:
            self.yard = ('module', r)
            m = data.MODULES[r.kind]
            if r.level < m['max']:
                cost = module_cost(r.kind, r.level)

                def up():
                    r.level += 1
                    self.msg = f"{m['title']} upgraded to level {r.level}."
                self.buttons.append(gfx.Button((x, PANEL_Y + 104, 150, 16), f"Upgrade to Lv{r.level + 1}: {cost}g",
                                               lambda c=cost, f=up: self.buy(c, f), enabled=gs.doubloons >= cost,
                                               size=14))

    # ------------------------------------------------------------------
    def ship_origin(self):
        k = min(1.0, self.dock_t / 2.6)
        k = 1 - (1 - k) ** 3
        x = -360 + (SHIP_O[0] + 360) * k
        return int(x), SHIP_O[1] + int(math.sin(self.t * 1.2) * 1.2)

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and e.pos[1] < PANEL_Y:
            ri = render.room_at(self.gs.ship, *self.ship_origin(), e.pos)
            if ri is not None:
                self.sel_room = ri
                self.tab = 'Shipyard'
                audio.play('click')
                self.build()

    def update(self, dt):
        self.t += dt
        self.dock_t += dt
        for c in self.gs.ship.crew:
            c.anim += dt
        for f in self.locals:
            if f['pause'] > 0:
                f['pause'] -= dt
                continue
            f['x'] += f['v'] * dt
            if f['x'] < 352 or f['x'] > 628 or random.random() < dt * 0.15:
                f['v'] = -f['v']
                f['pause'] = random.uniform(0.5, 2.5)
                f['x'] = max(352, min(628, f['x']))

    # ------------------------------------------------------------------
    def draw_town(self, s):
        t = self.t
        rng = random.Random(self.port['seed'])
        # sky, far hills, sea
        for y in range(0, 120):
            k = y / 120
            pygame.draw.line(s, (int(120 + 90 * k), int(170 + 55 * k), int(215 + 25 * k)), (0, y), (W, y))
        pygame.draw.circle(s, (255, 236, 170), (90, 34), 12)
        for i in range(3):
            cx = int((i * 211 + t * (2 + i)) % (W + 120)) - 60
            for dx, r in ((0, 8), (10, 11), (22, 8)):
                pygame.draw.circle(s, (246, 248, 252), (cx + dx, 26 + i * 14), r)
        hill = [(300, 120)] + [(300 + i * 20, 120 - int(26 + 18 * math.sin(i * 0.9 + 1))) for i in range(18)] + [(W, 120)]
        pygame.draw.polygon(s, (90, 140, 110), hill)
        gfx.draw_sea(s, t, 120)
        # the island and town
        pygame.draw.polygon(s, (226, 204, 150), [(330, 214), (340, 150), (380, 132), (W, 128), (W, 214)])
        pygame.draw.polygon(s, (110, 160, 90), [(352, 150), (390, 126), (W, 120), (W, 146), (380, 154)])
        # lighthouse
        lx = 600
        pygame.draw.polygon(s, P['white'], [(lx - 6, 128), (lx + 6, 128), (lx + 4, 70), (lx - 4, 70)])
        for yy in (84, 104):
            pygame.draw.rect(s, P['red'], (lx - 5, yy, 10, 7))
        pygame.draw.rect(s, P['dgrey'], (lx - 5, 62, 10, 8))
        if int(t * 2) % 2:
            pygame.draw.circle(s, P['yellow'], (lx, 66), 3)
        # houses
        x = 392
        for i in range(5):
            w = rng.randint(30, 40)
            h = rng.randint(22, 34)
            base = 132
            wall = rng.choice([(236, 220, 190), (200, 170, 130), (180, 200, 220), (230, 200, 200)])
            roof = rng.choice([(180, 70, 50), (120, 80, 60), (70, 90, 140)])
            pygame.draw.rect(s, wall, (x, base - h, w, h))
            pygame.draw.polygon(s, roof, [(x - 3, base - h), (x + w // 2, base - h - 12), (x + w + 3, base - h)])
            pygame.draw.rect(s, P['wood1'], (x + w // 2 - 3, base - 9, 6, 9))
            for wx in (x + 5, x + w - 10):
                lit = (int(t * 0.4 + i + wx) % 5) != 0
                pygame.draw.rect(s, (250, 220, 130) if lit else (60, 70, 90), (wx, base - h + 6, 5, 5))
            x += w + rng.randint(4, 10)
        # sign
        pygame.draw.rect(s, P['wood1'], (402, 94, 2, 10))
        # palm trees
        for px in (350, 560):
            pygame.draw.line(s, P['wood1'], (px, 140), (px + 4, 108), 3)
            for a in range(5):
                ang = -2.6 + a * 0.55 + math.sin(t + a) * 0.05
                pygame.draw.line(s, (60, 140, 70), (px + 4, 108), (px + 4 + math.cos(ang) * 14, 108 + math.sin(ang) * 8 + 4), 2)
        # market stalls
        for sx in (470, 520):
            pygame.draw.rect(s, P['wood2'], (sx, 140, 30, 10))
            for j in range(5):
                pygame.draw.rect(s, P['red'] if j % 2 else P['white'], (sx - 2 + j * 7, 132, 7, 5))
        # dock
        pygame.draw.rect(s, P['wood1'], (300, 188, 140, 5))
        for px_ in range(304, 440, 14):
            pygame.draw.line(s, P['wood0'], (px_, 193), (px_, 214), 2)
        # locals walking the quay
        for f in self.locals:
            frame = int(self.t * 6 + f['x']) % 4 if f['pause'] <= 0 else 0
            spr = people.sprite(f['cls'], f['skin'], 'walk' if f['pause'] <= 0 else 'stand', frame,
                                1 if f['v'] > 0 else -1)
            s.blit(spr, (int(f['x']) - 8, 150 - people.FEET_Y))
        gfx.text_outline(s, self.port['name'].upper(), 480, 30, P['gold'], 24, align='center')

    def draw(self, s):
        gs, ship = self.gs, self.gs.ship
        self.draw_town(s)
        ox, oy = self.ship_origin()
        render.draw_ship(s, ship, ox, oy, self.t,
                         hover=render.room_at(ship, ox, oy, pygame.mouse.get_pos()) if self.dock_t > 2.6 else None)
        if self.sel_room is not None:
            r = ship.rooms[self.sel_room]
            rect = pygame.Rect(ox + r.gx * TW, oy + r.gy * RH, r.w * TW, RH)
            pygame.draw.rect(s, P['gold'], rect.inflate(2, 2), 2)
        # mooring line once docked
        if self.dock_t > 2.6:
            bx = ox + ship.gw * TW + 30
            pygame.draw.line(s, (190, 160, 100), (bx, oy + 2 * RH - 8), (306, 188))
        pygame.draw.rect(s, P['navy'], (0, 0, W, 22))
        draw_resources(s, gs, y=7)
        # keeper speech
        bubble = pygame.Rect(338, 182 - 6, 0, 14)
        bubble.width = min(W - 344, gfx.text_w(self.msg) + 10)
        b2 = pygame.Rect(W - bubble.width - 6, 160, bubble.width, 14)
        pygame.draw.rect(s, P['white'], b2)
        pygame.draw.rect(s, P['ink'], b2, 1)
        gfx.text(s, self.msg if gfx.text_w(self.msg) < b2.width else self.msg[:70] + '...', b2.left + 5, b2.top + 4,
                 P['ink'])
        # panel
        gfx.panel(s, (0, PANEL_Y, W, H - PANEL_Y), 'parch')
        m = pygame.mouse.get_pos()
        getattr(self, 'draw_' + self.tab.lower())(s)
        for b in self.buttons:
            if getattr(b, 'active', False):
                pygame.draw.rect(s, P['gold'], b.rect.inflate(4, 4), 2)
            b.draw(s, m)
        for rect, tip in self.tips:
            if rect.collidepoint(m):
                tooltip(s, tip, m, 230)
                break
        else:
            if m[1] < PANEL_Y and self.dock_t > 2.6:
                ri = render.room_at(ship, ox, oy, m)
                if ri is not None:
                    tooltip(s, f"{ship.rooms[ri].title}: click to upgrade at the Shipyard.", m, 200)

    def draw_market(self, s):
        gfx.text(s, "SUPPLIES", 12, PANEL_Y + 24, P['dred'])
        gfx.text(s, "CANNONS FOR SALE", 172, PANEL_Y + 24, P['dred'])
        for ic, label, x, y in self.rows:
            s.blit(gfx.icon(ic), (x, y))
            gfx.text(s, label, x + 10, y, P['ink'])
        from .hangar import draw_tag
        for item, x, y in self.cards:
            d = data.WEAPONS[item['key']]
            r = pygame.Rect(x, y - 2, 274, 28)
            pygame.draw.rect(s, P['parch2'], r)
            gfx.text(s, d['name'], x + 4, y + 1, P['ink'] if not item['sold'] else P['parch3'])
            tx = x + 4
            for tag in data.weapon_tags(d)[:3]:
                tx += draw_tag(s, tag, tx, y + 13) + 2
            if item['sold']:
                gfx.text(s, "SOLD", r.right - 6, y + 1, P['dred'], align='right')
        gfx.text(s, "YOUR SPARE CANNONS", 456, PANEL_Y + 24, P['dred'])
        if not self.spares:
            gfx.text(s, "None. Buy one with 4 cannons", 456, PANEL_Y + 38, P['parch3'])
            gfx.text(s, "fitted and it goes here.", 456, PANEL_Y + 48, P['parch3'])
        for name, x, y in self.spares:
            gfx.text(s, name, x, y, P['ink'])

    def draw_trade(self, s):
        gs = self.gs
        gfx.text(s, f"TRADE GOODS: prices change from port to port. Cargo {gs.cargo_used()}/{gs.cargo_cap()}",
                 12, PANEL_Y + 24, P['dred'])
        if gs.ship.module_level('hold') == 0:
            gfx.text(s, "(No Cargo Hold: you can carry 2. Install one at the Shipyard.)", 12, PANEL_Y + 112,
                     P['wood2'])
        for k, y in self.trade_rows:
            g = data.GOODS[k]
            s.blit(gfx.icon(k), (12, y))
            gfx.text(s, g['title'], 24, y, P['ink'])
            price = self.port['prices'][k]
            base = g['price']
            verdict = "cheap here!" if price < base * 0.8 else ("pays well here!" if price > base * 1.25 else "")
            gfx.text(s, f"{price}g", 140, y, P['ink'])
            gfx.text(s, verdict, 172, y, P['dgreen'] if 'cheap' in verdict else P['dred'])
            gfx.text(s, f"you have {gs.goods[k]}", 480, y, P['wood2'])

    def draw_tavern(self, s):
        gfx.text(s, "THE TAVERN: sailors looking for work", 12, PANEL_Y + 24, P['dred'])
        for item, x in self.hire_cards:
            c = item['crew']
            r = pygame.Rect(x, PANEL_Y + 36, 196, 92)
            pygame.draw.rect(s, P['parch2'], r)
            pygame.draw.rect(s, P['parch3'], r, 1)
            img = people.portrait(c.cls, c.skin, 3)
            pygame.draw.rect(s, P['navy2'], (x + 4, r.top + 4, 50, 70))
            s.blit(img, (x + 5, r.top + 6))
            pygame.draw.rect(s, P['gold'], (x + 4, r.top + 4, 50, 70), 1)
            gfx.text(s, c.name, x + 60, r.top + 5, P['ink'] if not item['sold'] else P['parch3'])
            gfx.text(s, f"{c.title}, {data.HANDS.get(c.cls, 3)} Hands", x + 60, r.top + 15, P['wood2'])
            if item['sold']:
                gfx.text(s, "HIRED", x + 60, r.top + 28, P['dgreen'])
            else:
                gfx.paragraph(s, HIRE_PITCH.get(c.cls, c.d['desc']), x + 60, r.top + 28, 130, P['wood1'], line=10)

    def draw_shipyard(self, s):
        ship = self.gs.ship
        if self.yard is None:
            gfx.text(s, "THE SHIPYARD", 12, PANEL_Y + 24, P['dred'])
            gfx.paragraph(s, "Click any room on your ship to upgrade it. Empty compartments can be fitted with a "
                             "module: each one adds a new mechanic to your ship.", 12, PANEL_Y + 38, 600, P['ink'])
            empt = len(ship.empty_rooms())
            gfx.text(s, f"Empty compartments: {empt}", 12, PANEL_Y + 70, P['wood2'])
            return
        kind, r = self.yard
        if kind == 'system':
            d = data.SYSTEMS[r.sys]
            lvl, mx = ship.sys[r.sys].level, d['max']
            title, desc = d['title'], d['desc']
        elif kind == 'module':
            d = data.MODULES[r.kind]
            lvl, mx = r.level, d['max']
            title, desc = d['title'], d['desc']
        else:
            lvl, mx = 0, 0
            title, desc = "Empty compartment", "Choose a module to install here. Hover for details."
        gfx.text(s, title.upper(), 12, PANEL_Y + 24, P['dred'])
        for i in range(mx):
            pygame.draw.rect(s, P['dgreen'] if i < lvl else P['parch2'], (12 + i * 12, PANEL_Y + 36, 10, 5))
        gfx.paragraph(s, desc, 12, PANEL_Y + 46, 236 if kind == 'empty' else 600, P['ink'])
        if kind != 'empty' and lvl >= mx:
            gfx.text(s, "Fully upgraded.", 12, PANEL_Y + 106, P['dgreen'])
