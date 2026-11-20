"""Headless smoke tests. Run with: python -m pytest  (or python tests/test_smoke.py)."""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame  # noqa: E402

from sardines import data, events, model  # noqa: E402
from sardines.battle import Battle  # noqa: E402
from sardines.state import GameState  # noqa: E402


def autopilot(battle, rng):
    """A simple 'player' that targets enemy systems and sends crew to fix things."""
    p = battle.player
    for w in p.weapons:
        if w.target is None:
            rooms = [r.idx for r in battle.enemy.rooms if r.sys] or [0]
            w.target = rng.choice(rooms)
    boarders = [c for c in p.crew if c.side == 'enemy' and c.alive]
    mine = [c for c in p.crew if c.side == 'player' and c.alive]
    if boarders:
        room = boarders[0].cur_room()
        for c in mine:
            if c.cls != 'captain' and c.room != room and not c.moving and rng.random() < 0.05:
                c.order_move(room)
    else:
        for c in mine:
            st = getattr(c, 'home', None)
            if st is None:
                c.home = c.room
            if not c.moving and c.task in ('idle', 'man') and rng.random() < 0.02:
                r = next((r for r in p.rooms if r.fire > 0 or r.breach or
                          (r.sys and p.sys[r.sys].damage > 0 and not p.crew_in(r.idx, 'player'))), None)
                if r:
                    c.order_move(r.idx)
                elif c.room != c.home:
                    c.order_move(c.home)


def run_battle(key, sector, seed, max_t=400):
    gs = GameState(seed)
    gs.sector_idx = sector
    rng = random.Random(seed)
    enemy = model.make_enemy(key, sector, rng)
    b = Battle(gs, enemy, fog=(seed % 2 == 0), boss=(key == 'boss'), rng=rng)
    t = 0.0
    while not b.over and t < max_t:
        autopilot(b, rng)
        b.update(1 / 30)
        t += 1 / 30
    b.cleanup()
    return b.over, t


def test_battles_resolve():
    results = {}
    for key in data.ENEMIES:
        for seed in range(4):
            over, t = run_battle(key, 2 if key != 'sloop' else 0, seed)
            results.setdefault(key, []).append(over)
    for key, outs in results.items():
        assert all(o in (None, 'win', 'win_crew', 'lose', 'fled', 'enemy_fled') for o in outs), (key, outs)
    print(results)


def test_sectors_connected():
    rng = random.Random(1)
    for i in range(len(data.SECTORS)):
        for _ in range(20):
            from sardines.sector import Sector
            s = Sector(i, rng)
            assert len(s._component(0)) == len(s.nodes)
            assert s.nodes[-1].kind == 'exit'


def test_every_event_choice_applies():
    gs = GameState(3)
    for c in ('drunk', 'cook', 'carpenter', 'surgeon', 'monkey'):
        gs.recruit(c)
    pool = events.EVENTS + events.DISTRESS + [events.INTRO, events.tide_event(), events.port_event(gs.rng),
                                              events.exit_event(gs.sector, None)]
    for ev in pool:
        ctx, target = gs.context()
        ev['text'].format_map(ctx)
        for ch in ev['choices']:
            ch['text'].format_map(ctx)
            outs = [o for _, o in ch['outs']] if 'outs' in ch else [ch['out']]
            for o in outs:
                o.get('text', '').format_map(ctx)
                if o.get('fight'):
                    assert o['fight'] in data.ENEMIES
                gs.doubloons = gs.rum = gs.balls = 100
                gs.apply(o, target)
                if not gs.crew:
                    gs.recruit('deckhand')


def test_full_run_events():
    """Hop across all five seas taking random choices, auto-winning fights."""
    gs = GameState(11)
    for _ in range(5):
        for _ in range(40):
            sec = gs.sector
            nxt = max(sec.neighbours(), key=lambda i: sec.nodes[i].x + random.random() * 80)
            ev, notes = gs.jump(nxt)
            ch = random.choice([c for c in ev['choices'] if gs.meets(c.get('req', {}))] or ev['choices'])
            outs = [o for _, o in ch['outs']] if 'outs' in ch else [ch['out']]
            o = random.choice(outs)
            gs.apply(o)
            if o.get('fight'):
                gs.apply(gs.loot(o['fight'], 'win'))
            if sec.nodes[nxt].kind == 'exit':
                break
        if gs.sector_idx < 4:
            gs.next_sector()
    assert gs.sector_idx == 4


def test_scenes_render():
    from sardines.app import App
    from sardines.scenes.title import TitleScene, HelpScene
    from sardines.scenes.map import MapScene
    from sardines.scenes.event import EventScene
    from sardines.scenes.combat import CombatScene
    from sardines.scenes.store import StoreScene
    from sardines.scenes.shipwright import ShipwrightScene
    from sardines.scenes.endings import GameOverScene, VictoryScene
    app = App()
    out = os.environ.get('SHOTS')
    app.push(TitleScene(app))
    app.step(0.5)
    shots = [('title', None)]
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'title.png'))
    app.top.new_game()
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'intro.png'))
    app.pop()
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'map.png'))
    gs = app.gs
    gs.recruit('carpenter')
    gs.recruit('cook')
    for i, ev in enumerate(events.EVENTS[:3]):
        app.push(EventScene(app, ev))
        app.step(0.1)
        if out and i == 0:
            pygame.image.save(app.screen, os.path.join(out, 'event.png'))
        app.top.choose(ev['choices'][0])
        app.step(0.1)
        if out and i == 0:
            pygame.image.save(app.screen, os.path.join(out, 'event_result.png'))
        app.pop()
    for key, fog in (('brig', False), ('ghost', True), ('boss', False)):
        enemy = gs.make_enemy(key)
        cs = CombatScene(app, enemy, key, fog=fog, boss=(key == 'boss'))
        app.push(cs)
        for w in gs.ship.weapons:
            w.target = enemy.sys_room.get('guns', 0)
        for k in range(60 * 25):
            app.step(1 / 60)
            if cs.battle.over:
                break
            if out and k == 60 * 14:
                pygame.image.save(app.screen, os.path.join(out, f'combat_{key}.png'))
        cs.battle.cleanup()
        while app.top is not cs and app.top in app.stack and len(app.stack) > 1 and not isinstance(app.top, MapScene):
            app.pop()
        if app.top is cs:
            app.pop()
    app.push(StoreScene(app, gs.sector.node))
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'store.png'))
    app.pop()
    gs.cargo.append('carronade')
    app.push(ShipwrightScene(app))
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'shipwright.png'))
    app.pop()
    app.push(HelpScene(app))
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'help.png'))
    app.pop()
    gs.cause = 'sunk'
    app.push(GameOverScene(app))
    app.step(0.1)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'gameover.png'))
    app.push(VictoryScene(app))
    app.step(0.5)
    if out:
        pygame.image.save(app.screen, os.path.join(out, 'victory.png'))


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
