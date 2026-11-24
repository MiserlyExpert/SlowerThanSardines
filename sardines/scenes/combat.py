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

PANEL_Y = 288             # top of the control bar
HANDS_X = 2
SYS_X0 = 34
SYS_W = 27
WEAP_X0 = 200
WEAP_W = 68
RIGHT_X = 474
HORIZON = 112
PLAYER_O = (20, 132)      # player ship grid origin
ENEMY_OY = 34
CHIP_W = 30
BANNER_Y = 88


class SinkFx:
    """The enemy ship snaps in half: both halves tip up and slide under the waves."""
    DUR = 3.6

    def __init__(self, ship, ox, oy, t, interior):
        b = render.hull_bounds(ship, ox, oy).inflate(60, 60)
        b.top -= 30
        b.height += 30
        self.base = b.topleft
        self.waterline = oy + max(r.floor_y for r in ship.rooms) + 5
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
        self.player_base = PLAYER_O
        self.enemy_base = (W - 8 - e.gw * T - 60, ENEMY_OY)
        self.board_btn = gfx.Button((RIGHT_X + 2, 334, 78, 16), "Board [B]", self.board, size=14)
        self.recall_btn = gfx.Button((RIGHT_X + 84, 334, 76, 16), "Recall", self.recall, size=14)
        self.hit_flash = {}
        self.hover_crew = None
        p.recoil, e.recoil = {}, {}
        self.muzzles = []
        self.smoke = []
        msg = f"{enemy.name} ({data.ENEMIES[enemy_key]['name']}) attacks!"
        self.say_banner(msg, P['white'])
        if fog:
            self.say_banner("Fog! Everyone's evasion is halved. Escape is slow.", P['fog'])
        self.sink = None
        self.flee_btn = gfx.Button((RIGHT_X + 2, 312, 160, 16), "Make Sail!", self.flee, size=14)
        self.souls = []
        audio.play('bell')
        audio.set_mood('boss' if boss else 'battle')

    # ------------------------------------------------------------------
    @property
    def porig(self):
        bx, by = self.player_base
        return bx, by + int(math.sin(self.t * 1.3) * 1.5)

    @property
    def eorig(self):
        bx, by = self.enemy_base
        return bx, by + int(math.sin(self.t * 1.3 + 1) * 1.5)

    def origin_of(self, ship):
        return self.porig if ship is self.gs.ship else self.eorig

    def board(self):
        n = self.battle.player_board(self.selected)
        if n:
            audio.play('board')
            self.say_banner(f"{n} crew swing across on grappling lines! Fight your way down!", P['gold'])
        else:
            if not self.gs.ship.grapple:
                self.say_banner("You need Grappling Hooks (sold in port) to board.", P['orange'])
            else:
                self.say_banner("Select crew, send them to your TOP DECK, then press Board.", P['orange'])

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
        return pygame.Rect(WEAP_X0 + i * WEAP_W, PANEL_Y + 14, WEAP_W - 4, 54)

    def sys_rect(self, i):
        return pygame.Rect(SYS_X0 + i * SYS_W, PANEL_Y + 12, SYS_W - 2, 58)

    def sys_names(self):
        return [n for n in data.SYS_ORDER if n in self.gs.ship.sys]

    def crew_list_rect(self, i):
        return pygame.Rect(4 + i * (CHIP_W + 2), 26, CHIP_W, 36)

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
                self.say_banner("Not enough free Hands, or the Gun Deck is full. Take Hands off another station.",
                                P['orange'])
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
        self.hover_crew = render.crew_at(self.gs.ship, *self.porig, m) or render.crew_at(self.enemy, *self.eorig, m)
        for k in list(self.hit_flash):
            self.hit_flash[k] -= dt
            if self.hit_flash[k] <= 0:
                del self.hit_flash[k]
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
                self.hit_flash[(id(ship), ev['room'])] = 0.45
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
                self.floater("HOLE IN THE HULL!", x, y - 22, P['lblue'])
            elif k == 'leak':
                self.floater("-1 leak", x, y - 6, P['lblue'])
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
            gs.enemy_had_hold = self.enemy.module_level('hold') > 0
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
            for g in getattr(b, 'risen', []):
                text += f"\n\n{g.name} rises from the Crypt, slightly see-through but ready for duty."
            loot['text'] = "Spoils of war:"
            choices = [dict(text="Collect the spoils.", out=loot)]
            if random.random() < gs.prisoner_chance():
                faction = data.ENEMIES[self.enemy_key].get('faction')
                cls = {'crown': 'marine', 'ghost': 'ghost'}.get(faction, 'pirate')
                ransom = 15 + 8 * gs.sector_idx
                text += f"\n\nYou've taken a prisoner and thrown them in the Brig. They look sheepish."
                choices = [dict(text=f"Ransom the prisoner (+{ransom} doubloons).",
                                out=dict(loot, doubloons=loot.get('doubloons', 0) + ransom)),
                           dict(text="Offer the prisoner a job.", out=dict(loot, add_crew=cls))]
            ev = dict(id='loot', title='Victory!', text=text, choices=choices)
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
    def can_see(self):
        nest = self.gs.ship.sys.get('nest')
        boarded = any(c.side == 'player' for c in self.enemy.crew)
        return bool((nest and nest.eff() >= 1) or boarded)

    def room_rect(self, ship, idx):
        ox, oy = self.origin_of(ship)
        r = ship.rooms[idx]
        return pygame.Rect(ox + r.gx * T, oy + r.gy * render.RH, r.w * T, render.RH)

    def draw(self, s):
        t = self.t
        gs, ship, en, b = self.gs, self.gs.ship, self.enemy, self.battle
        self._sky(s, t)
        gfx.draw_sea(s, t, HORIZON)
        px, py = self.porig
        if self.shake:
            px += int(random.uniform(-2, 2) * self.shake)
            py += int(random.uniform(-2, 2) * self.shake)
        ex, ey = self.eorig
        see = self.can_see()
        targets = [w.target for w in ship.weapons if w.target is not None]
        boarders_aboard = any(c in self.selected and c.ship is en for c in self.selected)
        # the enemy is further away, so it is drawn first
        if self.sink:
            self.sink.draw(s, t)
        else:
            self._shields(s, en, ex, ey)
            render.draw_ship(s, en, ex, ey, t, interior=see, selected=self.selected,
                             hover=self.hover_eroom if (self.aiming is not None or boarders_aboard) else None,
                             targets=targets, hover_crew=self.hover_crew)
        if self.fog:
            gfx.draw_fog(s, t)
        self._shields(s, ship, px, py)
        render.draw_ship(s, ship, px, py, t, interior=True, selected=self.selected,
                         hover=self.hover_room if self.selected else None, hover_crew=self.hover_crew)
        self._attack_markers(s, t)
        self._boarding_hint(s, t)
        # projectiles
        for p in b.projectiles:
            if p['t'] < 0:
                continue
            k = min(1.0, p['t'] / p['dur'])
            src, dst = p['src'], p['dst']
            x0, y0 = render.cannon_pos(src, *self.origin_of(src), p['slot'])
            x1, y1 = self.room_screen(dst, p['room'])
            lob = p['w'].get('pierce')
            arc = 80 if lob else 34
            x = x0 + (x1 - x0) * k
            y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * arc
            for j in range(1, 5):
                kk = max(0.0, k - j * 0.02)
                tx = x0 + (x1 - x0) * kk
                ty = y0 + (y1 - y0) * kk - math.sin(math.pi * kk) * arc
                s.set_at((int(tx), int(ty)), (190, 190, 200) if j < 3 else (120, 120, 130))
            r = 3 if src is ship else 4
            if p['key'] in ('firebomb', 'hot_shot', 'brimstone'):
                pygame.draw.circle(s, P['orange'], (int(x), int(y)), r)
                s.set_at((int(x), int(y) - r - 1), P['yellow'])
            elif p['key'] == 'grapeshot':
                for j in range(4):
                    s.set_at((int(x) + j * 2 - 3, int(y) + (j % 2) * 2), P['lgrey'])
            elif p['key'] == 'chain_shot':
                pygame.draw.circle(s, P['black'], (int(x) - 4, int(y)), 2)
                pygame.draw.circle(s, P['black'], (int(x) + 4, int(y)), 2)
                pygame.draw.line(s, P['grey'], (int(x) - 4, int(y)), (int(x) + 4, int(y)))
            else:
                pygame.draw.circle(s, P['black'], (int(x), int(y)), r)
                s.set_at((int(x) - 1, int(y) - 1), P['lgrey'])
        # smoke, muzzle flashes, sparks
        if self.smoke:
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            for x, y, vx, vy, age, life in self.smoke:
                k = age / life
                rad = int(2 + 8 * k)
                a = int(150 * (1 - k))
                pygame.draw.circle(layer, (205, 205, 210, a), (int(x), int(y)), rad)
                pygame.draw.circle(layer, (150, 150, 160, a // 2), (int(x) + 1, int(y) + 1), max(1, rad - 2))
            s.blit(layer, (0, 0))
        for x, y, age, d in self.muzzles:
            k = age / 0.2
            r = int(6 - 3 * k)
            pygame.draw.circle(s, P['orange'], (int(x + d * 2), int(y)), r + 2)
            pygame.draw.circle(s, P['yellow'], (int(x + d), int(y)), r)
            pygame.draw.circle(s, P['white'], (int(x), int(y)), max(1, r - 2))
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
            pygame.draw.ellipse(s, P['gold'], (int(x) - 4, int(y - 30 * k) - 4, 9, 3), 1)
            s.set_at((int(x), int(y - 30 * k) + 1), P['white'])
        for txt, x, y, col, life in self.floaters:
            gfx.text(s, txt, int(x), int(y), col, shadow=P['black'], align='center')
        # HUD
        self._top(s)
        self._crew_chips(s)
        self._player_status(s)
        self._enemy_panel(s, see)
        self._banners(s)
        self._bottom(s)
        m = pygame.mouse.get_pos()
        if self.aiming is not None and self.aiming < len(ship.weapons):
            mx0, my0 = render.cannon_pos(ship, px, py, self.aiming)
            n = int(math.hypot(m[0] - mx0, m[1] - my0) / 6)
            for i in range(n):
                if i % 2 == 0:
                    k0, k1 = i / max(1, n), (i + 1) / max(1, n)
                    pygame.draw.line(s, P['red'], (mx0 + (m[0] - mx0) * k0, my0 + (m[1] - my0) * k0),
                                     (mx0 + (m[0] - mx0) * k1, my0 + (m[1] - my0) * k1))
            pygame.draw.circle(s, P['red'], m, 7, 1)
            pygame.draw.line(s, P['red'], (m[0] - 10, m[1]), (m[0] + 10, m[1]))
            pygame.draw.line(s, P['red'], (m[0], m[1] - 10), (m[0], m[1] + 10))
            gfx.text(s, "click an enemy room", m[0] + 10, m[1] + 8, P['white'], shadow=P['black'])
        if self.paused and not b.over:
            gfx.text_outline(s, "PAUSED", W // 2, 232, P['yellow'], 24, align='center')
            gfx.text(s, "press SPACE to resume", W // 2, 252, P['white'], shadow=P['black'], align='center')
        self._tooltips(s, m)

    # ------------------------------------------------------------------
    def _attack_markers(self, s, t):
        """Make it obvious what is being shot at, and what was just hit."""
        ship, en = self.gs.ship, self.enemy
        pulse = 0.5 + 0.5 * math.sin(t * 8)
        # our targets on the enemy, with cannon numbers
        if not self.sink:
            badges = {}
            for i, w in enumerate(ship.weapons):
                if w.target is not None:
                    badges.setdefault(w.target, []).append(i + 1)
            for ri, nums in badges.items():
                r = self.room_rect(en, ri)
                col = (255, int(60 + 80 * pulse), 60)
                pygame.draw.rect(s, col, r.inflate(2, 2), 2)
                label = ' '.join(str(n) for n in nums)
                w = gfx.text_w(label) + 6
                pygame.draw.rect(s, P['red'], (r.right - w - 1, r.bottom - 11, w, 10))
                gfx.text(s, label, r.right - w + 2, r.bottom - 10, P['white'])
        # incoming: rooms the enemy's loaded cannons are aimed at
        for w in en.weapons:
            if w.target is not None and w.charge > 0.5 and not self.sink:
                r = self.room_rect(ship, w.target)
                if int(t * 6) % 2:
                    pygame.draw.rect(s, P['red'], r, 1)
                gfx.text(s, "!", r.centerx, r.top + 2, P['red'], 24, align='center')
        # hit flashes
        for (sid, ri), life in self.hit_flash.items():
            sh = ship if sid == id(ship) else en
            if sh is en and self.sink:
                continue
            r = self.room_rect(sh, ri)
            fl = pygame.Surface(r.size, pygame.SRCALPHA)
            fl.fill((255, 240, 200, int(170 * life / 0.45)))
            s.blit(fl, r.topleft)

    def _boarding_hint(self, s, t):
        if not self.gs.ship.grapple:
            return
        m = pygame.mouse.get_pos()
        if not self.board_btn.rect.collidepoint(m):
            return
        for sh in (self.gs.ship, self.enemy):
            for ri in sh.top_rooms():
                r = self.room_rect(sh, ri)
                if int(t * 4) % 2:
                    pygame.draw.rect(s, P['gold'], r, 2)

    def _sky(self, s, t):
        for y in range(22, HORIZON):
            k = (y - 22) / (HORIZON - 22)
            col = (int(110 + 80 * k), int(160 + 60 * k), int(205 + 30 * k))
            if self.fog:
                col = tuple(int(c * 0.6 + 200 * 0.4) for c in col)
            pygame.draw.line(s, col, (0, y), (W, y))
        for i in range(4):
            cx = int((i * 173 + t * (3 + i)) % (W + 120)) - 60
            cy = 40 + (i * 17) % 40
            for dx, r in ((0, 7), (9, 10), (20, 7), (6, 5)):
                pygame.draw.circle(s, (244, 246, 250), (cx + dx, cy), r)
        pygame.draw.line(s, (180, 210, 230), (0, HORIZON), (W, HORIZON))

    def _shields(self, s, ship, ox, oy):
        hb = render.hull_bounds(ship, ox, oy)
        hb.top -= 10
        hb.height += 10
        for i in range(ship.shield_layers):
            r = hb.inflate(22 + i * 8, 14 + i * 8)
            pygame.draw.ellipse(s, P['lblue'] if i % 2 == 0 else P['teal'], r, 1)
        ml = ship.max_layers()
        if ship.shield_layers < ml and ship.shield_t > 0:
            r = hb.inflate(22, 14)
            pygame.draw.arc(s, P['lblue'], r, 0, math.tau * ship.shield_t / 2.0, 1)

    def _top(self, s):
        pygame.draw.rect(s, P['navy'], (0, 0, W, 22))
        pygame.draw.line(s, P['black'], (0, 22), (W, 22))
        x = draw_resources(s, self.gs, y=7)
        if self.fog:
            gfx.text(s, "FOG: evasion halved", x + 4, 7, P['fog'])

    def _crew_chips(self, s):
        m = pygame.mouse.get_pos()
        for i, c in enumerate(self.gs.crew):
            r = self.crew_list_rect(i)
            sel = c in self.selected
            away = c.ship is self.enemy
            pygame.draw.rect(s, P['dgreen'] if sel else P['navy2'], r)
            pygame.draw.rect(s, P['gold'] if away else (P['green'] if sel else P['black']), r, 1)
            from .. import people
            s.blit(people.sprite(c.cls, c.skin, 'stand', 0, 1), (r.left + 7, r.top + 2))
            gfx.bar(s, r.left + 3, r.bottom - 6, r.width - 6, 3, c.hp / c.max_hp,
                    P['green'] if c.hp > c.max_hp * 0.35 else P['red'])
            if i < 9:
                gfx.text(s, str(i + 1), r.left + 2, r.top + 2, P['lgrey'])
            if r.collidepoint(m):
                pygame.draw.rect(s, P['yellow'], r, 1)

    def _player_status(self, s):
        ship = self.gs.ship
        x, y = 4, 66
        ev = ship.evasion(self.fog)
        parts = [(f"Evasion {ev}%", P['white']), (f"Bulwarks {ship.shield_layers}/{ship.max_layers()}", P['lblue'])]
        if not ship.manned('helm'):
            parts.append(("Nobody at the helm!", P['orange']))
        fires = sum(1 for rm in ship.rooms if rm.fire > 0)
        holes = sum(1 for rm in ship.rooms if rm.breach)
        if fires:
            parts.append((f"{fires} fire{'s' if fires > 1 else ''}", P['orange']))
        if holes:
            parts.append((f"{holes} hole{'s' if holes > 1 else ''} in the hull", P['lblue']))
        for txt, col in parts:
            w = gfx.text(s, txt, x, y, col, shadow=P['black'])
            x += w + 10

    def _banners(self, s):
        y = BANNER_Y
        for txt, col, life in self.banner:
            w = gfx.text_w(txt) + 12
            strip = pygame.Surface((w, 12), pygame.SRCALPHA)
            strip.fill((8, 14, 28, 210))
            s.blit(strip, (4, y - 2))
            gfx.text(s, txt, 10, y, col)
            y += 13

    def _enemy_panel(self, s, see):
        en = self.enemy
        if self.sink:
            return
        hb = render.hull_bounds(en, *self.eorig)
        r = pygame.Rect(max(hb.left, 370), min(hb.bottom + 6, PANEL_Y - 48), 0, 44)
        r.width = W - 4 - r.left
        gfx.panel(s, r, 'dark')
        x = r.left + 5
        gfx.text(s, en.name, x, r.top + 4, P['red'])
        gfx.text(s, data.ENEMIES[self.enemy_key]['name'], r.right - 5, r.top + 4, P['lgrey'], align='right')
        per = 4 if en.hull_max <= 40 else 3
        for i in range(en.hull_max):
            col = P['red'] if i < en.hull else P['dgrey']
            pygame.draw.rect(s, col, (x + i * per, r.top + 15, per - 1, 6))
        info = f"Evasion {en.evasion(self.fog)}%   Bulwarks {en.shield_layers}/{en.max_layers()}"
        if en.fleeing:
            info += "   FLEEING!"
        if self.battle.angry:
            info += "   ENRAGED"
        gfx.text(s, info, x, r.top + 24, P['white'] if not en.fleeing else P['yellow'])
        if not see:
            gfx.text(s, "Can't see inside: Crow's Nest needed", x, r.top + 34, P['lgrey'])
        else:
            nest = self.gs.ship.sys.get('nest')
            if nest and nest.eff() >= 2:
                xx = x
                for w in en.weapons:
                    nm = w.name.split(' ')[0]
                    gfx.text(s, nm, xx, r.top + 34, P['lgrey'])
                    gfx.bar(s, xx + gfx.text_w(nm) + 2, r.top + 36, 22, 3, w.charge, P['red'])
                    xx += gfx.text_w(nm) + 30
            else:
                gfx.text(s, "Crow's Nest Lv2 shows their loading", x, r.top + 34, P['grey'])

    def _bottom(self, s):
        gs, ship = self.gs, self.gs.ship
        pygame.draw.rect(s, P['navy'], (0, PANEL_Y, W, H - PANEL_Y))
        pygame.draw.line(s, P['black'], (0, PANEL_Y), (W, PANEL_Y))
        m = pygame.mouse.get_pos()
        # hands
        free = ship.reactor_free()
        gfx.text(s, "HANDS", HANDS_X + 1, PANEL_Y + 3, P['gold'])
        total = min(ship.gusto, 14)
        for i in range(total):
            col = P['green'] if i < free else P['dgrey']
            pygame.draw.rect(s, col, (HANDS_X + 4, H - 6 - i * 4, 18, 3))
        gfx.text(s, f"{free}/{ship.gusto}", HANDS_X + 26, PANEL_Y + 3, P['white'])
        # stations
        gfx.text(s, "STATIONS", SYS_X0 + 28, PANEL_Y + 3, P['gold'])
        for i, n in enumerate(self.sys_names()):
            r = self.sys_rect(i)
            sysm = ship.sys[n]
            if r.collidepoint(m):
                pygame.draw.rect(s, P['navy2'], r)
            ic = gfx.icon(n, P['red'] if sysm.damage >= sysm.level else None)
            s.blit(ic, (r.centerx - 4, H - 11))
            for j in range(sysm.level):
                rr = pygame.Rect(r.centerx - 7, H - 17 - j * 5, 14, 4)
                if j >= sysm.level - sysm.damage:
                    pygame.draw.rect(s, P['red'], rr)
                elif sysm.sub:
                    pygame.draw.rect(s, P['lgrey'], rr)
                elif j < sysm.power:
                    pygame.draw.rect(s, P['green'], rr)
                else:
                    pygame.draw.rect(s, P['dgrey'], rr, 1)
            if ship.manned(n):
                pygame.draw.rect(s, P['yellow'], (r.right - 4, H - 10, 2, 2))
        # cannons
        gfx.text(s, "CANNONS", WEAP_X0, PANEL_Y + 3, P['gold'])
        gfx.text(s, "1-4: select, then click an enemy room", WEAP_X0 + 44, PANEL_Y + 3, P['grey'])
        from .hangar import draw_tag
        for i, w in enumerate(ship.weapons):
            r = self.weapon_rect(i)
            col = P['dred'] if self.aiming == i else (P['dgrey'] if r.collidepoint(m) else P['navy2'])
            pygame.draw.rect(s, col, r)
            edge = P['yellow'] if self.aiming == i else (P['green'] if w.powered else P['black'])
            pygame.draw.rect(s, edge, r, 1)
            gfx.text(s, f"{i + 1}", r.left + 3, r.top + 3, P['gold'])
            nm = w.name if gfx.text_w(w.name) <= r.width - 14 else w.name.split(' ')[0]
            gfx.text(s, nm, r.left + 10, r.top + 3, P['white'] if w.powered else P['lgrey'])
            ready = w.charge >= 1
            gfx.bar(s, r.left + 3, r.top + 13, r.width - 6, 4, w.charge, P['yellow'] if ready else P['orange'])
            for j in range(w.power):
                pygame.draw.rect(s, P['green'] if w.powered else P['dgrey'], (r.left + 3 + j * 5, r.top + 20, 3, 5))
            tx = r.left + 4 + w.power * 5 + 2
            for tag in data.weapon_tags(w.d)[:1]:
                draw_tag(s, tag, tx, r.top + 19)
            if not w.powered:
                status, scol = "no Hands: click", P['grey']
            elif w.target is None:
                status, scol = ("READY: aim it!" if ready else f"loading {int(w.charge * 100)}%"), P['lgrey']
            else:
                tgt = self.enemy.rooms[w.target]
                status = ("FIRING" if ready else f"loading {int(w.charge * 100)}%")
                scol = P['red']
                gfx.text(s, "at " + render.ROOM_LABEL.get(tgt.sys or tgt.kind, '?'), r.left + 3, r.top + 41, P['red'])
            gfx.text(s, status, r.left + 3, r.top + 30, scol)
        # escape and boarding
        x = RIGHT_X
        e = ship.escape
        gfx.text(s, "CHARTING COURSE", x + 2, PANEL_Y + 3, P['gold'])
        if not ship.can_escape():
            gfx.text(s, "needs someone at the helm", x + 2, PANEL_Y + 13, P['orange'])
        elif e < 1:
            gfx.text(s, f"hoisting sails... {int(e * 100)}%", x + 2, PANEL_Y + 13, P['lgrey'])
        else:
            gfx.text(s, "course set: ready to flee", x + 2, PANEL_Y + 13, P['green'])
        gfx.bar(s, x + 2, PANEL_Y + 23, 160, 3, e, P['teal'])
        fb = self.flee_btn
        fb.enabled = e >= 1.0
        fb.draw(s, m)
        if ship.grapple:
            cd = self.battle.board_cd
            self.board_btn.enabled = cd <= 0
            self.board_btn.label = "Board [B]" if cd <= 0 else f"Board {cd:.0f}s"
            self.board_btn.draw(s, m)
            self.recall_btn.draw(s, m)
        else:
            gfx.text(s, "Boarding needs an Armory", x + 2, 338, P['grey'])
        gfx.text(s, "SPACE pause   R-click: move", x + 2, 351, P['grey'])

    def _tooltips(self, s, m):
        ship = self.gs.ship
        for i, n in enumerate(self.sys_names()):
            if self.sys_rect(i).collidepoint(m):
                d = data.SYSTEMS[n]
                sysm = ship.sys[n]
                extra = " (needs no Hands)" if sysm.sub else " L-click: +1 Hand, R-click: -1 Hand."
                if n == 'guns':
                    extra = " Click a cannon card to give it Hands."
                tooltip(s, f"{d['title']} Lv{sysm.level}: {d['desc']}{extra}", m, 230)
                return
        for i, w in enumerate(ship.weapons):
            if self.weapon_rect(i).collidepoint(m):
                d = w.d
                stats = (f"{d['shots']} shot(s), {d['dmg'] + d.get('hull', 0)} hull damage, loads in "
                         f"{d['charge']:.1f}s, needs {d['power']} Hands. [{' '.join(data.weapon_tags(d))}] "
                         f"Right-click to take its Hands away.")
                tooltip(s, f"{d['name']}: {d['desc']} {stats}", m, 230)
                return
        for i, c in enumerate(self.gs.crew):
            if self.crew_list_rect(i).collidepoint(m):
                where = "aboard the ENEMY" if c.ship is self.enemy else c.ship.rooms[c.room].title
                tooltip(s, f"{c.name} the {c.title} ({int(c.hp)}/{c.max_hp} HP), {data.HANDS.get(c.cls, 3)} Hands. "
                           f"{TASK_LABEL.get(c.task, c.task)} in {where}. {c.d['desc']}", m, 230)
                return
        if self.board_btn.rect.collidepoint(m) and ship.grapple:
            tooltip(s, "Boarding: select crew standing on your top deck (HELM or SAILS), then press Board. "
                       "They swing onto the enemy's top deck and must fight their way down. Recall brings home "
                       "crew standing on the enemy's top deck.", m, 230)
            return
        if self.hover_crew is not None:
            c = self.hover_crew
            tooltip(s, f"{c.name} the {c.title}: {TASK_LABEL.get(c.task, c.task)}. {int(c.hp)}/{c.max_hp} HP",
                    m, 200)
            return
        if m[1] < PANEL_Y:
            for sh in (ship, self.enemy):
                ri = render.room_at(sh, *self.origin_of(sh), m)
                if ri is not None and not (self.sink and sh is self.enemy):
                    r = sh.rooms[ri]
                    if sh is self.enemy and not self.can_see() and not r.sys:
                        return
                    desc = data.SYSTEMS[r.sys]['desc'] if r.sys else data.MODULES.get(r.kind, {}).get('desc', '')
                    extra = []
                    if r.fire > 0:
                        extra.append("ON FIRE.")
                    if r.breach:
                        extra.append("HOLE IN THE HULL: costs 1 hull every 12s until patched.")
                    tooltip(s, f"{r.title}. {desc} {' '.join(extra)}", (m[0], m[1] + 10), 220)
                    return
