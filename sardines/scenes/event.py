"""Text events with choices."""
import pygame

from .. import audio, data, gfx
from ..app import Scene
from ..config import H, W
from ..gfx import P

COLS = dict(good=P['dgreen'], bad=P['dred'])


class EventScene(Scene):
    overlay = True
    PX, PW = 80, 480
    PAD = 14
    LH = 11

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
        return len(gfx.wrap(txt, self.PW - self.PAD * 2)) * self.LH

    def _layout_choices(self):
        self.buttons = []
        y = self._top() + 12 + (24 if self.title else 0) + self._text_height(self.body) + 8
        if self.notes:
            y += len(self.notes) * self.LH + 4
        y += 6
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
            lines = gfx.wrap(label, self.PW - self.PAD * 2 - 8)
            h = len(lines) * gfx.CHOICE_LINE + 5
            b = gfx.Button((self.PX + self.PAD - 4, y, self.PW - self.PAD * 2 + 8, h), label, (lambda c=ch: self.choose(c)),
                           enabled=ok, key=pygame.K_1 + n - 1, kind='choice')
            b.blue = 'crew' in req
            self.buttons.append(b)
            y += h + 2
        self.bottom = y + 8

    def _top(self):
        return 34

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
        y = self._top() + 12 + self._text_height(self.body) + 10 + len(self.summary) * 12 + 8
        label, cb = "Continue", self.finish
        if o.get('fight'):
            label, cb = "Battle stations!", self.fight
        elif o.get('store'):
            label, cb = "Browse the market", self.store
        elif o.get('exit'):
            label, cb = f"Sail on to {self.ctx['next']}", self.exit
        elif o.get('next'):
            label, cb = "Continue", self.next
        self.buttons = [gfx.Button((W // 2 - 90, y, 180, 22), label, cb, key=pygame.K_RETURN)]
        self.bottom = y + 32

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
            text=sec.blurb + "\n\nThe Royal Armada is still on your trail, brass band and all. Keep moving."
            + ''.join('\n\n' + n for n in getattr(self.gs, 'new_unlocks', [])),
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
        y = top + 12
        if self.title and self.phase == 'choose':
            gfx.text(s, self.title.upper(), W // 2, y, P['dred'], 24, align='center')
            y += 24
        for line in gfx.wrap(self.body, self.PW - self.PAD * 2):
            gfx.text(s, line, self.PX + self.PAD, y, P['ink'])
            y += self.LH
        y += 8
        for txt, c in self.notes:
            gfx.text(s, txt, self.PX + self.PAD, y, COLS.get(c, P['ink']))
            y += self.LH
        if self.phase == 'result':
            for txt, c in self.summary:
                gfx.text(s, '> ' + txt, self.PX + self.PAD, y, COLS.get(c, P['ink']))
                y += 12
        else:
            pygame.draw.line(s, P['parch3'], (self.PX + self.PAD, y), (self.PX + self.PW - self.PAD, y))
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            if b.kind == 'choice' and getattr(b, 'blue', False) and b.enabled:
                hover = b.rect.collidepoint(m)
                if hover:
                    pygame.draw.rect(s, P['parch2'], b.rect)
                yy = b.rect.top + 3
                for line in gfx.wrap(b.label, b.rect.width - 8):
                    gfx.text(s, line, b.rect.left + 4, yy, P['blue'] if not hover else P['purple'])
                    yy += gfx.CHOICE_LINE
            else:
                b.draw(s, m)
