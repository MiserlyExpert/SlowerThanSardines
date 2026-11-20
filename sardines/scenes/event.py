"""Text events with choices."""
import pygame

from .. import audio, data, gfx
from ..app import Scene
from ..config import H, W
from ..gfx import P

COLS = dict(good=P['dgreen'], bad=P['dred'])


class EventScene(Scene):
    overlay = True
    PX, PW = 90, 460

    def __init__(self, app, ev, notes=None):
        super().__init__(app)
        self.ev = ev
        self.ctx, self.target = self.gs.context()
        self.notes = list(notes or [])
        self.phase = 'choose'
        self.outcome = None
        self.summary = []
        self.body = self.fmt(ev['text'])
        self.title = self.fmt(ev.get('title', ''))
        self.buttons = []
        self._layout_choices()

    def fmt(self, s):
        return s.format_map(self.ctx)

    # ------------------------------------------------------------------
    def _text_height(self, txt):
        return len(gfx.wrap(txt, self.PW - 24, 16)) * 11

    def _layout_choices(self):
        self.buttons = []
        y = self._top() + 16 + (14 if self.title else 0) + self._text_height(self.body) + 10
        if self.notes:
            y += len(self.notes) * 11 + 4
        n = 0
        for ch in self.ev['choices']:
            req = ch.get('req', {})
            if 'crew' in req and not self.gs.has(req['crew']):
                continue
            n += 1
            label = self.fmt(ch['text'])
            if 'crew' in req:
                label = f"[{data.CREW[req['crew']]['title']}] {label}"
            label = f"{n}. {label}"
            ok = self.gs.meets(req)
            lines = gfx.wrap(label, self.PW - 28, 16)
            h = len(lines) * 12 + 4
            b = gfx.Button((self.PX + 12, y, self.PW - 24, h), label, (lambda c=ch: self.choose(c)),
                           enabled=ok, key=pygame.K_1 + n - 1, kind='choice')
            b.blue = 'crew' in req
            self.buttons.append(b)
            y += h + 2
        self.bottom = y + 6

    def _top(self):
        return 30

    def choose(self, ch):
        gs = self.gs
        if 'outs' in ch:
            total = sum(w for w, _ in ch['outs'])
            r = gs.rng.uniform(0, total)
            for w, o in ch['outs']:
                r -= w
                if r <= 0:
                    break
        else:
            o = ch['out']
        self.outcome = o
        self.summary = gs.apply(o, self.target)
        if not o.get('text') and not self.summary and not (o.get('fight') or o.get('store') or o.get('exit')
                                                           or o.get('next')):
            self.finish()
            return
        self.phase = 'result'
        self.body = self.fmt(o.get('text', ''))
        self.notes = []
        if self.summary:
            audio.play('win' if all(c == 'good' for _, c in self.summary) else 'click')
        y = self._top() + 16 + self._text_height(self.body) + 10 + len(self.summary) * 12 + 6
        label, cb = "Continue", self.finish
        if o.get('fight'):
            label, cb = "Battle stations!", self.fight
        elif o.get('store'):
            label, cb = "Browse the market", self.store
        elif o.get('exit'):
            label, cb = f"Sail on to {self.ctx['next']}", self.exit
        elif o.get('next'):
            label, cb = "Continue", self.next
        self.buttons = [gfx.Button((W // 2 - 80, y, 160, 20), label, cb, key=pygame.K_RETURN)]
        self.bottom = y + 26

    # ------------------------------------------------------------------
    def finish(self):
        self.gs.sector.node.cleared = True
        self.app.pop()

    def fight(self):
        from .combat import CombatScene
        o = self.outcome
        enemy = self.gs.make_enemy(o['fight'])
        fog = self.gs.sector.node.fog
        self.app.replace(CombatScene(self.app, enemy, o['fight'], fog=fog, win=o.get('win'),
                                     boss=o.get('boss', False)))

    def store(self):
        from .store import StoreScene
        self.app.replace(StoreScene(self.app, self.gs.sector.node))

    def exit(self):
        self.gs.next_sector()
        sec = self.gs.sector
        self.app.replace(EventScene(self.app, dict(
            id='sector', title=sec.name,
            text=sec.blurb + "\n\nThe Black Tide is still on your trail. It always will be. Keep moving.",
            choices=[dict(text="Onward!", out={})])))

    def next(self):
        self.app.replace(EventScene(self.app, self.outcome['next']))

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def draw(self, s):
        gfx.dim(s, 120)
        top = self._top()
        h = max(80, self.bottom - top)
        gfx.panel(s, (self.PX, top, self.PW, h), 'parch')
        y = top + 10
        if self.title and self.phase == 'choose':
            gfx.text(s, self.title.upper(), W // 2, y, P['dred'], 24, align='center')
            y += 20
        for line in gfx.wrap(self.body, self.PW - 24, 16):
            gfx.text(s, line, self.PX + 12, y, P['ink'], 16)
            y += 11
        y += 6
        for txt, c in self.notes:
            gfx.text(s, txt, self.PX + 12, y, COLS.get(c, P['ink']), 16)
            y += 11
        if self.phase == 'result':
            for txt, c in self.summary:
                gfx.text(s, txt, self.PX + 12, y, COLS.get(c, P['ink']), 16)
                y += 12
        else:
            pygame.draw.line(s, P['parch3'], (self.PX + 12, y), (self.PX + self.PW - 12, y))
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            if b.kind == 'choice' and getattr(b, 'blue', False) and b.enabled:
                hover = b.rect.collidepoint(m)
                if hover:
                    pygame.draw.rect(s, P['parch2'], b.rect)
                yy = b.rect.top + 2
                for line in gfx.wrap(b.label, b.rect.width - 4, 16):
                    gfx.text(s, line, b.rect.left + 2, yy, P['blue'] if not hover else P['purple'], 16)
                    yy += 12
            else:
                b.draw(s, m)
