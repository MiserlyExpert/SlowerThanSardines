"""Port market, with a shopkeeper and portraits of crew for hire."""
import random

import pygame

from .. import audio, data, gfx, profile
from ..app import Scene
from ..config import H, MAX_CREW, MAX_WEAPONS, W
from ..gfx import P
from .hangar import draw_tag
from .hud import draw_resources, tooltip

QUIPS = [
    "Everything's for sale. Except the parrot. The parrot is for rent.",
    "No refunds. No returns. No questions. Especially no questions.",
    "Cannonballs! Gently used! Fired only once!",
    "Rum's fresh. Fresh-ish. It was fresh at one point, definitely.",
    "Rebels get a discount. Not a big one. But it's the thought.",
    "I don't sell to the Crown. Mostly because they never pay.",
]
BROKE = ["Come back when you've got the coin, sunshine.", "That's not enough doubloons. I counted. Twice.",
         "I don't take IOUs. Or fish. Well. Depends on the fish."]
THANKS = ["Pleasure doing business!", "Lovely. No take-backs.", "Spend more, it's good for morale. Mine."]
HIRE_PRICE = dict(captain=70, drunk=45, deckhand=40, monkey=40, carpenter=50, surgeon=50, cook=50)
HIRE_PITCH = {
    'captain': "Retired captain. Steers beautifully. Will tell you about it.",
    'drunk': "Found asleep in a barrel. Excellent shot. Excellent puncher.",
    'deckhand': "Can tie three knots. Claims forty.",
    'monkey': "Small. Fast. Asks about gunpowder too often.",
    'carpenter': "Will fix your hull and criticise it at the same time.",
    'surgeon': "Has a saw. Has a different saw for emergencies.",
    'cook': "Makes a stew that heals the soul. And wounds. Mostly wounds.",
}


def gen_store(gs):
    rng = gs.rng
    weapons = rng.sample(sorted(set(data.LOOT_WEAPONS)), 3)
    hires = [rng.choice(data.HIREABLE) for _ in range(3)]
    from ..model import Crew
    return dict(weapons=[dict(key=k, sold=False) for k in weapons],
                hires=[dict(crew=Crew(c, side='player', rng=rng), sold=False) for c in hires],
                quip=rng.choice(QUIPS), keeper_skin=rng.randrange(4))


