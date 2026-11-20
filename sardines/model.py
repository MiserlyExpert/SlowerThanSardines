"""Core ship model: rooms, systems, weapons, crew, ships."""
import math
import random
from collections import deque

from . import data
from .config import RH, TOP_ROW, TW


class Room:
    """One room on one deck. Crew stand on its floor, one per tile."""

    def __init__(self, idx, kind, gx, gy, w, sys=None):
        self.idx, self.kind, self.sys = idx, kind, sys
        self.gx, self.gy, self.w, self.h = gx, gy, w, 1
        self.fire = 0.0      # 0..100
        self.water = 0.0     # 0..100 (percentage of the room's height)
        self.breach = False
        self.breach_prog = 0.0
        self.exploded = False

    @property
    def open_air(self):
        return self.gy <= TOP_ROW

    @property
    def title(self):
        if self.sys:
            return data.SYSTEMS[self.sys]['title']
        return data.FLAVOR.get(self.kind, self.kind.title())

    def tiles(self):
        return [(self.gx + i, self.gy) for i in range(self.w)]

    @property
    def n_tiles(self):
        return self.w

    @property
    def floor_y(self):
        return (self.gy + 1) * RH - 2

    def tile_center(self, k):
        return ((self.gx + k + 0.5) * TW, self.floor_y)

    def center(self):
        return ((self.gx + self.w / 2) * TW, (self.gy + 0.5) * RH)

    @property
    def rect(self):
        return (self.gx * TW, self.gy * RH, self.w * TW, RH)

    def contains(self, x, y):
        return self.gx * TW <= x < (self.gx + self.w) * TW and self.gy * RH <= y < (self.gy + 1) * RH

    def has_col(self, c):
        return self.gx <= c < self.gx + self.w


class System:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.power = 0
        self.want = 0
        self.damage = 0
        self.repair_prog = 0.0
        self.harm_prog = 0.0
        self.sub = data.SYSTEMS[name].get('sub', False)
        self.flooded = False

    @property
    def intact(self):
        return max(0, self.level - self.damage)

    def eff(self):
        e = self.intact if self.sub else min(self.power, self.intact)
        if self.flooded and e > 0:
            e -= 1
        return e


class Weapon:
    def __init__(self, key):
        self.key = key
        self.d = data.WEAPONS[key]
        self.charge = 0.0
        self.powered = False
        self.want = False
        self.target = None  # room index on the enemy ship

    @property
    def name(self):
        return self.d['name']

    @property
    def power(self):
        return self.d['power']


class Crew:
    _uid = 0

    def __init__(self, cls, name=None, side='player', rng=random):
        d = data.CREW[cls]
        self.cls = cls
        if name is None:
            pool = data.NAMES.get(cls) or data.NAMES['generic']
            if cls in ('brute',):
                pool = data.NAMES['pirate']
            name = rng.choice(pool)
        self.name = name
        self.hp = self.max_hp = d['hp']
        self.side = side
        self.skin = rng.randrange(4)
        self.ship = None
        self.room = 0
        self.tile = 0
        self.x = self.y = 0.0
        self.path = []
        self.task = 'idle'
        self.foe = None
        self.bark = None
        self.bark_t = 0.0
        self.anim = rng.random() * 10
        self.walk_t = 0.0
        self.mode = 'stand'
        self.facing = 1 if side == 'player' else -1
        self.station = None
        Crew._uid += 1
        self.uid = Crew._uid

    # -- stats --
    @property
    def d(self):
        return data.CREW[self.cls]

    @property
    def title(self):
        return self.d['title']

    def skill(self, key):
        return self.d.get(key, 0)

    @property
    def alive(self):
        return self.hp > 0

    @property
    def moving(self):
        return bool(self.path)

    def cur_room(self):
        if not self.path or self.ship is None:
            return self.room
        for r in self.ship.rooms:
            if r.contains(self.x, self.y - 3):
                return r.idx
        return self.room

    def say(self, text, dur=3.0):
        self.bark, self.bark_t = text, dur

    # -- movement --
    def order_move(self, room_idx):
        ship = self.ship
        if room_idx == self.room and not self.path:
            return True
        k = ship.free_tile(room_idx, self.side, exclude=self)
        if k is None:
            return False
        pts = ship.path_points(self.cur_room(), room_idx, (self.x, self.y))
        if pts is None:
            return False
        pts.append((*ship.rooms[room_idx].tile_center(k), 'walk'))
        self.path = pts
        self.room, self.tile = room_idx, k
        return True

    def update_move(self, dt):
        if not self.path:
            self.mode = 'stand'
            return
        tx, ty, mode = self.path[0]
        spd = self.skill('speed') * TW * 1.5
        if mode == 'climb':
            spd *= 0.55
        elif mode == 'stairs':
            spd *= 0.8
        if self.cls == 'drunk' and mode == 'walk':
            spd *= 0.55 + 0.9 * abs(math.sin(self.anim * 1.7))
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = spd * dt
        self.walk_t += dt
        self.mode = mode
        if abs(dx) > 0.3 and mode != 'climb':
            self.facing = 1 if dx > 0 else -1
        if dist <= step:
            self.x, self.y = tx, ty
            self.path.pop(0)
        else:
            self.x += dx / dist * step
            self.y += dy / dist * step


