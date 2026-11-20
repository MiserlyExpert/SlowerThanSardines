"""Real-time-with-pause naval combat."""
import math
import random

import pygame

from .. import audio, data, gfx, render
from ..app import Scene
from ..battle import Battle
from ..config import H, T, TOP_ROW, W
from ..gfx import P
from .hud import draw_resources, tooltip

TASK_LABEL = dict(man='Manning', repair='Repairing', patch='Patching', fire='Firefighting',
                  fight='Brawling!', walk='Walking', idle='Idle', sabotage='Sabotage')

SYS_X0 = 36
SYS_W = 30
WEAP_X0 = 228
WEAP_W = 74
PANEL_Y = 252
HORIZON = 74
PLAYER_WL, ENEMY_WL = 202, 100
CREW_X = 534
BANNER_X, BANNER_Y = 150, 100


class SinkFx:
    """The enemy ship snaps in half: both halves tip up and slide under the waves."""
    DUR = 3.6

    def __init__(self, ship, ox, oy, t, interior):
        b = render.hull_bounds(ship, ox, oy).inflate(60, 60)
        b.top -= 30
        b.height += 30
        self.base = b.topleft
        self.waterline = oy + render.WATERLINE
        full = pygame.Surface(b.size, pygame.SRCALPHA)
        render.draw_ship(full, ship, ox - b.left, oy - b.top, t, interior=interior, sea=False, overlay=False)
        rng = random.Random(7)
        mid = ox - b.left + ship.gw * T // 2 + rng.randint(-8, 8)
        cut, x = [], mid
        for y in range(b.height):
            if y % 3 == 0:
                x = mid + rng.randint(-5, 5)
            cut.append(x)
        self.halves = []
        for side in (-1, 1):
            half = full.copy()
            for y, cx in enumerate(cut):
                if side < 0:
                    pygame.draw.line(half, (0, 0, 0, 0), (cx, y), (b.width, y))
                else:
                    pygame.draw.line(half, (0, 0, 0, 0), (0, y), (cx - 1, y))
            self.halves.append((side, half))
        self.crack = (b.left + mid, self.waterline - 20)
        self.width = b.width
        self.t = 0.0
        self.debris = [[self.crack[0] + rng.randint(-8, 8), self.crack[1] + rng.randint(-25, 10),
                        rng.uniform(-60, 60), rng.uniform(-90, -20), rng.uniform(0.8, 1.8),
                        rng.choice([P['wood1'], P['wood2'], P['wood3'], P['white']])] for _ in range(45)]

    def update(self, dt):
        self.t += dt
        for d in self.debris:
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[3] += 110 * dt
            if d[1] > self.waterline:      # bob on the surface
                d[1], d[3], d[2] = self.waterline, 0, d[2] * 0.9
            d[4] -= dt

    def draw(self, s, t):
        k = min(1.0, self.t / self.DUR)
        clip = pygame.Rect(self.base[0] - 60, 0, self.width + 120, self.waterline + 1)
        old = s.get_clip()
        s.set_clip(clip)
        for side, half in self.halves:
            tip = min(1.0, k * 1.8)
            ang = side * 28 * tip                 # the broken ends drop, bow and stern rear up
            img = pygame.transform.rotate(half, ang)
            cx = self.base[0] + half.get_width() // 2 + side * (4 + 22 * k)
            cy = self.base[1] + half.get_height() // 2 + 95 * max(0.0, k - 0.15) ** 1.4
            s.blit(img, img.get_rect(center=(int(cx), int(cy))))
        s.set_clip(old)
        x, y = self.crack[0], self.waterline
        r = int(14 + 70 * k)
        pygame.draw.ellipse(s, P['foam'], (x - r, y - 3, r * 2, 7), 1)
        for i in range(14):
            bx = x + math.sin(i * 2.3 + t) * (16 + i * 5)
            by = y - ((t * 25 + i * 9) % 14)
            pygame.draw.circle(s, P['foam'], (int(bx), int(by)), 1)
        if k < 0.25:
            rr = int(22 * (0.25 - k) / 0.25 + 2)
            pygame.draw.circle(s, P['yellow'], (x, self.crack[1]), rr)
            pygame.draw.circle(s, P['orange'], (x, self.crack[1]), max(1, rr - 5))
        for d in self.debris:
            if d[4] > 0:
                pygame.draw.line(s, d[5], (d[0], d[1]), (d[0] + 3, d[1] + 1))


