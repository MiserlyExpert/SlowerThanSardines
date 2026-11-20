"""Real-time-with-pause naval combat."""
import math
import random

import pygame

from .. import audio, data, gfx, render
from ..app import Scene
from ..battle import Battle
from ..config import H, T, W
from ..gfx import P
from .hud import draw_resources, tooltip

TASK_LABEL = dict(man='Manning', repair='Repairing', patch='Patching', fire='Firefighting',
                  fight='Brawling!', walk='Walking', idle='Idle', sabotage='Sabotage')

SYS_X0 = 36
SYS_W = 30
WEAP_X0 = 228
WEAP_W = 74
PANEL_Y = 252


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
        self.player_base = (138, 104)
        e = enemy
        self.enemy_base = (496 - e.gw * T // 2, 146 - e.gh * T // 2)
        msg = f"{enemy.name} ({data.ENEMIES[enemy_key]['name']}) attacks!"
        self.say_banner(msg, P['white'])
        if fog:
            self.say_banner("Fog! Everyone's evasion is halved. Escape is slow.", P['fog'])
        self.flee_btn = gfx.Button((534, 296, 100, 22), "Make Sail!", self.flee)
        audio.play('bell')

    # ------------------------------------------------------------------
    @property
    def porig(self):
        bx, by = self.player_base
        return bx, by + int(math.sin(self.t * 1.3) * 1.5)

    @property
    def eorig(self):
        bx, by = self.enemy_base
        sink = 0
        if self.battle.over in ('win',):
            sink = int(self.end_t * 25)
        return bx, by + int(math.sin(self.t * 1.3 + 1) * 1.5) + sink

    def room_screen(self, ship, idx):
        ox, oy = self.porig if ship is self.gs.ship else self.eorig
        cx, cy = ship.rooms[idx].center()
        return ox + cx, oy + cy

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
        return pygame.Rect(WEAP_X0 + i * WEAP_W, 292, WEAP_W - 4, 58)

    def sys_rect(self, i):
        return pygame.Rect(SYS_X0 + i * SYS_W, PANEL_Y + 4, SYS_W - 2, 100)

    def sys_names(self):
        return [n for n in data.SYS_ORDER if n in self.gs.ship.sys]

    def crew_list_rect(self, i):
        return pygame.Rect(4, 30 + i * 21, 110, 20)

    def handle(self, e):
        gs, ship, b = self.gs, self.gs.ship, self.battle
        if b.over:
            return
        if self.flee_btn.handle(e):
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
                c = render.crew_at(ship, *self.porig, pos)
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
                ri = render.room_at(ship, *self.porig, pos)
                if ri is not None and self.selected:
                    moved = False
                    for c in self.selected:
                        if c.alive and c.order_move(ri):
                            moved = True
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
            self.end_t += dt
            if self.end_t > 1.6:
                self.finish()
                return
        self.selected = [c for c in self.selected if c.alive]
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
                audio.play('cannon')
                gr = ship.sys_room.get('guns')
                if gr is not None:
                    gx, gy = self.room_screen(ship, gr)
                    self.burst(gx + (30 if mine else -30), gy, [P['yellow'], P['orange'], P['white']], 8, 30)
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
            elif k == 'breach':
                self.floater("LEAK!", x, y - 22, P['lblue'])
            elif k == 'board':
                audio.play('board')
                self.say_banner(f"BOARDERS! {ev['n']} pirates swing aboard on ropes!", P['red'])
                self.burst(x, y, [P['white'], P['lgrey']], 14, 40)
            elif k == 'death':
                audio.play('death')
                c = ev['crew']
                col = P['red'] if c.side == 'player' else P['green']
                self.say_banner(f"{c.name} the {c.title} has perished.", col)
                if c.side == 'player' and gs.crew and random.random() < 0.6:
                    random.choice(gs.crew).say(random.choice(
                        ["Nooo! They owed me money!", "Rest easy, shipmate.", "I'll drink their share. For honour."]))
            elif k == 'enemy_flee':
                self.say_banner(f"{self.enemy.name} is trying to escape!", P['yellow'])
            elif k == 'angry':
                self.say_banner("Barnacle Vane is FURIOUS! His guns reload faster!", P['red'])
                dread = [c for c in self.enemy.crew if c.cls == 'dread']
                if dread:
                    dread[0].say("NOW I'M ANGRY!", 3)
        b.events.clear()

    def finish(self):
        from .endings import GameOverScene, VictoryScene
        from .event import EventScene
        b, gs = self.battle, self.gs
        over = b.over
        if over == 'lose':
            audio.play('lose')
            self.app.replace(GameOverScene(self.app))
            return
        b.cleanup()
        gs.sector.node.cleared = True
        if over in ('win', 'win_crew'):
            gs.stats['wins'] += 1
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
        gfx.draw_sea(s, t, 0)
        if self.fog:
            gfx.draw_fog(s, t)
        sx = int(random.uniform(-2, 2) * self.shake) if self.shake else 0
        sy = int(random.uniform(-2, 2) * self.shake) if self.shake else 0
        # enemy panel frame
        epan = pygame.Rect(350, 28, 286, 220)
        pygame.draw.rect(s, P['navy2'], epan, 1)
        # ships
        px, py = self.porig
        px += sx
        py += sy
        ex, ey = self.eorig
        targets = [w.target for w in ship.weapons if w.target is not None]
        self._shields(s, ship, px, py)
        render.draw_hull(s, ship, px, py, t)
        render.draw_rooms(s, ship, px, py, t, hover=self.hover_room if self.selected else None)
        render.draw_crew(s, ship, px, py, t, selected=self.selected)
        see = ship.sys.get('nest') and ship.sys['nest'].eff() >= 1
        self._shields(s, en, ex, ey)
        render.draw_hull(s, en, ex, ey, t)
        render.draw_rooms(s, en, ex, ey, t, hover=self.hover_eroom if self.aiming is not None else None,
                          targets=targets)
        render.draw_crew(s, en, ex, ey, t, visible_sides=('player', 'enemy') if see else ('player',))
        if b.over == 'win':
            for i in range(6):
                bx = ex + (i * 37 + int(t * 50)) % (en.gw * T)
                pygame.draw.circle(s, P['foam'], (bx, ey + en.gh * T - int((t * 40 + i * 13) % 50)), 2, 1)
        # projectiles
        for p in b.projectiles:
            if p['t'] < 0:
                continue
            k = min(1.0, p['t'] / p['dur'])
            src, dst = p['src'], p['dst']
            gr = src.sys_room.get('guns', 0)
            x0, y0 = self.room_screen(src, gr)
            x1, y1 = self.room_screen(dst, p['room'])
            x = x0 + (x1 - x0) * k
            y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * (60 if p['w'].get('pierce') else 25)
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
        for x, y, r, life in self.flashes:
            pygame.draw.circle(s, P['gold'], (int(x), int(y)), int(r), 1)
        for p in self.particles:
            s.set_at((int(p[0]), int(p[1])), p[5])
            s.set_at((int(p[0]) + 1, int(p[1])), p[5])
        render.draw_barks(s, ship, px, py)
        render.draw_barks(s, en, ex, ey, ('player', 'enemy') if see else ('player',))
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
        y = 70 if not self.paused else 90
        for txt, col, life in self.banner:
            gfx.text(s, txt, W // 2 - 70, y, col, 16, shadow=P['black'], align='center')
            y += 13
        if self.paused and not b.over:
            gfx.text(s, "PAUSED  (space to resume)", W // 2 - 70, 34, P['yellow'], 24, shadow=P['black'],
                     align='center')
        self._tooltips(s, m)

    def _shields(self, s, ship, ox, oy):
        SW, SH = ship.gw * T, ship.gh * T
        for i in range(ship.shield_layers):
            r = pygame.Rect(ox - 26 - i * 4, oy - 26 - i * 4, SW + 52 + i * 8, SH + 52 + i * 8)
            if ship.facing > 0:
                r.width += 18
            else:
                r.x -= 18
                r.width += 18
            pygame.draw.ellipse(s, P['lblue'] if i % 2 == 0 else P['teal'], r, 1)
        ml = ship.max_layers()
        if ship.shield_layers < ml and ship.shield_t > 0:
            r = pygame.Rect(ox - 26, oy - 26, SW + 70, SH + 52)
            if ship.facing < 0:
                r.x -= 18
            start = 0
            pygame.draw.arc(s, P['lblue'], r, start, start + math.tau * ship.shield_t / 2.0, 1)

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
            gfx.text(s, c.name[:18], r.left + 15, r.top + 2, P['white'], 14)
            gfx.text(s, TASK_LABEL.get(c.task, c.task), r.left + 15, r.top + 10, P['lgrey'], 14)
            gfx.bar(s, r.right - 30, r.top + 13, 26, 3, c.hp / c.max_hp,
                    P['green'] if c.hp > c.max_hp * 0.35 else P['red'])

    def _player_stats(self, s, px, py):
        ship = self.gs.ship
        y = 214
        ev = ship.evasion(self.fog)
        gfx.text(s, f"Evasion {ev}%", 132, y, P['white'], 16, shadow=P['black'])
        if not ship.manned('helm'):
            gfx.text(s, "Helm unmanned!", 220, y, P['orange'], 16, shadow=P['black'])
        flood = ship.flood_frac()
        if flood > 0.05:
            gfx.text(s, f"Flooding {int(flood * 100)}%", 132, y + 12, P['lblue'], 16, shadow=P['black'])

    def _enemy_panel(self, s, r, see):
        en, b = self.enemy, self.battle
        gfx.text(s, en.name, r.left + 6, r.top + 4, P['white'], 16, shadow=P['black'])
        gfx.text(s, data.ENEMIES[self.enemy_key]['name'], r.left + 6, r.top + 15, P['lgrey'], 14)
        x = r.left + 6
        y = r.top + 27
        for i in range(en.hull_max):
            col = P['red'] if i < en.hull else P['dgrey']
            pygame.draw.rect(s, col, (x + i * 4, y, 3, 6))
        y += 10
        ev = en.evasion(self.fog)
        gfx.text(s, f"Evasion {ev}%   Bulwarks {en.shield_layers}/{en.max_layers()}", x, y, P['white'], 14)
        if en.fleeing:
            gfx.text(s, "FLEEING", r.right - 6, r.top + 4, P['yellow'], 16, align='right')
            gfx.bar(s, r.right - 60, r.top + 16, 54, 4, en.escape, P['yellow'])
        if self.battle.angry:
            gfx.text(s, "ENRAGED", r.right - 6, r.top + 26, P['red'], 16, align='right')
        if not see:
            gfx.text(s, "Crow's Nest down: crew hidden", r.centerx, r.bottom - 12, P['lgrey'], 14, align='center')
        nest = self.gs.ship.sys.get('nest')
        if nest and nest.eff() >= 2:
            yy = r.bottom - 26
            for i, w in enumerate(en.weapons):
                gfx.text(s, w.name[:12], r.left + 6 + i * 70, yy, P['lgrey'], 14)
                gfx.bar(s, r.left + 6 + i * 70, yy + 10, 60, 3, w.charge, P['red'])

    def _bottom(self, s):
        gs, ship = self.gs, self.gs.ship
        pygame.draw.rect(s, P['navy'], (0, PANEL_Y, W, H - PANEL_Y))
        pygame.draw.line(s, P['black'], (0, PANEL_Y), (W, PANEL_Y))
        m = pygame.mouse.get_pos()
        # gusto
        free = ship.reactor_free()
        gfx.text(s, "GUSTO", 4, PANEL_Y + 3, P['gold'], 14)
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
        gfx.text(s, "CANNONS  (1-4 select, click enemy room to aim)", WEAP_X0, PANEL_Y + 4, P['gold'], 14)
        for i, w in enumerate(ship.weapons):
            r = self.weapon_rect(i)
            col = P['navy2']
            if self.aiming == i:
                col = P['dred']
            elif r.collidepoint(m):
                col = P['dgrey']
            pygame.draw.rect(s, col, r)
            pygame.draw.rect(s, P['yellow'] if self.aiming == i else (P['green'] if w.powered else P['black']), r, 1)
            gfx.text(s, f"{i + 1}", r.left + 3, r.top + 2, P['gold'], 14)
            gfx.text(s, w.name[:13], r.left + 11, r.top + 2, P['white'] if w.powered else P['lgrey'], 14)
            gfx.bar(s, r.left + 4, r.top + 14, r.width - 8, 5, w.charge,
                    P['yellow'] if w.charge >= 1 else P['orange'])
            for j in range(w.power):
                pygame.draw.rect(s, P['green'] if w.powered else P['dgrey'], (r.left + 4 + j * 7, r.top + 23, 5, 5))
            if w.d.get('ammo'):
                s.blit(gfx.icon('ball'), (r.right - 10, r.top + 22))
            if w.target is not None:
                gfx.text(s, "TARGET SET", r.left + 4, r.top + 31, P['red'], 14)
            elif w.powered:
                gfx.text(s, "no target", r.left + 4, r.top + 31, P['lgrey'], 14)
            else:
                gfx.text(s, "click: power", r.left + 4, r.top + 31, P['grey'], 14)
        # escape
        e = ship.escape
        fb = self.flee_btn
        fb.enabled = e >= 1.0
        gfx.text(s, "ESCAPE", 534, PANEL_Y + 4, P['gold'], 14)
        gfx.bar(s, 534, 284, 100, 6, e, P['teal'])
        if not ship.can_escape():
            gfx.text(s, "needs manned helm", 534, 270, P['orange'], 14)
        else:
            gfx.text(s, "charging..." if e < 1 else "ready!", 534, 270, P['lgrey'], 14)
        fb.draw(s, m)
        gfx.text(s, "SPACE: pause", 534, 324, P['grey'], 14)
        gfx.text(s, "A: select all crew", 534, 334, P['grey'], 14)
        gfx.text(s, "R-click room: move", 534, 344, P['grey'], 14)

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
                stats = (f"{d['shots']} shot(s), {d['dmg']} dmg, {d['charge']:.0f}s reload, {d['power']} power. "
                         "Right-click to unpower.")
                tooltip(s, f"{d['name']}: {d['desc']} {stats}", m, 220)
                return
        for i, c in enumerate(self.gs.crew):
            if self.crew_list_rect(i).collidepoint(m):
                tooltip(s, f"{c.name} the {c.title} ({int(c.hp)}/{c.max_hp}). {c.d['desc']}", m, 220)
                return
