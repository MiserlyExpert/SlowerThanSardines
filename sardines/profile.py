"""Persistent unlocks and lifetime stats (saved to ~/.slower_than_sardines/profile.json)."""
import json
import os
import sys

from . import data

PATH = os.environ.get('SARDINES_PROFILE') or os.path.join(os.path.expanduser('~'), '.slower_than_sardines',
                                                          'profile.json')
_profile = None
UNLOCK_ALL = '--unlock-all' in sys.argv or os.environ.get('SARDINES_UNLOCK_ALL') == '1'


def load():
    global _profile
    if _profile is None:
        _profile = dict(wins=0, best_sea=1, max_drunks=1, ghosts=0, unlocked=['sardine'], voyages=0, victories=0)
        try:
            with open(PATH) as f:
                _profile.update(json.load(f))
        except (OSError, ValueError):
            pass
    return _profile


def save():
    try:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        with open(PATH, 'w') as f:
            json.dump(load(), f, indent=1)
    except OSError:
        pass


def is_unlocked(key):
    return UNLOCK_ALL or key in load()['unlocked']


def record(**kw):
    """Update lifetime stats (max-merge) and return the names of any newly unlocked ships."""
    p = load()
    for k, v in kw.items():
        if k in ('wins', 'ghosts', 'voyages', 'victories'):
            p[k] = p.get(k, 0) + v
        else:
            p[k] = max(p.get(k, 0), v)
    new = []
    for key, d in data.SHIPS.items():
        u = d.get('unlock')
        if u and key not in p['unlocked'] and p.get(u[0], 0) >= u[1]:
            p['unlocked'].append(key)
            new.append(d['name'])
    save()
    return new