class CombatScene(Scene):
    def __init__(self, app, enemy, enemy_key, fog=False, win=None, boss=False):
        super().__init__(app)
        self.enemy_key = enemy_key
        self.battle = Battle(self.gs, enemy, fog=fog, boss=boss, rng=random.Random(self.gs.rng.random()))
        self.enemy = enemy
        self.fog = fog
        self.win_bonus = win
        self.boss = boss
        self.paused = False
        self.t = 0.0
        self.aiming = None
        self.selected = []
        self.particles = []
        self.floaters = []
        self.banner = []
        self.shake = 0.0
        self.end_t = 0.0
        self.hover_room = None
        self.hover_eroom = None
        self.flashes = []
        p = self.gs.ship
        e = enemy
        self.gs.enemy = enemy
        self.player_base = (26, PLAYER_WL - render.WATERLINE)
        self.enemy_base = (522 - e.gw * T - 46, ENEMY_WL - render.WATERLINE)
        self.board_btn = gfx.Button((534, 324, 48, 18), "Board [B]", self.board, size=14)
        self.recall_btn = gfx.Button((586, 324, 48, 18), "Recall", self.recall, size=14)
        p.recoil, e.recoil = {}, {}
        self.muzzles = []
        self.smoke = []
        msg = f"{enemy.name} ({data.ENEMIES[enemy_key]['name']}) attacks!"
        self.say_banner(msg, P['white'])
        if fog:
            self.say_banner("Fog! Everyone's evasion is halved. Escape is slow.", P['fog'])
        self.sink = None
        self.flee_btn = gfx.Button((534, 292, 100, 18), "Make Sail!", self.flee, size=14)
        self.souls = []
        audio.play('bell')

    # ------------------------------------------------------------------
    @property
    def porig(self):
        bx, by = self.player_base
        return bx, by + int(math.sin(self.t * 1.3) * 1.5 + self.gs.ship.flood_frac() * 8)

    @property
    def eorig(self):
        bx, by = self.enemy_base
        return bx, by + int(math.sin(self.t * 1.3 + 1) * 1.5 + self.enemy.flood_frac() * 8)

    def origin_of(self, ship):
        return self.porig if ship is self.gs.ship else self.eorig

    def board(self):
        n = self.battle.player_board(self.selected)
        if n:
            audio.play('board')
            self.say_banner(f"{n} crew swing across on grappling lines! Fight your way down!", P['gold'])
        else:
            self.say_banner("Select crew standing on your TOP DECK to board.", P['orange'])

    def recall(self):
        n = self.battle.player_recall()
        if n:
            audio.play('board')
            self.say_banner(f"{n} crew swing home.", P['gold'])
        else:
            self.say_banner("Boarders must climb to the enemy's top deck to swing back.", P['orange'])

    def room_screen(self, ship, idx):
        ox, oy = self.origin_of(ship)
        cx, cy = ship.rooms[idx].center()
        return ox + cx, oy + cy

    def muzzle(self, ship, slot):
        d = render.aim_dir(ship)
        x, y = render.cannon_pos(ship, *self.origin_of(ship), slot)
        ship.recoil[slot] = 0.35
        audio.play('cannon')
        self.muzzles.append([x, y, 0.0, d])
        for i in range(8):
            self.smoke.append([x + random.uniform(-2, 2), y + random.uniform(-2, 2), d * random.uniform(15, 45),
                               random.uniform(-25, -5), 0.0, random.uniform(0.8, 1.6)])
        self.burst(x, y, [P['yellow'], P['orange'], P['white']], 6, 35)

    def say_banner(self, txt, col=None):
        self.banner.append([txt, col or P['white'], 3.5])
        self.banner = self.banner[-3:]

    def floater(self, txt, x, y, col):
        self.floaters.append([txt, x, y, col, 1.2])

    def burst(self, x, y, cols, n=12, spd=40):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(spd * 0.3, spd)
            self.particles.append([x, y, math.cos(a) * v, math.sin(a) * v - 10, random.uniform(0.3, 0.7),
                                   random.choice(cols)])

    # ------------------------------------------------------------------
    def flee(self):
        if self.battle.player_flee():
            audio.play('splash')

    def weapon_rect(self, i):
        return pygame.Rect(WEAP_X0 + i * WEAP_W, 290, WEAP_W - 4, 60)

    def sys_rect(self, i):
        return pygame.Rect(SYS_X0 + i * SYS_W, PANEL_Y + 4, SYS_W - 2, 100)

    def sys_names(self):
        return [n for n in data.SYS_ORDER if n in self.gs.ship.sys]

    def crew_list_rect(self, i):
        return pygame.Rect(CREW_X, 28 + i * 23, W - CREW_X - 4, 21)

    def handle(self, e):
        gs, ship, b = self.gs, self.gs.ship, self.battle
        if b.over:
            return
        if self.flee_btn.handle(e):
            return
        if gs.ship.grapple and (self.board_btn.handle(e) or self.recall_btn.handle(e)):
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif e.key == pygame.K_ESCAPE:
                if self.aiming is not None:
                    self.aiming = None
                elif self.selected:
                    self.selected = []
                else:
                    self.paused = True
            elif pygame.K_1 <= e.key <= pygame.K_4:
                i = e.key - pygame.K_1
                if i < len(ship.weapons):
                    self.click_weapon(i)
            elif e.key == pygame.K_a:
                self.selected = list(gs.crew)
            elif e.key == pygame.K_b and gs.ship.grapple:
                self.board()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            pos = e.pos
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            if e.button == 1:
                for i in range(len(ship.weapons)):
                    if self.weapon_rect(i).collidepoint(pos):
                        self.click_weapon(i)
                        return
                for i, n in enumerate(self.sys_names()):
                    if self.sys_rect(i).collidepoint(pos):
                        if n == 'guns':
                            for w in ship.weapons:
                                if not w.powered and ship.power_weapon(w):
                                    break
                        elif ship.add_power(n):
                            audio.play('click')
                        return
                if self.aiming is not None:
                    ri = render.room_at(self.enemy, *self.eorig, pos)
                    if ri is not None:
                        ship.weapons[self.aiming].target = ri
                        audio.play('click')
                        self.aiming = None
                    return
                for i, c in enumerate(gs.crew):
                    if self.crew_list_rect(i).collidepoint(pos):
                        self.select(c, shift)
                        return
                c = render.crew_at(ship, *self.porig, pos) or render.crew_at(self.enemy, *self.eorig, pos)
                if c:
                    self.select(c, shift)
                    return
                if pos[1] < PANEL_Y and not shift:
                    self.selected = []
            elif e.button == 3:
                for i, w in enumerate(ship.weapons):
                    if self.weapon_rect(i).collidepoint(pos):
                        ship.unpower_weapon(w)
                        w.target = None
                        if self.aiming == i:
                            self.aiming = None
                        return
                for i, n in enumerate(self.sys_names()):
                    if self.sys_rect(i).collidepoint(pos):
                        if n == 'guns':
                            for w in reversed(ship.weapons):
                                if w.powered:
                                    ship.unpower_weapon(w)
                                    break
                        else:
                            ship.remove_power(n)
                        return
                if self.aiming is not None:
                    self.aiming = None
                    return
                if self.selected:
                    moved = False
                    for c in self.selected:
                        ri = render.room_at(c.ship, *self.origin_of(c.ship), pos)
                        if ri is not None and c.alive and c.order_move(ri):
                            moved = True
                    if not any(render.room_at(c.ship, *self.origin_of(c.ship), pos) is not None
                               for c in self.selected):
                        return
                    if moved:
                        audio.play('click')
                    else:
                        self.say_banner("No room in there!", P['orange'])

    def select(self, c, add):
        if add:
            if c in self.selected:
                self.selected.remove(c)
            else:
                self.selected.append(c)
        else:
            self.selected = [c]
        audio.play('click')
        if c.cls == 'drunk' and random.random() < 0.4:
            audio.play('hic')
            c.say("*hic*", 1.2)

    def click_weapon(self, i):
        ship = self.gs.ship
        w = ship.weapons[i]
        if not w.powered:
            if not ship.power_weapon(w):
                self.say_banner("Not enough Gusto or Gun Deck power!", P['orange'])
                return
            audio.play('click')
            return
        self.aiming = None if self.aiming == i else i
        audio.play('click')

    # ------------------------------------------------------------------
    def update(self, dt):
        self.t += dt
        b = self.battle
        m = pygame.mouse.get_pos()
        self.hover_room = render.room_at(self.gs.ship, *self.porig, m)
        self.hover_eroom = render.room_at(self.enemy, *self.eorig, m)
        if not self.paused and not b.over:
            b.update(dt)
        if b.over:
            if b.over == 'win' and self.sink is None:
                self.sink = SinkFx(self.enemy, *self.eorig, self.t, self.can_see())
                audio.play('hit')
                audio.play('splash')
                self.shake = 1.0
                self.say_banner(f"{self.enemy.name} breaks in half!", P['gold'])
            if self.sink:
                self.sink.update(dt)
            self.end_t += dt
            if self.end_t > (SinkFx.DUR + 0.4 if self.sink else 1.6):
                self.finish()
                return
        self.selected = [c for c in self.selected if c.alive]
        for sh in (self.gs.ship, self.enemy):
            for k in list(sh.recoil):
                sh.recoil[k] -= dt
                if sh.recoil[k] <= 0:
                    del sh.recoil[k]
        for pr in b.projectiles:
            if pr['t'] >= 0 and not pr.get('fired'):
                pr['fired'] = True
                self.muzzle(pr['src'], pr['slot'])
        for m_ in self.muzzles:
            m_[2] += dt
        self.muzzles = [m_ for m_ in self.muzzles if m_[2] < 0.2]
        for p_ in self.smoke:
            p_[0] += p_[2] * dt
            p_[1] += p_[3] * dt
            p_[2] = p_[2] * (1 - 2.5 * dt) + 6 * dt   # slows down, drifts with the wind
            p_[3] *= (1 - 2.5 * dt)
            p_[4] += dt
        self.smoke = [p_ for p_ in self.smoke if p_[4] < p_[5]]
        self._consume_events()
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 60 * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        for f in self.floaters:
            f[2] -= 14 * dt
            f[4] -= dt
        self.floaters = [f for f in self.floaters if f[4] > 0]
        for bn in self.banner:
            bn[2] -= dt
        self.banner = [bn for bn in self.banner if bn[2] > 0]
        self.flashes = [[x, y, r + 60 * dt, life - dt] for x, y, r, life in self.flashes if life > 0]
        self.souls = [[x, y, a + dt] for x, y, a in self.souls if a + dt < 1.6]
        self.shake = max(0.0, self.shake - dt * 3)

    def _consume_events(self):
        b = self.battle
        gs = self.gs
        for ev in b.events:
            k = ev['kind']
            ship = ev.get('ship')
            if 'room' in ev and ship is not None:
                x, y = self.room_screen(ship, ev['room'])
            else:
                x, y = W // 2, 120
            mine = ship is gs.ship
            if k == 'shoot':
                pass
            elif k == 'hit':
                audio.play('hit')
                self.burst(x, y, [P['orange'], P['yellow'], P['red'], P['wood2']], 16, 50)
                if ev['dmg']:
                    self.floater(f"-{ev['dmg']}", x, y - 10, P['red'])
                elif ev.get('crew'):
                    self.floater("OUCH", x, y - 10, P['orange'])
                if mine:
                    self.shake = 0.6
            elif k == 'miss':
                audio.play('splash')
                self.floater("MISS", x, y - 10, P['lblue'])
                self.burst(x + random.randint(-40, 40), y + random.randint(-30, 30), [P['foam'], P['lblue']], 10, 30)
            elif k == 'block':
                audio.play('block')
                self.floater("BLOCKED", x, y - 10, P['gold'])
                self.flashes.append([x, y, 6, 0.4])
            elif k == 'fire':
                audio.play('fire')
                self.floater("FIRE!", x, y - 16, P['orange'])
            elif k == 'explode':
                audio.play('hit')
                audio.play('cannon')
                self.say_banner("THE POWDER MAGAZINE EXPLODES!", P['orange'])
                self.burst(x, y, [P['yellow'], P['orange'], P['red'], P['white']], 40, 90)
                self.shake = 1.2
                self.floater("-4", x, y - 14, P['red'])
            elif k == 'pboard':
                pass
            elif k == 'breach':
                self.floater("LEAK!", x, y - 22, P['lblue'])
            elif k == 'board':
                audio.play('board')
                self.say_banner(f"BOARDERS! {ev['n']} pirates swing aboard on ropes!", P['red'])
                self.burst(x, y, [P['white'], P['lgrey']], 14, 40)
            elif k == 'death':
                audio.play('death')
                c = ev['crew']
                ox_, oy_ = self.origin_of(ev['ship'])
                self.souls.append([ox_ + c.x, oy_ + c.y - 10, 0.0])
                col = P['red'] if c.side == 'player' else P['green']
                self.say_banner(f"{c.name} the {c.title} has perished.", col)
                if c.side == 'player' and gs.crew and random.random() < 0.6:
                    random.choice(gs.crew).say(random.choice(
                        ["Nooo! They owed me money!", "Rest easy, shipmate.", "I'll drink their share. For honour."]))
            elif k == 'enemy_flee':
                self.say_banner(f"{self.enemy.name} is trying to escape!", P['yellow'])
            elif k == 'angry':
                self.say_banner("Someone spilled the Admiral's tea! His guns reload faster!", P['red'])
                adm = [c for c in self.enemy.crew if c.cls == 'admiral']
                if adm:
                    adm[0].say("MY TEA! NOW I'M CROSS!", 3)
        b.events.clear()

    def finish(self):
        from .endings import GameOverScene, VictoryScene
        from .event import EventScene
        b, gs = self.battle, self.gs
        over = b.over
        b.cleanup()
        gs.enemy = None
        if over == 'lose':
            audio.play('lose')
            self.app.replace(GameOverScene(self.app))
            return
        gs.sector.node.cleared = True
        if over in ('win', 'win_crew'):
            gs.stats['wins'] += 1
            unlocks = gs.unlock_notes(wins=1, ghosts=1 if self.enemy_key == 'ghost' else 0,
                                      victories=1 if self.boss else 0)
            audio.play('win')
            if self.boss:
                self.app.replace(VictoryScene(self.app))
                return
            loot = gs.loot(self.enemy_key, over)
            if self.win_bonus:
                for k, v in self.win_bonus.items():
                    if k == 'text':
                        continue
                    if k in loot and isinstance(v, int) and isinstance(loot[k], int):
                        loot[k] += v
                    else:
                        loot[k] = v
            if over == 'win':
                text = random.choice([
                    "The {enemy} slips beneath the waves, gurgling something rude. You fish valuables out of the flotsam.",
                    "Down she goes! The {enemy}'s crew paddles off on a floating barrel, shaking their fists.",
                    "Victory! The {enemy} sinks with all the dignity of a dropped pie.",
                ])
            else:
                text = ("The {enemy}'s crew is no more. You help yourself to the hold, which is very rude but "
                        "extremely profitable.")
            if self.win_bonus and self.win_bonus.get('text'):
                text += "\n\n" + self.win_bonus['text']
            text = text.replace('{enemy}', self.enemy.name)
            for u in unlocks:
                text += "\n\n" + u
            loot['text'] = "Spoils of war:"
            ev = dict(id='loot', title='Victory!', text=text,
                      choices=[dict(text="Collect the spoils.", out=loot)])
            self.app.replace(EventScene(self.app, ev))
        elif over == 'fled':
            ev = dict(id='fled', text=random.choice([
                "You crowd on every scrap of sail and leave the enemy in your wake. "
                "Discretion is the better part of not being sunk.",
                "You escape! Somewhere behind you, the enemy captain shakes a fist and drops his hat in the sea."]),
                choices=[dict(text="Continue.", out={})])
            self.app.replace(EventScene(self.app, ev))
        elif over == 'enemy_fled':
            ev = dict(id='efled', text=f"{self.enemy.name} limps away over the horizon. Cowards. "
                                       f"Smart cowards, but cowards.", choices=[dict(text="Continue.", out={})])
            self.app.replace(EventScene(self.app, ev))

    # ------------------------------------------------------------------
    def draw(self, s):
        t = self.t
        gs, ship, en, b = self.gs, self.gs.ship, self.enemy, self.battle
        self._sky(s, t)
        gfx.draw_sea(s, t, HORIZON)
        sx = int(random.uniform(-2, 2) * self.shake) if self.shake else 0
        sy = int(random.uniform(-2, 2) * self.shake) if self.shake else 0
        epan = pygame.Rect(6, 28, 200, 66)
        px, py = self.porig
        px += sx
        py += sy
        ex, ey = self.eorig
        targets = [w.target for w in ship.weapons if w.target is not None]
        see = self.can_see()
        # the enemy is further away, so it is drawn first
        if self.sink:
            self.sink.draw(s, t)
        else:
            self._shields(s, en, ex, ey)
            render.draw_ship(s, en, ex, ey, t, interior=see, selected=self.selected,
                             hover=self.hover_eroom if (self.aiming is not None or self.selected) else None,
                             targets=targets)
        if self.fog:
            gfx.draw_fog(s, t)
        self._shields(s, ship, px, py)
        render.draw_ship(s, ship, px, py, t, interior=True, selected=self.selected,
                         hover=self.hover_room if self.selected else None)
        # projectiles
        for p in b.projectiles:
            if p['t'] < 0:
                continue
            k = min(1.0, p['t'] / p['dur'])
            src, dst = p['src'], p['dst']
            x0, y0 = render.cannon_pos(src, *self.origin_of(src), p['slot'])
            x1, y1 = self.room_screen(dst, p['room'])
            lob = p['w'].get('pierce')
            x = x0 + (x1 - x0) * k
            y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * (70 if lob else 28)
            # trail
            for j in range(1, 4):
                kk = max(0.0, k - j * 0.025)
                tx = x0 + (x1 - x0) * kk
                ty = y0 + (y1 - y0) * kk - math.sin(math.pi * kk) * (70 if lob else 28)
                s.set_at((int(tx), int(ty)), (170, 170, 180) if j < 3 else (110, 110, 120))
            if p['key'] == 'firebomb':
                pygame.draw.circle(s, P['orange'], (int(x), int(y)), 3)
                s.set_at((int(x), int(y) - 4), P['yellow'])
            elif p['key'] == 'grapeshot':
                for j in range(3):
                    s.set_at((int(x) + j * 2 - 2, int(y) + (j % 2) * 2), P['lgrey'])
            elif p['key'] == 'chain_shot':
                pygame.draw.circle(s, P['black'], (int(x) - 3, int(y)), 2)
                pygame.draw.circle(s, P['black'], (int(x) + 3, int(y)), 2)
                pygame.draw.line(s, P['grey'], (int(x) - 3, int(y)), (int(x) + 3, int(y)))
            else:
                pygame.draw.circle(s, P['black'], (int(x), int(y)), 3)
                s.set_at((int(x) - 1, int(y) - 1), P['lgrey'])
        if self.smoke:
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            for x, y, vx, vy, age, life in self.smoke:
                k = age / life
                rad = int(2 + 7 * k)
                a = int(150 * (1 - k))
                pygame.draw.circle(layer, (200, 200, 205, a), (int(x), int(y)), rad)
                pygame.draw.circle(layer, (150, 150, 160, a // 2), (int(x) + 1, int(y) + 1), max(1, rad - 2))
            s.blit(layer, (0, 0))
        for x, y, age, sgn in self.muzzles:
            k = age / 0.2
            r = int(5 - 3 * k)
            pygame.draw.circle(s, P['orange'], (int(x), int(y + sgn * 2)), r + 2)
            pygame.draw.circle(s, P['yellow'], (int(x), int(y + sgn * 1)), r)
            pygame.draw.circle(s, P['white'], (int(x), int(y)), max(1, r - 2))
            for dx in (-1, 0, 1):
                pygame.draw.line(s, P['yellow'], (x, y), (x + dx * 6, y + sgn * (9 - 4 * k)))
        for x, y, r, life in self.flashes:
            pygame.draw.circle(s, P['gold'], (int(x), int(y)), int(r), 1)
        for p in self.particles:
            s.set_at((int(p[0]), int(p[1])), p[5])
            s.set_at((int(p[0]) + 1, int(p[1])), p[5])
        render.draw_barks(s, ship, px, py)
        if not self.sink:
            render.draw_barks(s, en, ex, ey, ('player', 'enemy') if see else ('player',))
        for x, y, age in self.souls:
            k = age / 1.6
            col = P['white'] if k < 0.6 else P['lgrey']
            pygame.draw.ellipse(s, P['gold'], (int(x) - 3, int(y - 26 * k) - 3, 7, 3), 1)
            s.set_at((int(x), int(y - 26 * k) + 1), col)
        for txt, x, y, col, life in self.floaters:
            gfx.text(s, txt, int(x), int(y), col, 16, shadow=P['black'], align='center')
        self._enemy_panel(s, epan, see)
        self._top(s)
        self._crew_list(s)
        self._player_stats(s, px, py)
        self._bottom(s)
        # aiming cursor
        m = pygame.mouse.get_pos()
        if self.aiming is not None:
            pygame.draw.circle(s, P['red'], m, 6, 1)
            pygame.draw.line(s, P['red'], (m[0] - 9, m[1]), (m[0] + 9, m[1]))
            pygame.draw.line(s, P['red'], (m[0], m[1] - 9), (m[0], m[1] + 9))
        # banners
        y = BANNER_Y
        for txt, col, life in self.banner:
            w = gfx.text_w(txt) + 12
            bx = max(2, min(BANNER_X - w // 2, CREW_X - w - 4))
            strip = pygame.Surface((w, 11), pygame.SRCALPHA)
            strip.fill((8, 14, 28, 200))
            s.blit(strip, (bx, y - 2))
            gfx.text(s, txt, bx + 6, y, col)
            y += 12
        if self.paused and not b.over:
            gfx.text_outline(s, "PAUSED", 400, 196, P['yellow'], 24, align='center')
            gfx.text(s, "space to resume", 400, 216, P['white'], shadow=P['black'], align='center')
        self._tooltips(s, m)

    def can_see(self):
        nest = self.gs.ship.sys.get('nest')
        boarded = any(c.side == 'player' for c in self.enemy.crew)
        return bool((nest and nest.eff() >= 1) or boarded)

    def _sky(self, s, t):
        for y in range(24, HORIZON):
            k = (y - 24) / (HORIZON - 24)
            col = (int(110 + 80 * k), int(160 + 60 * k), int(205 + 30 * k))
            if self.fog:
                col = tuple(int(c * 0.6 + 200 * 0.4) for c in col)
            pygame.draw.line(s, col, (0, y), (W, y))
        for i in range(4):
            cx = int((i * 173 + t * (3 + i)) % (W + 120)) - 60
            cy = 34 + (i * 13) % 28
            for dx, r in ((0, 7), (9, 10), (20, 7), (6, 5)):
                pygame.draw.circle(s, (244, 246, 250), (cx + dx, cy), r)
        pygame.draw.line(s, (180, 210, 230), (0, HORIZON), (W, HORIZON))

    def _shields(self, s, ship, ox, oy):
        hb = render.hull_bounds(ship, ox, oy)
        hb.top -= 14
        hb.height += 14
        for i in range(ship.shield_layers):
            r = hb.inflate(26 + i * 8, 20 + i * 8)
            pygame.draw.ellipse(s, P['lblue'] if i % 2 == 0 else P['teal'], r, 1)
        ml = ship.max_layers()
        if ship.shield_layers < ml and ship.shield_t > 0:
            r = hb.inflate(26, 20)
            pygame.draw.arc(s, P['lblue'], r, 0, math.tau * ship.shield_t / 2.0, 1)

    def _top(self, s):
        gs = self.gs
        pygame.draw.rect(s, P['navy'], (0, 0, W, 24))
        pygame.draw.line(s, P['black'], (0, 24), (W, 24))
        x = draw_resources(s, gs)
        if self.fog:
            gfx.text(s, "FOG", x + 6, 6, P['fog'], 16)

    def _crew_list(self, s):
        for i, c in enumerate(self.gs.crew):
            r = self.crew_list_rect(i)
            sel = c in self.selected
            pygame.draw.rect(s, P['navy2'] if not sel else P['dgreen'], r)
            pygame.draw.rect(s, P['black'], r, 1)
            s.blit(gfx.crew_sprite(c.cls, c.skin), (r.left + 3, r.top + 3))
            gfx.text(s, c.name[:16], r.left + 15, r.top + 3, P['white'], 14)
            where = "ABOARD ENEMY" if c.ship is self.enemy else c.ship.rooms[c.room].title
            gfx.text(s, TASK_LABEL.get(c.task, c.task) if c.task != 'idle' else where[:15], r.left + 15, r.top + 12,
                     P['gold'] if c.ship is self.enemy else P['lgrey'], 14)
            gfx.bar(s, r.left + 3, r.bottom - 4, 9, 2, c.hp / c.max_hp,
                    P['green'] if c.hp > c.max_hp * 0.35 else P['red'])

    def _player_stats(self, s, px, py):
        ship = self.gs.ship
        r = pygame.Rect(296, 176, 226, 52)
        gfx.panel(s, r, 'dark')
        gfx.text(s, ship.name, r.left + 6, r.top + 5, P['gold'])
        ev = ship.evasion(self.fog)
        gfx.text(s, f"Evasion {ev}%", r.left + 6, r.top + 17, P['white'])
        gfx.text(s, f"Bulwarks {ship.shield_layers}/{ship.max_layers()}", r.left + 84, r.top + 17, P['lblue'])
        y = r.top + 29
        if not ship.manned('helm'):
            gfx.text(s, "Helm unmanned! No evasion.", r.left + 6, y, P['orange'])
            y += 11
        flood = ship.flood_frac()
        if flood > 0.05:
            gfx.text(s, f"Flooding {int(flood * 100)}%: ship sluggish", r.left + 6, y, P['lblue'])
            y += 11
        fires = sum(1 for rm in ship.rooms if rm.fire > 0)
        if fires:
            gfx.text(s, f"{fires} room{'s' if fires > 1 else ''} on fire!", r.left + 6, y, P['orange'])

    def _enemy_panel(self, s, r, see):
        en = self.enemy
        if self.sink:
            return
        gfx.panel(s, r, 'dark')
        x = r.left + 6
        gfx.text(s, en.name, x, r.top + 5, P['red'])
        gfx.text(s, data.ENEMIES[self.enemy_key]['name'], x, r.top + 16, P['lgrey'])
        per = 4 if en.hull_max <= 36 else 3
        for i in range(en.hull_max):
            col = P['red'] if i < en.hull else P['dgrey']
            pygame.draw.rect(s, col, (x + i * per, r.top + 28, per - 1, 7))
        gfx.text(s, f"Evasion {en.evasion(self.fog)}%", x, r.top + 40, P['white'])
        gfx.text(s, f"Bulwarks {en.shield_layers}/{en.max_layers()}", x + 78, r.top + 40, P['lblue'])
        y = r.top + 52
        if en.fleeing:
            gfx.text(s, "FLEEING!", x, y, P['yellow'])
            gfx.bar(s, x + 50, y + 1, 60, 5, en.escape, P['yellow'])
            y += 11
        if self.battle.angry:
            gfx.text(s, "ENRAGED: reloads faster", x, y, P['red'])
            y += 11
        if not see:
            gfx.text(s, "Crow's Nest down: crew hidden", x, r.bottom - 12, P['lgrey'])
        nest = self.gs.ship.sys.get('nest')
        if nest and nest.eff() >= 2:
            yy = r.bottom - 34
            for i, w in enumerate(en.weapons):
                cx = x + (i % 2) * 82
                cy = yy + (i // 2) * 14
                gfx.text(s, w.name.split(' ')[0], cx, cy, P['lgrey'])
                gfx.bar(s, cx, cy + 9, 74, 2, w.charge, P['red'])
        elif see:
            gfx.text(s, "Crow's Nest Lv2 shows reloads", x, r.bottom - 12, P['grey'])

    def _bottom(self, s):
        gs, ship = self.gs, self.gs.ship
        pygame.draw.rect(s, P['navy'], (0, PANEL_Y, W, H - PANEL_Y))
        pygame.draw.line(s, P['black'], (0, PANEL_Y), (W, PANEL_Y))
        m = pygame.mouse.get_pos()
        # gusto
        free = ship.reactor_free()
        gfx.text(s, "GUSTO", 6, PANEL_Y + 6, P['gold'])
        gfx.text(s, "SYSTEMS", SYS_X0 + 4, PANEL_Y + 6, P["gold"])
        for i in range(min(ship.gusto, 18)):
            col = P['green'] if i < free else P['dgrey']
            pygame.draw.rect(s, col, (8, H - 18 - i * 5, 16, 4))
        s.blit(gfx.icon('bolt'), (13, H - 12))
        # systems
        for i, n in enumerate(self.sys_names()):
            r = self.sys_rect(i)
            sysm = ship.sys[n]
            hover = r.collidepoint(m)
            if hover:
                pygame.draw.rect(s, P['navy2'], r)
            ic = gfx.icon(n, P['red'] if sysm.damage >= sysm.level else None)
            s.blit(ic, (r.centerx - 4, H - 13))
            for j in range(sysm.level):
                by = H - 20 - j * 5
                rr = pygame.Rect(r.centerx - 6, by, 12, 4)
                if j >= sysm.level - sysm.damage:
                    pygame.draw.rect(s, P['red'], rr)
                elif sysm.sub:
                    pygame.draw.rect(s, P['lgrey'], rr)
                elif j < sysm.power:
                    pygame.draw.rect(s, P['green'], rr)
                else:
                    pygame.draw.rect(s, P['dgrey'], rr, 1)
            man = ship.manned(n)
            if man:
                s.set_at((r.centerx + 8, H - 9), P['yellow'])
                s.set_at((r.centerx + 9, H - 9), P['yellow'])
        # weapons
        gfx.text(s, "CANNONS", WEAP_X0, PANEL_Y + 6, P['gold'])
        gfx.text(s, "1-4 or click to select, then click an enemy room", WEAP_X0 + 48, PANEL_Y + 6, P['grey'])
        from .hangar import draw_tag
        for i, w in enumerate(ship.weapons):
            r = self.weapon_rect(i)
            col = P['navy2']
            if self.aiming == i:
                col = P['dred']
            elif r.collidepoint(m):
                col = P['dgrey']
            pygame.draw.rect(s, col, r)
            pygame.draw.rect(s, P['yellow'] if self.aiming == i else (P['green'] if w.powered else P['black']), r, 1)
            gfx.text(s, f"{i + 1}", r.left + 4, r.top + 4, P['gold'])
            name = w.name if gfx.text_w(w.name) <= r.width - 16 else w.name.split(' ')[0]
            gfx.text(s, name, r.left + 12, r.top + 4, P['white'] if w.powered else P['lgrey'])
            gfx.bar(s, r.left + 4, r.top + 15, r.width - 8, 4, w.charge,
                    P['yellow'] if w.charge >= 1 else P['orange'])
            for j in range(w.power):
                pygame.draw.rect(s, P['green'] if w.powered else P['dgrey'], (r.left + 4 + j * 6, r.top + 23, 4, 6))
            if w.d.get('ammo'):
                s.blit(gfx.icon('ball'), (r.left + 6 + w.power * 6, r.top + 23))
            tx = r.left + 4
            for tag in data.weapon_tags(w.d)[:2]:
                if tx + gfx.text_w(tag) + 4 > r.right - 2:
                    break
                tx += draw_tag(s, tag, tx, r.top + 34) + 2
            if w.target is not None:
                status, scol = "TARGET SET", P['red']
            elif w.powered:
                status, scol = "no target", P['lgrey']
            else:
                status, scol = "click: power", P['grey']
            gfx.text(s, status, r.left + 4, r.top + 46, scol)
        # escape
        e = ship.escape
        fb = self.flee_btn
        fb.enabled = e >= 1.0
        gfx.text(s, "ESCAPE", 534, PANEL_Y + 6, P['gold'])
        if not ship.can_escape():
            gfx.text(s, "needs manned helm", 534, 268, P['orange'])
        else:
            gfx.text(s, "charging..." if e < 1 else "ready!", 534, 268, P['lgrey'])
        gfx.bar(s, 534, 282, 100, 5, e, P['teal'], border=P['black'])
        fb.draw(s, m)
        if ship.grapple:
            cd = self.battle.board_cd
            gfx.text(s, "GRAPPLING HOOKS" if cd <= 0 else f"HOOKS: {cd:.0f}s", 534, 314, P['gold'])
            self.board_btn.enabled = cd <= 0
            self.board_btn.draw(s, m)
            self.recall_btn.draw(s, m)
        else:
            gfx.text(s, "SPACE pause", 534, 318, P['grey'])
            gfx.text(s, "R-click: move crew", 534, 329, P['grey'])
            gfx.text(s, "Hooks sold in port", 534, 340, P['dgrey'])

    def _tooltips(self, s, m):
        ship = self.gs.ship
        for i, n in enumerate(self.sys_names()):
            if self.sys_rect(i).collidepoint(m):
                d = data.SYSTEMS[n]
                sysm = ship.sys[n]
                extra = " (no power needed)" if sysm.sub else " L-click +power, R-click -power."
                if n == 'guns':
                    extra = " Click cannons to power them."
                tooltip(s, f"{d['title']} Lv{sysm.level}: {d['desc']}{extra}", m, 220)
                return
        for i, w in enumerate(ship.weapons):
            if self.weapon_rect(i).collidepoint(m):
                d = w.d
                stats = (f"{d['shots']} shot(s), {d['dmg'] + d.get('hull', 0)} hull dmg, {d['charge']:.1f}s reload, "
                         f"{d['power']} power. [{' '.join(data.weapon_tags(d))}] Right-click to unpower.")
                tooltip(s, f"{d['name']}: {d['desc']} {stats}", m, 220)
                return
        for i, c in enumerate(self.gs.crew):
            if self.crew_list_rect(i).collidepoint(m):
                tooltip(s, f"{c.name} the {c.title} ({int(c.hp)}/{c.max_hp}). {c.d['desc']}", m, 220)
                return
        if m[1] < PANEL_Y and m[0] < CREW_X:
            for sh in (self.gs.ship, self.enemy):
                ri = render.room_at(sh, *self.origin_of(sh), m)
                if ri is not None and not (self.sink and sh is self.enemy):
                    r = sh.rooms[ri]
                    if sh is self.enemy and not self.can_see() and not r.sys:
                        return
                    desc = data.SYSTEMS[r.sys]['desc'] if r.sys else data.FLAVOR_DESC.get(r.kind, '')
                    extra = []
                    if r.fire > 0:
                        extra.append("ON FIRE")
                    if r.breach:
                        extra.append("LEAKING")
                    if r.water > 5:
                        extra.append(f"{int(r.water)}% flooded")
                    tooltip(s, f"{r.title}. {desc} {' '.join(extra)}", (m[0], m[1] + 10), 200)
                    return
