"""Real-time naval combat simulation. Pure logic, no rendering, so it is testable headless."""
import random

from . import data


class Battle:
    PROJ_TIME = 0.9

    def __init__(self, gs, enemy, fog=False, boss=False, rng=None):
        self.gs = gs
        self.rng = rng or random.Random()
        self.player = gs.ship
        self.enemy = enemy
        self.fog = fog
        self.boss = boss
        self.angry = False
        self.t = 0.0
        self.projectiles = []
        self.events = []
        self.over = None
        self.ai_t = 0.0
        self.bark_t = 4.0
        self.board_t = self.rng.uniform(18, 30)
        self.boards_left = 2 if boss else (1 if self.rng.random() < data.ENEMIES[enemy.kind]['grapple'] else 0)
        if boss:
            self.boards_left = 3
        for w in self.player.weapons:
            w.charge = 0.0
            w.target = None
        self.player.escape = 0.0
        self.board_cd = 0.0
        for c in self.player.crew:
            c.axes = getattr(gs, 'axes', False)
        self.player.shield_layers = self.player.max_layers()

    # ------------------------------------------------------------------
    def emit(self, kind, **kw):
        kw['kind'] = kind
        self.events.append(kw)

    def other(self, ship):
        return self.enemy if ship is self.player else self.player

    def side_alive(self, side):
        return [c for s in (self.player, self.enemy) for c in s.crew if c.alive and c.side == side]

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.over:
            return
        self.t += dt
        self.board_cd = max(0.0, self.board_cd - dt)
        self.enemy.autopower()
        for ship in (self.player, self.enemy):
            ship.update(dt, self)
        for ship in (self.player, self.enemy):
            self._update_weapons(ship, dt)
            self._update_escape(ship, dt)
        for p in list(self.projectiles):
            p['t'] += dt
            if p['t'] >= p['dur']:
                self.projectiles.remove(p)
                self._resolve(p)
        self.ai_t -= dt
        if self.ai_t <= 0:
            self.ai_t = 0.5
            self._ai()
        self._barks(dt)
        self._check_end()

    # ------------------------------------------------------------------
    def _update_weapons(self, ship, dt):
        target_ship = self.other(ship)
        mult = 1.0
        m = ship.manned('guns')
        if m:
            mult = m.skill('guns')
        if ship is self.enemy and self.angry:
            mult *= 1.35
        guns = ship.sys.get('guns')
        for w in ship.weapons:
            if w.powered and guns and guns.intact > 0:
                w.charge = min(1.0, w.charge + dt * mult / w.d['charge'])
            else:
                w.charge = max(0.0, w.charge - dt * 0.4)
            if w.charge >= 1.0 and w.target is not None and target_ship.hull > 0:
                if w.d.get('ammo'):
                    if ship is self.player:
                        if self.gs.balls <= 0:
                            continue
                        self.gs.balls -= 1
                    else:
                        if ship.ammo <= 0:
                            continue
                        ship.ammo -= 1
                for i in range(w.d['shots']):
                    self.projectiles.append(dict(src=ship, dst=target_ship, room=w.target, w=w.d,
                                                 key=w.key, t=-i * 0.18, dur=self.PROJ_TIME,
                                                 slot=ship.weapons.index(w)))
                w.charge = 0.0
                self.emit('shoot', ship=ship, weapon=w)
                gunner = ship.manned('guns')
                if gunner and gunner.cls == 'drunk' and self.rng.random() < 0.25:
                    gunner.say(self.rng.choice(data.BARKS['drunk']))
                if ship is self.enemy:
                    w.target = None

    def _update_escape(self, ship, dt):
        if ship is self.enemy and not ship.fleeing:
            return
        if ship.can_escape():
            sails = ship.sys['sails'].eff()
            base = 20.0 if ship is self.player else 26.0
            if self.fog:
                base *= 2
            ship.escape = min(1.0, ship.escape + dt * (1 + 0.08 * sails) / base)
        if ship is self.enemy and ship.escape >= 1.0:
            self.over = 'enemy_fled'

    def player_board(self, crew):
        """Swing selected crew standing on our top deck across to the enemy's top deck."""
        if not self.player.grapple or self.board_cd > 0 or self.over:
            return 0
        from .config import TOP_ROW
        ready = [c for c in crew if c.alive and c.ship is self.player and not c.moving
                 and self.player.rooms[c.room].gy == TOP_ROW][:3]
        if not ready:
            return 0
        tops = self.enemy.top_rooms()
        for c in ready:
            self.player.crew.remove(c)
            c.path, c.foe = [], None
            self.enemy.place(c, self.rng.choice(tops), self.rng)
        self.board_cd = 20.0
        self.emit('pboard', ship=self.enemy, room=ready[0].room, n=len(ready))
        return len(ready)

    def player_recall(self):
        from .config import TOP_ROW
        home = [c for c in self.enemy.crew if c.alive and c.side == 'player' and not c.moving
                and self.enemy.rooms[c.room].gy == TOP_ROW]
        tops = self.player.top_rooms()
        for c in home:
            self.enemy.crew.remove(c)
            c.path, c.foe = [], None
            self.player.place(c, self.rng.choice(tops), self.rng)
        return len(home)

    def player_flee(self):
        if self.player.escape >= 1.0 and not self.over:
            self.over = 'fled'
            return True
        return False

    # ------------------------------------------------------------------
    def _resolve(self, p):
        dst, src, wd = p['dst'], p['src'], p['w']
        if dst.hull <= 0 or self.over:
            return
        room = dst.rooms[p['room']]
        ev = dst.evasion(self.fog)
        nest = src.sys.get('nest')
        if nest and nest.eff() >= 3:
            ev -= 10
        if self.rng.random() * 100 < ev:
            self.emit('miss', ship=dst, room=room.idx)
            return
        if not wd.get('pierce') and dst.shield_layers > 0:
            dst.shield_layers -= 1
            dst.shield_t = 0.0
            self.emit('block', ship=dst, room=room.idx)
            return
        dmg = wd['dmg']
        dst.hull = max(0, dst.hull - dmg - wd.get('hull', 0))
        if room.sys and (dmg > 0 or wd.get('sys')):
            dst.damage_system(room.sys, dmg + wd.get('sys', 0))
        crew_dmg = wd.get('crew', 12 * dmg)
        for c in dst.crew_in(room.idx):
            c.hp -= crew_dmg
        fire_p = wd.get('fire', 0.1 if dmg else 0.0)
        breach_p = wd.get('breach', 0.12 * dmg)
        if room.fire <= 0 and self.rng.random() < fire_p:
            room.fire = 25.0
            self.emit('fire', ship=dst, room=room.idx)
        if not room.breach and self.rng.random() < breach_p:
            room.breach = True
            self.emit('breach', ship=dst, room=room.idx)
        self.emit('hit', ship=dst, room=room.idx, dmg=dmg + wd.get('hull', 0), crew=crew_dmg if wd.get('crew') else 0)

    # ------------------------------------------------------------------
    def _ai(self):
        e, p = self.enemy, self.player
        rng = self.rng
        # weapons: choose targets
        sys_rooms = [r.idx for r in p.rooms if r.sys]
        prio = [p.sys_room[s] for s in ('guns', 'bulwark', 'helm', 'sails') if s in p.sys_room]
        for w in e.weapons:
            if w.target is None and w.charge > 0.6:
                roll = rng.random()
                if roll < 0.5:
                    w.target = rng.choice(prio)
                elif roll < 0.85:
                    w.target = rng.choice(sys_rooms)
                else:
                    w.target = rng.randrange(len(p.rooms))
        # crew on own ship
        own = [c for c in e.crew if c.alive and c.side == 'enemy']
        needy = []
        for r in e.rooms:
            score = 0
            if r.fire > 0:
                score += 3 + r.fire / 30
            if r.breach:
                score += 2
            if r.sys and e.sys[r.sys].damage > 0:
                score += 1 + e.sys[r.sys].damage * (2 if r.sys in ('helm', 'guns', 'bulwark') else 1)
            if any(o.side != 'enemy' for o in e.crew_in(r.idx)):
                score += 4
            if score:
                needy.append((score, r.idx))
        needy.sort(reverse=True)
        busy = {c.room for c in own if c.moving}
        for score, ri in needy:
            if any(c.room == ri for c in own):
                continue
            # pick a responder: station-less first, then least important station
            cands = [c for c in own if not c.moving and not getattr(c, 'station', None)]
            if not cands:
                order = {'bulwark': 0, 'sails': 1, 'guns': 2, 'helm': 3}
                cands = sorted([c for c in own if not c.moving and c.task in ('man', 'idle')],
                               key=lambda c: order.get(getattr(c, 'station', None), -1))
                if score < 3:
                    cands = []
            if cands:
                cands[0].order_move(ri)
                busy.add(ri)
        # return to stations when there is nothing needy in their current room
        needy_rooms = {ri for _, ri in needy}
        for c in own:
            st = getattr(c, 'station', None)
            if st and not c.moving and st in e.sys_room and c.room != e.sys_room[st] \
                    and c.room not in needy_rooms:
                c.order_move(e.sys_room[st])
        # stations that lost their crew get backfilled
        for st in ('helm', 'guns'):
            if st in e.sys_room and not any(getattr(c, 'station', None) == st for c in own):
                spare = [c for c in own if getattr(c, 'station', None) in (None, 'bulwark', 'sails')]
                if spare:
                    spare[0].station = st
        # boarders on the player's ship
        for c in p.crew:
            if c.alive and c.side == 'enemy' and not c.moving and c.task == 'idle':
                targets = [r.idx for r in p.rooms if r.sys and p.sys[r.sys].intact > 0]
                defenders = [r.idx for r in p.rooms if p.crew_in(r.idx, 'player')]
                pool = defenders if (defenders and rng.random() < 0.5) else targets
                if pool:
                    c.order_move(rng.choice(pool))
        # boarding
        if self.boards_left > 0 and not self.over:
            self.board_t -= 0.5
            if self.board_t <= 0 and len(own) >= 3:
                self.boards_left -= 1
                self.board_t = rng.uniform(35, 55)
                party = [c for c in own if getattr(c, 'station', None) not in ('helm',)]
                party = sorted(party, key=lambda c: -c.skill('fight'))[:2]
                dest = rng.choice(p.top_rooms())
                for c in party:
                    e.crew.remove(c)
                    c.path = []
                    c.station = None
                    p.place(c, dest, rng)
                self.emit('board', ship=p, room=dest, n=len(party))
        # fleeing
        if e.kind and data.ENEMIES[e.kind]['flee'] and not e.fleeing and e.hull <= e.hull_max * 0.3:
            if rng.random() < 0.05:
                e.fleeing = True
                self.emit('enemy_flee', ship=e)
        # boss rage
        if self.boss and not self.angry and e.hull <= e.hull_max // 2:
            self.angry = True
            self.emit('angry', ship=e)

    def _barks(self, dt):
        self.bark_t -= dt
        if self.bark_t > 0:
            return
        self.bark_t = self.rng.uniform(6, 12)
        pool = [c for s in (self.player, self.enemy) for c in s.crew if c.alive]
        if not pool:
            return
        c = self.rng.choice(pool)
        lines = data.BARKS.get(c.cls)
        if lines:
            c.say(self.rng.choice(lines))

    def _check_end(self):
        if self.over:
            return
        if self.player.hull <= 0:
            self.over = 'lose'
            self.gs.cause = 'sunk'
        elif not self.side_alive('player'):
            self.over = 'lose'
            self.gs.cause = 'crew'
        elif self.enemy.hull <= 0:
            self.over = 'win'
        elif not self.side_alive('enemy'):
            self.over = 'win_crew'

    # ------------------------------------------------------------------
    def cleanup(self):
        """Called after the battle ends: remove boarders, mop up hazards, fix systems."""
        ship = self.player
        for c in list(self.enemy.crew):          # boarders swim home, soggy
            if c.side == 'player' and c.alive:
                self.enemy.crew.remove(c)
                c.hp = max(1, c.hp - (25 if self.over in ('win', 'enemy_fled') else 0))
                ship.place(c, None, self.rng)
        ship.crew = [c for c in ship.crew if c.side == 'player' and c.alive]
        for r in ship.rooms:
            r.fire = r.water = 0.0
            r.breach = False
            r.breach_prog = 0.0
        for s in ship.sys.values():
            s.damage = 0
            s.repair_prog = s.harm_prog = 0.0
            ship.restore_power(s)
        for c in ship.crew:
            c.path = []
            c.x, c.y = ship.rooms[c.room].tile_center(c.tile)
            c.bark_t = 0
            c.foe = None
        for w in ship.weapons:
            w.charge = 0.0
            w.target = None
        ship.escape = 0.0