class StoreScene(Scene):
    overlay = True

    def __init__(self, app, node):
        super().__init__(app)
        if node.store is None:
            node.store = gen_store(self.gs)
        self.store = node.store
        self.msg = self.store['quip']
        self.t = 0.0
        self.build()

    def buy(self, price, fn):
        if self.gs.doubloons < price:
            self.msg = random.choice(BROKE)
            return
        res = fn()
        if res is False:
            return
        self.gs.doubloons -= price
        audio.play('win')
        if not self.msg.startswith("NEW SHIP"):
            self.msg = random.choice(THANKS)
        self.build()

    def build(self):
        gs, ship = self.gs, self.gs.ship
        self.buttons, self.tips = [], []
        missing = ship.hull_max - ship.hull

        def addv(attr, n):
            def f():
                setattr(gs, attr, getattr(gs, attr) + n)
            return f

        def repair(n):
            def f():
                ship.hull = min(ship.hull_max, ship.hull + n)
            return f

        # supplies column
        self.supplies = []
        rows = [('rum', "1 Rum", 4, addv('rum', 1), True), ('rum', "5 Rum", 18, addv('rum', 5), True),
                ('ball', "1 Cannonball", 6, addv('balls', 1), True),
                ('ball', "4 Cannonballs", 20, addv('balls', 4), True),
                ('heart', "Patch 1 hull", 3, repair(1), missing > 0)]
        if missing > 1:
            cost = 3 * missing - missing // 4
            rows.append(('heart', f"Repair all (+{missing})", cost, repair(missing), True))
        y = 102
        for ic, label, price, fn, ok in rows:
            self.supplies.append((ic, label, y))
            self.buttons.append(gfx.Button((150, y - 3, 44, 15), f"{price}g", lambda p=price, f=fn: self.buy(p, f),
                                           enabled=ok and gs.doubloons >= price, size=14))
            y += 18
        # cannons column
        self.cannons = []
        y = 104
        for item in self.store['weapons']:
            d = data.WEAPONS[item['key']]
            self.cannons.append((item, y))
            if not item['sold']:
                def bw(item=item):
                    self.msg = random.choice(THANKS)
                    gs.add_weapon(item['key'])
                    item['sold'] = True
                self.buttons.append(gfx.Button((358, y + 3, 44, 15), f"{d['cost']}g",
                                               lambda p=d['cost'], f=bw: self.buy(p, f),
                                               enabled=gs.doubloons >= d['cost'], size=14))
                self.tips.append((pygame.Rect(214, y, 190, 50),
                                  f"{d['shots']} shot(s), {d['dmg'] + d.get('hull', 0)} hull dmg, "
                                  f"{d['charge']:.1f}s reload, needs {d['power']} power."
                                  + (" Goes to the hold if you already have 4 cannons."
                                     if len(ship.weapons) >= MAX_WEAPONS else "")))
            y += 56
        # crew column
        self.hires = []
        y = 104
        for item in self.store['hires']:
            c = item['crew']
            self.hires.append((item, y))
            if not item['sold']:
                price = HIRE_PRICE.get(c.cls, 45)

                def bh(item=item):
                    if len(gs.crew) >= MAX_CREW:
                        self.msg = "Your ship's full, mate. Any more and she'll sink."
                        return False
                    gs.ship.place(item['crew'], None, gs.rng)
                    item['sold'] = True
                    self.msg = f"{item['crew'].name} waves goodbye to nobody in particular."
                    for n in profile.record(max_drunks=sum(1 for x in gs.crew if x.cls == 'drunk')):
                        self.msg = f"NEW SHIP UNLOCKED: {n}!"
                self.buttons.append(gfx.Button((574, y + 3, 44, 15), f"{price}g",
                                               lambda p=price, f=bh: self.buy(p, f),
                                               enabled=gs.doubloons >= price and len(gs.crew) < MAX_CREW, size=14))
                self.tips.append((pygame.Rect(418, y, 200, 50), c.d['desc']))
            y += 56
        self.buttons.append(gfx.Button((W // 2 - 60, H - 30, 120, 22), "Leave port", self.leave,
                                       key=pygame.K_ESCAPE))

    def leave(self):
        self.gs.sector.node.cleared = True
        self.app.pop()

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        gs = self.gs
        gfx.dim(s, 170)
        gfx.panel(s, (10, 30, W - 20, H - 36), 'parch')
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        draw_resources(s, gs)
        # shopkeeper + speech bubble
        gfx.portrait(s, 'merchant', self.store.get('keeper_skin', 1), 22, 38, 3, bg=P['wood1'], t=self.t)
        gfx.text(s, "PORT MARKET", 66, 40, P['dred'], 24)
        bubble = pygame.Rect(66, 58, 360, 18)
        pygame.draw.rect(s, P['white'], bubble)
        pygame.draw.rect(s, P['ink'], bubble, 1)
        pygame.draw.polygon(s, P['white'], [(bubble.left, bubble.top + 5), (bubble.left - 6, bubble.top + 9),
                                            (bubble.left, bubble.top + 12)])
        gfx.text(s, self.msg, bubble.left + 6, bubble.top + 5, P['ink'])
        gfx.text(s, f"Hull {gs.ship.hull}/{gs.ship.hull_max}    Crew {len(gs.crew)}/{MAX_CREW}    "
                 f"Cannons {len(gs.ship.weapons)}/{MAX_WEAPONS}", W - 24, 42, P['wood2'], align='right')
        # column headers
        for x, label in ((22, "SUPPLIES"), (214, "CANNONS"), (418, "CREW FOR HIRE")):
            gfx.text(s, label, x, 88, P['dred'])
            pygame.draw.line(s, P['parch3'], (x, 98), (x + 184, 98))
        for ic, label, y in self.supplies:
            s.blit(gfx.icon(ic), (24, y))
            gfx.text(s, label, 36, y, P['ink'])
        for item, y in self.cannons:
            d = data.WEAPONS[item['key']]
            r = pygame.Rect(214, y, 192, 50)
            pygame.draw.rect(s, P['parch2'], r)
            pygame.draw.rect(s, P['parch3'], r, 1)
            gfx.text(s, d['name'], r.left + 5, r.top + 5, P['ink'] if not item['sold'] else P['parch3'])
            tx = r.left + 5
            for tag in data.weapon_tags(d)[:3]:
                tx += draw_tag(s, tag, tx, r.top + 15) + 2
            if item['sold']:
                gfx.text(s, "SOLD", r.right - 6, r.top + 5, P['dred'], align='right')
            gfx.paragraph(s, d['desc'], r.left + 5, r.top + 27, 182, P['wood1'], line=10)
        for item, y in self.hires:
            c = item['crew']
            r = pygame.Rect(418, y, 202, 50)
            pygame.draw.rect(s, P['parch2'], r)
            pygame.draw.rect(s, P['parch3'], r, 1)
            gfx.portrait(s, c.cls, c.skin, r.left + 3, r.top + 3, 2, t=self.t if not item['sold'] else 0)
            gfx.text(s, c.name, r.left + 32, r.top + 4, P['ink'] if not item['sold'] else P['parch3'])
            gfx.text(s, c.title, r.left + 32, r.top + 14, P['wood2'])
            if item['sold']:
                gfx.text(s, "HIRED", r.right - 6, r.top + 5, P['dgreen'], align='right')
            else:
                gfx.paragraph(s, HIRE_PITCH.get(c.cls, c.d['desc']), r.left + 32, r.top + 26, 166, P['wood1'],
                              line=10)
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, m)
        for rect, tip in self.tips:
            if rect.collidepoint(m):
                tooltip(s, tip, m, 220)
