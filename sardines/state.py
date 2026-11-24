"""Run state: resources, outcomes, loot, travel."""
import random

from . import data, events, model, profile
from .config import MAX_CREW, MAX_WEAPONS
from .sector import FLEET_STEP, Sector


class SafeDict(dict):
    def __missing__(self, k):
        return '{' + k + '}'


class GameState:
    def __init__(self, seed=None, ship_key='sardine', crew=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.ship_key = ship_key
        d = data.SHIPS[ship_key]
        self.ship = model.make_player_ship(self.rng, ship_key, crew)
        self.doubloons = d['doubloons']
        self.rum = d['rum']
        self.balls = d['balls']
        self.cargo = []
        self.sector_idx = 0
        self.sector = Sector(0, self.rng)
        self.stats = dict(jumps=0, wins=0, doubloons=0, sea=1)
        self.cause = None
        self.enemy = None
        self.goods = {k: 0 for k in data.GOODS}
        self.seen = set()
        self.pending = {}

    # ------------------------------------------------------------------
    @property
    def crew(self):
        away = [c for c in getattr(self, 'enemy', None).crew if c.side == 'player' and c.alive] \
            if getattr(self, 'enemy', None) is not None else []
        return [c for c in self.ship.crew if c.side == 'player' and c.alive] + away

    def has(self, cls):
        return any(c.cls == cls for c in self.crew)

    def first(self, cls):
        for c in self.crew:
            if c.cls == cls:
                return c
        return None

    def context(self, rng=None):
        rng = rng or self.rng
        crew = self.crew
        pick = rng.choice(crew) if crew else None
        drunk, cap = self.first('drunk'), self.first('captain')
        nxt = data.SECTORS[self.sector_idx + 1]['name'] if self.sector_idx + 1 < len(data.SECTORS) else ''
        ctx = SafeDict(drunk=drunk.name if drunk else 'the drunkest sailor aboard',
                       captain=cap.name if cap else 'the captain',
                       crew=pick.name if pick else 'nobody', ship=self.ship.name,
                       sector=self.sector.name, next=nxt)
        return ctx, pick

    def meets(self, req):
        if not req:
            return True
        if 'crew' in req and not self.has(req['crew']):
            return False
        if 'crew_n' in req and len(self.crew) < req['crew_n']:
            return False
        for k in ('doubloons', 'rum', 'balls'):
            if k in req and getattr(self, k) < req[k]:
                return False
        return True

    # ------------------------------------------------------------------
    def _val(self, v):
        return self.rng.randint(*v) if isinstance(v, tuple) else v

    def apply(self, o, target=None):
        """Apply an outcome dict. Returns a list of (text, colour-key) summary lines."""
        out = []
        for key, label in (('doubloons', 'Doubloons'), ('rum', 'Rum'), ('balls', 'Cannonballs')):
            if key in o:
                n = self._val(o[key])
                before = getattr(self, key)
                setattr(self, key, max(0, before + n))
                n = getattr(self, key) - before
                if key == 'doubloons' and n > 0:
                    self.stats['doubloons'] += n
                if n:
                    out.append((f"{'+' if n > 0 else ''}{n} {label}", 'good' if n > 0 else 'bad'))
        if 'hull' in o:
            n = self._val(o['hull'])
            before = self.ship.hull
            self.ship.hull = max(1, min(self.ship.hull_max, self.ship.hull + n))
            n = self.ship.hull - before
            if n:
                out.append((f"{'+' if n > 0 else ''}{n} Hull", 'good' if n > 0 else 'bad'))
        if 'heal' in o:
            for c in self.crew:
                c.hp = min(c.max_hp, c.hp + o['heal'])
            out.append((f"Crew healed {o['heal']}", 'good'))
        if 'all_hurt' in o:
            for c in self.crew:
                c.hp = max(1, c.hp - o['all_hurt'])
            out.append((f"All crew -{o['all_hurt']} HP", 'bad'))
        if 'crew_hurt' in o:
            c = target if (target and target.alive) else (self.rng.choice(self.crew) if self.crew else None)
            if c:
                c.hp = max(1, c.hp - o['crew_hurt'])
                out.append((f"{c.name} -{o['crew_hurt']} HP", 'bad'))
        if o.get('lose_crew') and len(self.crew) > 1:
            c = target if (target and target in self.crew) else self.rng.choice(self.crew)
            self.ship.crew.remove(c)
            out.append((f"{c.name} left the crew", 'bad'))
        if 'add_crew' in o:
            c = self.recruit(o['add_crew'])
            if c:
                out.append((f"{c.name} the {c.title} joined!", 'good'))
                for name in profile.record(max_drunks=sum(1 for x in self.crew if x.cls == 'drunk')):
                    out.append((f"NEW SHIP UNLOCKED: {name}!", 'good'))
            else:
                out.append(("No room for more crew", 'bad'))
        if 'weapon' in o:
            key = o['weapon']
            if key == 'random':
                key = self.rng.choice(data.LOOT_WEAPONS)
            out.append((self.add_weapon(key), 'good'))
        if 'gusto' in o:
            self.ship.hands_bonus += o['gusto']
            out.append((f"+{o['gusto']} Hands (morale!)", 'good'))
        if 'goods' in o:
            key = o['goods']
            n = min(self.rng.randint(1, 3), self.cargo_cap() - self.cargo_used())
            if n > 0:
                self.goods[key] += n
                out.append((f"+{n} {data.GOODS[key]['title']}", 'good'))
            else:
                out.append((f"No cargo space for {data.GOODS[key]['title']}", 'bad'))
        if 'upgrade' in o:
            s = self.ship.sys.get(o['upgrade'])
            if s and s.level < data.SYSTEMS[s.name]['max']:
                s.level += 1
                out.append((f"{data.SYSTEMS[s.name]['title']} upgraded", 'good'))
        if 'fleet' in o:
            self.sector.fleet_x += o['fleet']
            out.append(("The Armada gains on you" if o['fleet'] > 0 else "The Armada falls behind",
                        'bad' if o['fleet'] > 0 else 'good'))
        return out

    def recruit(self, cls):
        if len(self.crew) >= MAX_CREW:
            return None
        if cls == 'random':
            cls = self.rng.choice(data.HIREABLE)
        c = model.Crew(cls, side='player', rng=self.rng)
        self.ship.place(c, None, self.rng)
        return c

    def add_weapon(self, key):
        name = data.WEAPONS[key]['name']
        if len(self.ship.weapons) < MAX_WEAPONS:
            self.ship.weapons.append(model.Weapon(key))
            return f"New cannon: {name}"
        self.cargo.append(key)
        return f"{name} stowed in the hold"

    # ------------------------------------------------------------------
    def make_enemy(self, key):
        if key in self.pending:
            return self.pending.pop(key)
        return model.make_enemy(key, self.sector_idx, self.rng)

    def cargo_cap(self):
        return data.BASE_CARGO + data.CARGO_PER_HOLD * self.ship.module_level('hold')

    def cargo_used(self):
        return sum(self.goods.values())

    def loot(self, enemy_key, how):
        rng = self.rng
        base = 12 + 7 * self.sector_idx
        d = rng.randint(base, base + 12)
        d = int(d * data.ENEMIES.get(enemy_key, {}).get('gold', 1.0))
        if enemy_key in ('frigate', 'galleon'):
            d = int(d * 1.4)
        if how == 'win_crew':
            d = int(d * 1.5)
        o = dict(doubloons=d)
        rum = data.ENEMIES.get(enemy_key, {}).get('rum', 0)
        if rng.random() < 0.55 or rum:
            o['rum'] = rng.randint(1, 3) + rum
        if rng.random() < 0.45:
            o['balls'] = rng.randint(1, 3)
        if rng.random() < 0.12 + (0.2 if how == 'win_crew' else 0) + (0.2 if enemy_key == 'frigate' else 0):
            o['weapon'] = 'random'
        if how == 'win_crew' and rng.random() < 0.25:
            o['add_crew'] = 'random'
        mag = self.ship.module_level('magazine')
        if mag:
            o['balls'] = o.get('balls', 0) + mag
        if self.enemy_had_hold and rng.random() < 0.7:
            o['goods'] = rng.choice(list(data.GOODS))
        return o

    enemy_had_hold = False

    def prisoner_chance(self):
        return 0.4 * self.ship.module_level('brig')

    # ------------------------------------------------------------------
    def can_jump(self, idx):
        return idx in self.sector.neighbours()

    def jump(self, idx):
        """Travel to a node. Returns (event dict, notes)."""
        sec = self.sector
        notes = []
        src = sec.node
        dst = sec.nodes[idx]
        if self.rum > 0:
            self.rum -= 1
        else:
            for c in self.crew:
                c.hp = max(1, c.hp - (25 if c.cls == 'drunk' else 12))
            notes.append(("Sailing sober! The crew suffers withdrawal.", 'bad'))
        days = 2 if (src.fog or dst.fog) else 1
        chart = self.ship.module_level('chartroom')
        sec.fleet_x += FLEET_STEP * days * (1.0 - 0.1 * chart)
        if days == 2:
            notes.append(("The fog slows you down: 2 days pass.", 'bad'))
        galley = self.ship.module_level('galley')
        heal = 10 * galley * (2 if self.has('cook') else 1) + (10 if self.has('cook') else 0)
        if heal:
            for c in self.crew:
                c.hp = min(c.max_hp, c.hp + heal)
        bar = self.ship.module_level('bar')
        if bar:
            self.rum += bar
            notes.append((f"The Bar brews {bar} Rum.", 'good'))
        sec.cur = idx
        first_visit = not dst.visited
        dst.visited = True
        self.stats['jumps'] += 1
        return self.event_for(dst, first_visit), notes

    def event_for(self, nd, first_visit):
        sec = self.sector
        rng = self.rng
        if nd.kind == 'exit':
            return events.exit_event(sec, None)
        if sec.overrun(nd) and not nd.cleared:
            return events.armada_event()
        if nd.kind == 'port':
            if nd.store is None:
                from .scenes.harbor import gen_port
                nd.store = gen_port(self)
            return dict(id='port', text='', choices=[])
        if not first_visit or nd.cleared:
            return dict(id='quiet', text=rng.choice(events.QUIET), choices=[dict(text="Continue.", out={})])
        if nd.kind == 'distress':
            return self._pick(events.DISTRESS, nd)
        r = rng.random()
        if r < 0.42:
            key = rng.choice(sec.d['pool'])
            enemy = model.make_enemy(key, self.sector_idx, rng)
            self.pending = {key: enemy}
            return events.fight_event(key, data.ENEMIES[key]['name'], enemy.name, rng)
        if r < 0.5:
            return dict(id='quiet', text=rng.choice(events.QUIET), choices=[dict(text="Continue.", out={})])
        return self._pick(events.EVENTS, nd)

    def _pick(self, pool, nd):
        ok = []
        for e in pool:
            tags = e.get('tags', [])
            if 'fog' in tags and not nd.fog:
                continue
            if 'sectors' in e and self.sector_idx not in e['sectors']:
                continue
            ok.append(e)
        fresh = [e for e in ok if e['id'] not in self.seen] or ok
        e = self.rng.choice(fresh)
        self.seen.add(e['id'])
        return e

    def unlock_notes(self, **kw):
        return [f"NEW SHIP UNLOCKED: {n}!" for n in profile.record(**kw)]

    def next_sector(self):
        self.sector_idx += 1
        self.new_unlocks = self.unlock_notes(best_sea=self.sector_idx + 1)
        self.stats['sea'] = self.sector_idx + 1
        self.sector = Sector(self.sector_idx, self.rng)
        self.pending = {}