class Ship:
    def __init__(self, name, layout, hull, levels, gusto, weapons, side, mirror=False, kind=None):
        self.name = name
        self.side = side
        self.kind = kind
        lay = data.LAYOUTS[layout]
        self.layout_key = layout
        self.gw = max(r[1] + r[3] for r in lay['rooms'])
        self.gh = max(r[2] for r in lay['rooms']) + 1
        self.rooms = []
        for kind_, gx, gy, w in lay['rooms']:
            sysn = None
            if kind_ in data.SYSTEMS:
                if levels.get(kind_, 0) > 0:
                    sysn = kind_
                else:
                    kind_ = data.SYS_FALLBACK.get(kind_, 'hold')
            self.rooms.append(Room(len(self.rooms), kind_, gx, gy, w, sysn))
        self.masts = list(lay.get('masts', []))
        self.sys = {r.sys: System(r.sys, levels[r.sys]) for r in self.rooms if r.sys}
        self.sys_room = {r.sys: r.idx for r in self.rooms if r.sys}
        self.hull = self.hull_max = hull
        self.gusto = gusto
        self.weapons = [Weapon(k) for k in weapons]
        self.crew = []
        self.facing = 1
        self.shield_layers = 0
        self.shield_t = 0.0
        self.escape = 0.0
        self.fleeing = False
        self.manning = {}
        self.ammo = 8   # enemies only
        self.recoil = {}
        self.grapple = False
        self.faction = data.ENEMIES[kind].get('faction', 'pirate') if kind in data.ENEMIES else 'rebel'
        self._build_graph(lay.get('links', []))

    # -- geometry --
    def _build_graph(self, links):
        """Rooms joined by doors (same deck, side by side) and by ladders, stairs and rigging (vertical)."""
        self.adj = {r.idx: [] for r in self.rooms}
        self.edges = {}
        self.links = []
        for a in self.rooms:
            for b in self.rooms:
                if a.idx != b.idx and a.gy == b.gy and a.gx + a.w == b.gx:
                    self._join(a.idx, b.idx, ('door', b.gx * TW))
        for kind, col, row in links:
            up = next((r for r in self.rooms if r.gy == row and r.has_col(col)), None)
            low_col = col + 1 if kind == 'stairs' else col
            lo = next((r for r in self.rooms if r.gy == row + 1 and r.has_col(low_col)), None)
            if up and lo:
                self._join(up.idx, lo.idx, (kind, col, up.idx, lo.idx))
                self.links.append((kind, col, up.idx, lo.idx))

    def _join(self, a, b, info):
        self.adj[a].append(b)
        self.adj[b].append(a)
        self.edges[(a, b)] = self.edges[(b, a)] = info

    def route(self, a, b):
        if a == b:
            return [a]
        prev = {a: None}
        q = deque([a])
        while q:
            n = q.popleft()
            for m in self.adj[n]:
                if m not in prev:
                    prev[m] = n
                    if m == b:
                        path = [b]
                        while prev[path[-1]] is not None:
                            path.append(prev[path[-1]])
                        return path[::-1]
                    q.append(m)
        return None

    def path_points(self, a, b, start):
        """Waypoints (x, y, mode) to walk from room a to room b. Modes: walk, climb, stairs."""
        route = self.route(a, b)
        if route is None:
            return None
        pts = []
        cur_y = self.rooms[a].floor_y
        if abs(start[1] - cur_y) > 1:            # mid-ladder: finish getting onto this floor
            pts.append((start[0], cur_y, 'climb'))
        for r1, r2 in zip(route, route[1:]):
            info = self.edges[(r1, r2)]
            R1, R2 = self.rooms[r1], self.rooms[r2]
            if info[0] == 'door':
                pts.append((info[1], R1.floor_y, 'walk'))
            elif info[0] in ('ladder', 'rigging'):
                cx = (info[1] + 0.5) * TW
                pts.append((cx, R1.floor_y, 'walk'))
                pts.append((cx, R2.floor_y, 'climb'))
            else:  # stairs: top at column c (upper room), bottom at column c+1 (lower room)
                col = info[1]
                top = (col * TW + 3, self.rooms[info[2]].floor_y)
                bot = ((col + 2) * TW - 3, self.rooms[info[3]].floor_y)
                if r1 == info[2]:
                    pts.append((*top, 'walk'))
                    pts.append((*bot, 'stairs'))
                else:
                    pts.append((*bot, 'walk'))
                    pts.append((*top, 'stairs'))
        return pts

    def top_rooms(self):
        return [r.idx for r in self.rooms if r.gy == TOP_ROW]

    def free_tile(self, room_idx, side, exclude=None):
        taken = {c.tile for c in self.crew if c is not exclude and c.room == room_idx
                 and c.side == side and c.alive}
        room = self.rooms[room_idx]
        for k in range(room.n_tiles):
            if k not in taken:
                return k
        return None

    def place(self, crew, room_idx=None, rng=random):
        crew.ship = self
        order = [room_idx] if room_idx is not None else []
        rest = [r.idx for r in self.rooms if r.idx != room_idx]
        rng.shuffle(rest)
        for ri in order + rest:
            k = self.free_tile(ri, crew.side, exclude=crew)
            if k is not None:
                crew.room, crew.tile = ri, k
                crew.x, crew.y = self.rooms[ri].tile_center(k)
                crew.path = []
                if crew not in self.crew:
                    self.crew.append(crew)
                return True
        return False

    def crew_in(self, room_idx, side=None):
        return [c for c in self.crew if c.alive and c.cur_room() == room_idx and (side is None or c.side == side)]

    # -- power --
    def reactor_used(self):
        return sum(s.power for s in self.sys.values() if not s.sub)

    def reactor_free(self):
        return self.gusto - self.reactor_used()

    def add_power(self, name):
        s = self.sys.get(name)
        if not s or s.sub or name == 'guns':
            return False
        if s.power < s.intact and self.reactor_free() > 0:
            s.power += 1
            s.want = s.power
            return True
        return False

    def remove_power(self, name):
        s = self.sys.get(name)
        if not s or s.sub or name == 'guns' or s.power <= 0:
            return False
        s.power -= 1
        s.want = s.power
        return True

    def power_weapon(self, w, auto=False):
        g = self.sys.get('guns')
        if not g or w.powered:
            return w.powered
        if g.power + w.power <= g.intact and self.reactor_free() >= w.power:
            w.powered = True
            g.power += w.power
            if not auto:
                w.want = True
            return True
        return False

    def unpower_weapon(self, w, auto=False):
        if w.powered:
            w.powered = False
            self.sys['guns'].power -= w.power
        if not auto:
            w.want = False

    def clamp_power(self, s):
        if s.name == 'guns':
            for w in reversed(self.weapons):
                if s.power <= s.intact:
                    break
                if w.powered:
                    self.unpower_weapon(w, auto=True)
        elif not s.sub:
            s.power = min(s.power, s.intact)

    def restore_power(self, s):
        if s.name == 'guns':
            for w in self.weapons:
                if w.want and not w.powered:
                    self.power_weapon(w, auto=True)
        elif not s.sub:
            while s.power < min(s.want, s.intact) and self.reactor_free() > 0:
                s.power += 1

    def damage_system(self, name, n):
        s = self.sys.get(name)
        if not s or n <= 0:
            return
        s.damage = min(s.level, s.damage + n)
        s.repair_prog = 0.0
        self.clamp_power(s)

    def repair_bar(self, s):
        s.damage = max(0, s.damage - 1)
        s.repair_prog = 0.0
        self.restore_power(s)

    def autopower(self):
        """Enemy ships: power everything that is intact."""
        for s in self.sys.values():
            if not s.sub and s.name != 'guns':
                s.power = s.want = s.intact
        g = self.sys.get('guns')
        if g:
            used = sum(w.power for w in self.weapons if w.powered)
            for w in self.weapons:
                if w.powered and used > g.intact:
                    w.powered = False
                    used -= w.power
            for w in self.weapons:
                if not w.powered and used + w.power <= g.intact:
                    w.powered = True
                    used += w.power
            g.power = used

    # -- derived stats --
    def manned(self, name):
        return self.manning.get(name)

    def flood_frac(self):
        below = [r for r in self.rooms if not r.open_air]
        return sum(r.water * r.w for r in below) / (100.0 * max(1, sum(r.w for r in below)))

    def evasion(self, fog=False):
        helm, sails = self.sys.get('helm'), self.sys.get('sails')
        if not helm or not sails or helm.eff() <= 0 or sails.eff() <= 0:
            return 0
        pilot = self.manned('helm')
        if not pilot:
            return 0
        ev = sails.eff() * 5 + pilot.skill('helm') + (helm.eff() - 1) * 3
        sailor = self.manned('sails')
        if sailor:
            ev += sailor.skill('sails')
        ev -= 20 * self.flood_frac()
        if fog:
            ev *= 0.5
        return int(max(0, min(60, ev)))

    def max_layers(self):
        b = self.sys.get('bulwark')
        return b.eff() // 2 if b else 0

    def can_escape(self):
        helm, sails = self.sys.get('helm'), self.sys.get('sails')
        return bool(helm and sails and helm.eff() > 0 and sails.eff() > 0 and self.manned('helm'))

    def alive_crew(self, side=None):
        side = side or self.side
        return [c for c in self.crew if c.alive and c.side == side]

    # -- simulation --
    def update(self, dt, battle):
        self._update_hazards(dt, battle)
        for r in self.rooms:
            if r.sys:
                self.sys[r.sys].flooded = r.water > 55
        self._update_crew(dt, battle)
        # bulwarks regrow
        ml = self.max_layers()
        if self.shield_layers > ml:
            self.shield_layers = ml
        if self.shield_layers < ml:
            mult = 1.0
            m = self.manned('bulwark')
            if m:
                mult = m.skill('shields')
            self.shield_t += dt * mult
            if self.shield_t >= 2.0:
                self.shield_t = 0
                self.shield_layers += 1
        else:
            self.shield_t = 0
        # sick bay
        sb = self.sys.get('sickbay')
        if sb and sb.eff() > 0:
            for c in self.crew_in(self.sys_room['sickbay'], self.side):
                if not c.moving:
                    c.hp = min(c.max_hp, c.hp + 6 * sb.eff() * dt)
        # surgeons
        for c in self.crew:
            if c.alive and c.cls == 'surgeon' and not c.moving:
                for o in self.crew_in(c.room, c.side):
                    o.hp = min(o.max_hp, o.hp + c.skill('heal') * dt)
        # bark timers / deaths
        for c in self.crew:
            if c.bark_t > 0:
                c.bark_t -= dt
            c.anim += dt
            c.act_t = getattr(c, 'act_t', 0.0) + dt
        dead = [c for c in self.crew if not c.alive]
        for c in dead:
            self.crew.remove(c)
            if battle:
                battle.emit('death', ship=self, crew=c)

    def waterline_row(self):
        """Rows at or below this index are under the sea's surface."""
        return TOP_ROW + 2

    def _update_hazards(self, dt, battle):
        rooms = self.rooms
        delta = [0.0] * len(rooms)
        wl = self.waterline_row()
        for r in rooms:
            if r.breach and not r.open_air:
                rate = 11 if r.gy >= wl else 4      # below the waterline the sea pours in
                delta[r.idx] += rate * dt
            elif r.water > 0 and r.gy < wl and not any(rooms[n].gy > r.gy for n in self.adj[r.idx]):
                delta[r.idx] -= 3 * dt                # scuppers
            elif r.water > 0:
                delta[r.idx] -= 1.2 * dt              # pumps, slowly
            if r.open_air and r.water > 0:
                delta[r.idx] -= 40 * dt               # top deck: it just runs overboard
        for (a_, b_), info in self.edges.items():
            if a_ > b_:
                continue
            A, B = rooms[a_], rooms[b_]
            if info[0] == 'door':
                diff = A.water - B.water
                if abs(diff) > 4:
                    f = diff * 0.25 * dt
                    delta[a_] -= f
                    delta[b_] += f
            else:
                up, lo = (A, B) if A.gy < B.gy else (B, A)
                if up.water > 0 and lo.water < 100:   # water pours down hatches
                    f = min(up.water, 30 * dt)
                    delta[up.idx] -= f
                    delta[lo.idx] += f * 0.8
        for r in rooms:
            r.water = max(0.0, min(100.0, r.water + delta[r.idx]))
            if r.fire > 0:
                if r.water > 35:
                    r.fire = max(0.0, r.fire - 45 * dt)
                else:
                    r.fire = min(100.0, r.fire + 7 * dt)
                if r.sys:
                    s = self.sys[r.sys]
                    if s.intact > 0:
                        s.harm_prog += dt * (r.fire / 100) / 8
                        if s.harm_prog >= 1:
                            s.harm_prog = 0
                            self.damage_system(r.sys, 1)
                if r.kind == 'magazine' and r.fire > 70 and not r.exploded:
                    r.exploded = True
                    self.hull = max(0, self.hull - 4)
                    for c in self.crew_in(r.idx):
                        c.hp -= 60
                    for n in self.adj[r.idx]:
                        rooms[n].fire = max(rooms[n].fire, 40)
                    r.breach = True
                    if battle:
                        battle.emit('explode', ship=self, room=r.idx)
                for c in self.crew_in(r.idx):
                    c.hp -= 4 * dt * (0.4 + r.fire / 160)
                for n in self.adj[r.idx]:
                    nb = rooms[n]
                    if nb.fire <= 0 and nb.water < 35 and random.random() < dt * 0.035 * (r.fire / 100):
                        nb.fire = 10.0
                        if battle:
                            battle.emit('fire', ship=self, room=nb.idx)
            if r.water > 65:
                for c in self.crew_in(r.idx):
                    c.hp -= 2.5 * dt

    def _update_crew(self, dt, battle):
        self.manning = {}
        best = {}
        for c in list(self.crew):
            if not c.alive:
                continue
            c.update_move(dt)
            if c.moving:
                c.task = 'walk'
                continue
            room = self.rooms[c.room]
            foes = [o for o in self.crew if o.alive and o.side != c.side and o.cur_room() == c.room]
            if foes:
                if c.foe not in foes:
                    c.foe = random.choice(foes)
                c.task = 'fight'
                c.foe.hp -= c.skill('fight') * dt * (1.5 if getattr(c, 'axes', False) else 1.0)
                continue
            c.foe = None
            rep = c.skill('repair')
            if c.side == self.side:
                s = self.sys.get(room.sys) if room.sys else None
                if room.fire > 0:
                    room.fire = max(0.0, room.fire - 22 * dt * rep)
                    c.task = 'fire'
                elif room.breach:
                    room.breach_prog += dt * rep / 6
                    c.task = 'patch'
                    if room.breach_prog >= 1:
                        room.breach, room.breach_prog = False, 0.0
                elif s and s.damage > 0:
                    s.repair_prog += dt * rep / 5
                    c.task = 'repair'
                    if s.repair_prog >= 1:
                        self.repair_bar(s)
                elif room.sys in data.MANNABLE:
                    c.task = 'man'
                    score = c.skill('helm') if room.sys == 'helm' else (
                        c.skill('sails') if room.sys == 'sails' else c.skill(
                            'guns' if room.sys == 'guns' else 'shields'))
                    if room.sys not in best or score > best[room.sys][0]:
                        best[room.sys] = (score, c)
                else:
                    c.task = 'idle'
            else:
                # boarder on a hostile ship: sabotage whatever is here
                s = self.sys.get(room.sys) if room.sys else None
                if s and s.intact > 0:
                    c.task = 'sabotage'
                    s.harm_prog += dt / 6
                    if s.harm_prog >= 1:
                        s.harm_prog = 0
                        self.damage_system(room.sys, 1)
                else:
                    c.task = 'idle'
        self.manning = {k: v[1] for k, v in best.items()}


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def make_player_ship(rng=random, key='sardine', crew=None):
    d = data.SHIPS[key]
    ship = Ship(d['name'], d['layout'], d['hull'], dict(d['sys']), gusto=d['gusto'],
                weapons=list(d['weapons']), side='player', kind=None)
    ship.faction = d['faction']
    ship.key = key
    # power: bulwarks first, then sails, then sick bay, then cannons
    for name in ('bulwark', 'sails', 'sickbay'):
        if name in ship.sys:
            while ship.add_power(name):
                if ship.reactor_free() <= sum(w.power for w in ship.weapons) and name != 'bulwark':
                    break
    for w in ship.weapons:
        if not ship.power_weapon(w):
            for name in ('sickbay', 'sails'):
                if name in ship.sys and ship.sys[name].power > 1 and ship.remove_power(name):
                    if ship.power_weapon(w):
                        break
    stations = [s for s in ('helm', 'guns', 'sails', 'bulwark', 'nest', 'sickbay') if s in ship.sys_room]
    classes = crew or d['crew']
    # put each crew member on the station they are best at, captain on the helm first
    order = sorted(classes, key=lambda c: 0 if c == 'captain' else (1 if c == 'drunk' else 2))
    used = set()
    for cls in order:
        c = Crew(cls, side='player', rng=rng)
        pref = {'captain': 'helm', 'drunk': 'guns', 'deckhand': 'sails', 'monkey': 'guns',
                'carpenter': 'bulwark', 'marine': 'bulwark', 'brute': 'guns'}.get(cls)
        room = None
        for st in ([pref] if pref else []) + stations:
            if st in ship.sys_room and st not in used:
                room = ship.sys_room[st]
                used.add(st)
                break
        ship.place(c, room, rng)
    return ship


