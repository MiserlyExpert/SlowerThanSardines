"""Sea chart (sector map) generation."""
import math

from . import data

MAP_X0, MAP_X1 = 46, 596
MAP_Y0, MAP_Y1 = 74, 300
FLEET_STEP = 34


class Node:
    def __init__(self, idx, x, y, kind='event'):
        self.idx, self.x, self.y, self.kind = idx, x, y, kind
        self.visited = False
        self.fog = False
        self.store = None
        self.cleared = False


class Sector:
    def __init__(self, idx, rng):
        d = data.SECTORS[idx]
        self.idx = idx
        self.d = d
        self.name = d['name']
        self.blurb = d['blurb']
        self.final = d.get('final', False)
        self.nodes = []
        self.edges = {}
        self.fogs = []
        self._generate(rng)
        self.fleet_x = -70.0
        self.cur = 0
        self.nodes[0].visited = True

    def _generate(self, rng):
        pts = [(28, rng.randint(150, 230)), (612, rng.randint(120, 250))]
        tries = 0
        while len(pts) < 22 and tries < 4000:
            tries += 1
            x, y = rng.randint(MAP_X0 + 30, MAP_X1 - 30), rng.randint(MAP_Y0, MAP_Y1)
            if all(math.hypot(x - a, y - b) >= 48 for a, b in pts):
                pts.append((x, y))
        start, exit_ = pts[0], pts[1]
        mids = sorted(pts[2:])
        pts = [start] + mids + [exit_]
        self.nodes = [Node(i, x, y) for i, (x, y) in enumerate(pts)]
        self.nodes[0].kind = 'start'
        self.nodes[-1].kind = 'exit'
        n = len(self.nodes)
        self.edges = {i: set() for i in range(n)}

        def dist(i, j):
            a, b = self.nodes[i], self.nodes[j]
            return math.hypot(a.x - b.x, a.y - b.y)

        for i in range(n):
            for j in range(i + 1, n):
                if dist(i, j) < 92:
                    self._link(i, j)
        for i in range(n):
            if len(self.edges[i]) < 2:
                near = sorted((j for j in range(n) if j != i and j not in self.edges[i]),
                              key=lambda j: dist(i, j))
                for j in near[:2 - len(self.edges[i])]:
                    self._link(i, j)
        # make sure everything is connected
        while True:
            comp = self._component(0)
            if len(comp) == n:
                break
            best = min(((i, j) for i in comp for j in range(n) if j not in comp),
                       key=lambda ij: dist(*ij))
            self._link(*best)
        # node kinds
        mid = list(range(1, n - 1))
        rng.shuffle(mid)
        k = 0
        for _ in range(self.d['ports']):
            self.nodes[mid[k]].kind = 'port'
            k += 1
        for _ in range(3):
            self.nodes[mid[k]].kind = 'distress'
            k += 1
        # fog banks
        for _ in range(self.d['fog']):
            cx, cy = rng.randint(140, 540), rng.randint(MAP_Y0, MAP_Y1)
            r = rng.randint(40, 72)
            self.fogs.append((cx, cy, r))
        for nd in self.nodes[1:]:
            if any(math.hypot(nd.x - cx, nd.y - cy) < r for cx, cy, r in self.fogs):
                nd.fog = True

    def _link(self, i, j):
        self.edges[i].add(j)
        self.edges[j].add(i)

    def _component(self, s):
        seen = {s}
        stack = [s]
        while stack:
            a = stack.pop()
            for b in self.edges[a]:
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        return seen

    @property
    def node(self):
        return self.nodes[self.cur]

    def neighbours(self):
        return self.edges[self.cur]

    def overrun(self, nd):
        return nd.x < self.fleet_x
