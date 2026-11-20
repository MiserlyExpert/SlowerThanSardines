"""Synthesized sound effects and a chiptune 'Drunken Sailor'. No audio files needed."""
import array
import math
import random

import pygame

SR = 22050
_sounds = {}
_music = None
_ok = False
_channels = 1
music_on = True
sfx_on = True


def _to_sound(samples, vol=0.5):
    data = array.array('h')
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32767 * vol)
        for _ in range(_channels):
            data.append(v)
    return pygame.mixer.Sound(buffer=data.tobytes())


def _env(n, attack=0.005, decay=None):
    a = max(1, int(attack * SR))
    out = []
    for i in range(n):
        e = i / a if i < a else math.exp(-(i - a) / (decay * SR)) if decay else 1 - (i - a) / max(1, n - a)
        out.append(e)
    return out


def _noise(dur, decay, lp=0.3, seed=1):
    rng = random.Random(seed)
    n = int(dur * SR)
    env = _env(n, 0.002, decay)
    y = 0.0
    out = []
    for i in range(n):
        y += lp * (rng.uniform(-1, 1) - y)
        out.append(y * env[i] * 2.2)
    return out


def _tone(dur, f0, f1=None, decay=0.2, wave='sine', vol=1.0):
    n = int(dur * SR)
    f1 = f1 or f0
    env = _env(n, 0.003, decay)
    ph = 0.0
    out = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        ph += f / SR
        if wave == 'sine':
            v = math.sin(2 * math.pi * ph)
        elif wave == 'square':
            v = 1.0 if (ph % 1) < 0.5 else -1.0
        else:  # triangle
            v = 4 * abs((ph % 1) - 0.5) - 1
        out.append(v * env[i] * vol)
    return out


def _mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def _build():
    s = {}
    s['cannon'] = _to_sound(_mix(_noise(0.5, 0.12, 0.25, 1), _tone(0.4, 90, 35, 0.12)), 0.55)
    s['hit'] = _to_sound(_mix(_noise(0.35, 0.08, 0.6, 2), _tone(0.2, 160, 60, 0.06)), 0.5)
    s['splash'] = _to_sound(_noise(0.5, 0.18, 0.12, 3), 0.45)
    s['block'] = _to_sound(_mix(_tone(0.18, 140, 110, 0.05), _noise(0.12, 0.03, 0.4, 4)), 0.5)
    s['click'] = _to_sound(_tone(0.04, 900, 700, 0.02, 'square', 0.3), 0.4)
    s['hic'] = _to_sound(_tone(0.12, 300, 900, 0.06), 0.4)
    s['bell'] = _to_sound(_mix(_tone(1.2, 880, None, 0.4), _tone(1.2, 1320, None, 0.25, vol=0.5)), 0.3)
    s['fire'] = _to_sound(_noise(0.4, 0.15, 0.8, 5), 0.35)
    s['board'] = _to_sound(_mix(_tone(0.3, 200, 500, 0.1, 'square', 0.3), _noise(0.3, 0.1, 0.5, 6)), 0.4)
    s['death'] = _to_sound(_tone(0.5, 400, 120, 0.2, 'triangle'), 0.45)
    win = []
    for f in (523, 659, 784, 1046):
        win += _tone(0.13, f, None, 0.1, 'square', 0.4)
    s['win'] = _to_sound(win, 0.35)
    lose = []
    for f in (392, 349, 311, 262):
        lose += _tone(0.25, f, None, 0.2, 'triangle')
    s['lose'] = _to_sound(lose, 0.4)
    return s


def _build_music():
    """'What Shall We Do With a Drunken Sailor' (traditional, public domain) as a chiptune loop."""
    N = dict(C4=261.63, D4=293.66, E4=329.63, F4=349.23, G4=392.0, A4=440.0, B4=493.88,
             D3=146.83, C3=130.81, A2=110.0, G2=98.0)
    l1 = [('A4', 1), ('A4', .5), ('A4', .5), ('A4', 1), ('A4', .5), ('A4', .5), ('D4', 1), ('F4', 1), ('A4', 2)]
    l2 = [('G4', 1), ('G4', .5), ('G4', .5), ('G4', 1), ('G4', .5), ('G4', .5), ('C4', 1), ('E4', 1), ('G4', 2)]
    l4 = [('A4', 1), ('G4', 1), ('E4', 1), ('C4', 1), ('D4', 2), ('D4', 2)]
    melody = l1 + l2 + l1 + l4
    bass_roots = ['D3', 'D3', 'C3', 'C3', 'D3', 'D3', 'A2', 'D3']  # one root per bar (4 beats)
    bpm = 150
    beat = 60.0 / bpm
    total = int(32 * beat * SR)
    out = [0.0] * total
    pos = 0.0
    for note, dur in melody:
        n = int(dur * beat * SR)
        start = int(pos * beat * SR)
        f = N[note]
        for i in range(int(n * 0.9)):
            ph = (i * f / SR) % 1
            env = min(1.0, i / 200) * (1 - i / n) ** 0.5
            if start + i < total:
                out[start + i] += (0.18 if ph < 0.25 else -0.18) * env
        pos += dur
    for bar, root in enumerate(bass_roots):
        f = N[root]
        for half in range(8):  # eighth notes alternating root / fifth
            ff = f * (1.5 if half % 2 else 1.0)
            start = int((bar * 4 + half * 0.5) * beat * SR)
            n = int(0.45 * beat * SR)
            for i in range(n):
                ph = (i * ff / SR) % 1
                v = 4 * abs(ph - 0.5) - 1
                if start + i < total:
                    out[start + i] += v * 0.16 * (1 - i / n)
    return _to_sound(out, 0.6)


def init():
    global _ok, _sounds, _music, _channels
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(SR, -16, 1, 512)
        freq, size, ch = pygame.mixer.get_init()
        if freq != SR or size != -16:
            pygame.mixer.quit()
            pygame.mixer.init(SR, -16, 1, 512)
            freq, size, ch = pygame.mixer.get_init()
        _channels = ch
        _sounds = _build()
        _music = _build_music()
        _ok = True
    except Exception:
        _ok = False


def play(name):
    if _ok and sfx_on and name in _sounds:
        try:
            _sounds[name].play()
        except Exception:
            pass


def start_music():
    if _ok and _music and music_on:
        _music.set_volume(0.35)
        _music.play(loops=-1)


def toggle_music():
    global music_on
    music_on = not music_on
    if not _ok or not _music:
        return
    if music_on:
        start_music()
    else:
        _music.stop()