def make_enemy(key, sector_idx, rng=random):
    t = data.ENEMIES[key]
    lv = dict(t['sys'])
    hull = t['hull'] + 2 * sector_idx
    if key not in ('boss', 'frigate'):
        if sector_idx >= 3 or (sector_idx >= 1 and lv.get('bulwark', 0) == 0):
            lv['bulwark'] = min(6, lv.get('bulwark', 0) + 2)
        lv['sails'] = lv.get('sails', 1) + sector_idx // 2
        lv['guns'] = lv.get('guns', 1) + sector_idx // 2
    weapons = list(t['weapons'])
    if sector_idx >= 3 and key not in ('boss', 'frigate') and len(weapons) < 3:
        weapons.append(rng.choice(['long_nine', 'chain_shot', 'hot_shot']))
        lv['guns'] = lv.get('guns', 1) + 1
    ship = Ship(rng.choice(t['names']), t['layout'], hull, lv, gusto=99, weapons=weapons,
                side='enemy', mirror=False, kind=key)
    ship.autopower()
    ship.shield_layers = ship.max_layers()
    crew_list = list(t['crew'])
    if sector_idx >= 2 and key not in ('boss',):
        crew_list.append({'ghost': 'ghost', 'crown': 'marine'}.get(t.get('faction'), 'pirate'))
    stations = [s for s in ('helm', 'guns', 'sails', 'bulwark') if s in ship.sys_room]
    for i, cls in enumerate(crew_list):
        c = Crew(cls, side='enemy', rng=rng)
        room = ship.sys_room[stations[i]] if i < len(stations) else None
        ship.place(c, room, rng)
        c.station = stations[i] if i < len(stations) else None
        c.facing = 1
    return ship
