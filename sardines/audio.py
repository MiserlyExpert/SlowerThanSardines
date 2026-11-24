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


NOTE_I = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7,
          'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def freq(name):
    if name in ('-', 'R'):
        return 0.0
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE_I[n] + 12 * (o + 1) - 69) / 12)


def _voice(out, notes, bpm, wave, vol, legato=0.9, vibrato=0.0, start=0.0):
    """Render a monophonic line into out (list of floats)."""
    beat = 60.0 / bpm
    pos = start
    total = len(out)
    for name, dur in notes:
        f = freq(name)
        n = int(dur * beat * SR)
        s0 = int(pos * beat * SR)
        if f > 0:
            ln = int(n * legato)
            att = min(300, ln // 4 + 1)
            ph = 0.0
            for i in range(ln):
                j = s0 + i
                if j >= total:
                    break
                ff = f * (1 + vibrato * math.sin(i / SR * 2 * math.pi * 5.5)) if vibrato else f
                ph += ff / SR
                p_ = ph % 1
                if wave == 'square':
                    v = 1.0 if p_ < 0.5 else -1.0
                elif wave == 'pulse':
                    v = 1.0 if p_ < 0.25 else -1.0
                elif wave == 'tri':
                    v = 4 * abs(p_ - 0.5) - 1
                else:
                    v = math.sin(2 * math.pi * p_)
                env = min(1.0, i / att) * (1 - i / ln) ** 0.6
                out[j] += v * env * vol
        pos += dur


def _drums(out, bpm, bars, pattern, vol=0.25, seed=3):
    """pattern: per eighth note, a string of 'k' kick, 's' snare, 'h' hat, '.' rest (8 per bar)."""
    rng = random.Random(seed)
    beat = 60.0 / bpm
    total = len(out)
    for bar in range(bars):
        for i, ch in enumerate(pattern):
            s0 = int((bar * 4 + i * 0.5) * beat * SR)
            if ch == 'k':
                n = int(0.18 * SR)
                ph = 0.0
                for k in range(n):
                    if s0 + k >= total:
                        break
                    f = 110 * (1 - k / n) + 40
                    ph += f / SR
                    out[s0 + k] += math.sin(2 * math.pi * ph) * math.exp(-k / (0.05 * SR)) * vol * 1.6
            elif ch in 'sh':
                n = int((0.12 if ch == 's' else 0.03) * SR)
                y = 0.0
                for k in range(n):
                    if s0 + k >= total:
                        break
                    y += (0.6 if ch == 's' else 0.95) * (rng.uniform(-1, 1) - y)
                    out[s0 + k] += y * math.exp(-k / ((0.04 if ch == 's' else 0.01) * SR)) * vol * (0.9 if ch == 's' else 0.35)


def _bass(roots, bpm, beats_per_bar, style):
    notes = []
    for r in roots:
        lo = r + '2' if r[-1] not in '0123456789' else r
        fifth = {'C': 'G', 'D': 'A', 'E': 'B', 'F': 'C', 'G': 'D', 'A': 'E', 'B': 'F#', 'Bb': 'F'}[r]
        f5 = fifth + ('3' if fifth in ('C', 'D', 'E', 'F', 'F#') and r in ('G', 'A', 'B', 'Bb') else '2')
        if style == 'waltz':
            notes += [(lo, 1), (f5, 1), (r + '3', 1)]
        elif style == 'jig':
            notes += [(lo, 1.5), (f5, 1.5)]
        elif style == 'oompah':
            notes += [(lo, 1), (f5, 1), (lo, 1), (f5, 1)]
        else:  # driving eighths
            notes += [(lo, 0.5)] * 6 + [(f5, 0.5), (lo, 0.5)]
    return notes


def _track(bpm, beats, voices):
    total = int(beats * 60.0 / bpm * SR) + 1
    out = [0.0] * total
    for v in voices:
        if v[0] == 'drums':
            _drums(out, bpm, int(beats // 4), v[1], v[2])
        else:
            notes, wave, vol = v[0], v[1], v[2]
            _voice(out, notes, bpm, wave, vol, *v[3:])
    return out


def _parse(s):
    out = []
    for tok in s.split():
        n, d = tok.split(':')
        out.append((n, float(d)))
    return out


def _build_tracks():
    T = {}
    # Title: 'What Shall We Do With a Drunken Sailor' (traditional, public domain)
    l1 = "A4:1 A4:.5 A4:.5 A4:1 A4:.5 A4:.5 D4:1 F4:1 A4:2"
    l2 = "G4:1 G4:.5 G4:.5 G4:1 G4:.5 G4:.5 C4:1 E4:1 G4:2"
    l4 = "A4:1 G4:1 E4:1 C4:1 D4:2 D4:2"
    mel = _parse(' '.join([l1, l2, l1, l4]))
    T['title'] = _track(150, 32, [(mel, 'pulse', 0.16), (_bass(['D', 'D', 'C', 'C', 'D', 'D', 'A', 'D'], 150, 4, 'oompah'), 'tri', 0.16),
                                  ('drums', 'k.h.s.h.', 0.12)])
    # At sea 1: 'Becalmed', a slow waltz in D dorian (original)
    mel = _parse("A4:2 D5:1 C5:2 A4:1 G4:2 E4:1 F4:3 G4:2 A4:1 C5:2 D5:1 E5:1.5 D5:.5 C5:1 A4:3 "
                 "D5:2 E5:1 F5:2 E5:1 D5:2 C5:1 A4:3 G4:2 F4:1 E4:2 C4:1 D4:3 D4:3")
    T['sea1'] = _track(84, 48, [(mel, 'tri', 0.22, 0.95, 0.004),
                                (_bass(['D', 'F', 'C', 'D', 'C', 'F', 'A', 'D', 'D', 'F', 'G', 'A', 'G', 'C', 'D', 'D'], 84, 3, 'waltz'),
                                 'sine', 0.14)])
    # At sea 2: 'Lantern Jig', 6/8 in G (original)
    mel = _parse("G4:.5 D5:.5 B4:.5 G4:.5 D5:.5 B4:.5 A4:.5 E5:.5 C5:.5 A4:.5 E5:.5 C5:.5 "
                 "B4:.5 D5:.5 G5:.5 F#5:.5 E5:.5 D5:.5 C5:.5 A4:.5 F#4:.5 D4:.5 E4:.5 F#4:.5 "
                 "G4:.5 D5:.5 B4:.5 G4:.5 D5:.5 B4:.5 A4:.5 E5:.5 C5:.5 A4:.5 F#4:.5 A4:.5 "
                 "B4:.5 G5:.5 D5:.5 C5:.5 A4:.5 F#4:.5 G4:1.5 G4:1.5")
    mel = mel + mel
    T['sea2'] = _track(104, 48, [(mel, 'pulse', 0.13, 0.85),
                                 (_bass(['G', 'A', 'G', 'D', 'G', 'A', 'G', 'G'] * 2, 104, 3, 'jig'), 'tri', 0.15)])
    # Port: 'Harbour Lights', accordion-ish oom-pah in F (original)
    mel = _parse("F4:1 A4:1 C5:1 A4:1 Bb4:1 D5:1 C5:2 A4:1 C5:1 F5:1 E5:1 D5:2 C5:2 "
                 "Bb4:1 A4:1 G4:1 A4:1 Bb4:1 C5:1 D5:2 C5:1 A4:1 G4:1 E4:1 F4:4")
    mel = mel + mel
    T['port'] = _track(112, 64, [(mel, 'square', 0.12, 0.92, 0.008),
                                 (_bass(['F', 'Bb', 'F', 'Bb', 'Bb', 'Bb', 'C', 'F'] * 2, 112, 4, 'oompah'), 'tri', 0.16),
                                 ('drums', 'k.h.s.h.', 0.08)])
    # Battle: 'Broadside', D minor with drums (original)
    mel = _parse("D5:.5 D5:.5 F5:1 E5:.5 D5:.5 C5:1 A4:1 C5:1 D5:2 D5:.5 D5:.5 F5:1 G5:.5 F5:.5 E5:1 "
                 "C5:1 E5:1 D5:2 F5:1 E5:.5 D5:.5 C5:1 A4:1 Bb4:1 A4:1 G4:2 A4:.5 Bb4:.5 C5:1 D5:1 F5:1 E5:2 D5:2")
    mel = mel + mel
    roots = ['D', 'D', 'D', 'A', 'F', 'G', 'A', 'D'] * 2
    T['battle'] = _track(140, 64, [(mel, 'square', 0.11, 0.8),
                                   (_bass(roots, 140, 4, 'drive'), 'tri', 0.2),
                                   ('drums', 'k.hsk.sh', 0.16)])
    T['boss'] = _track(158, 64, [(mel, 'pulse', 0.12, 0.75),
                                 ([(n, d) for n, d in _parse(' '.join(f"{n[:-1]}{int(n[-1]) - 1}:{d}" for n, d in mel))], 'square', 0.06, 0.7),
                                 (_bass(roots, 158, 4, 'drive'), 'tri', 0.22),
                                 ('drums', 'kkhskhsh', 0.18)])
    return T


def _build_ambience():
    """A 12-second sea loop: surf rising and falling, plus a breath of wind."""
    rng = random.Random(9)
    n = int(12 * SR)
    out = [0.0] * n
    y1 = y2 = 0.0
    for i in range(n):
        t = i / SR
        swell = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 6.0)) ** 2   # two waves per loop
        y1 += 0.08 * (rng.uniform(-1, 1) - y1)       # low rumble
        y2 += 0.5 * (rng.uniform(-1, 1) - y2)        # hiss
        wind = 0.5 + 0.5 * math.sin(2 * math.pi * t / 12.0 + 1)
        out[i] = y1 * 1.4 * swell + y2 * 0.08 * swell + y2 * 0.03 * wind
    fade = int(0.4 * SR)                             # smooth the loop seam
    for i in range(fade):
        k = i / fade
        out[i] = out[i] * k + out[n - fade + i] * (1 - k)
    return out[:n - fade]


def _gull():
    out = []
    for call in range(2):
        n = int(0.28 * SR)
        ph = 0.0
        for i in range(n):
            k = i / n
            f = 1500 + 700 * math.sin(math.pi * k) - 500 * k + 60 * math.sin(i / SR * 2 * math.pi * 28)
            ph += f / SR
            out.append(math.sin(2 * math.pi * ph) * math.sin(math.pi * k) * 0.5)
        out += [0.0] * int(0.08 * SR)
    return out


def _creak():
    rng = random.Random(5)
    n = int(0.7 * SR)
    out = []
    ph = 0.0
    for i in range(n):
        k = i / n
        f = 70 + 40 * k + 10 * math.sin(k * 30)
        ph += f / SR
        v = (1.0 if (ph % 1) < 0.08 else -0.05) * (0.6 + rng.uniform(-0.2, 0.2))
        out.append(v * math.sin(math.pi * k) * 0.5)
    return out


_tracks = {}
_amb = None
_oneshots = {}
_mood = 'title'
_playing = None
_gap = 0.0
_amb_t = 8.0
_ready = False
PLAYLISTS = {'title': ['title'], 'sea': ['sea1', 'sea2'], 'port': ['port'], 'battle': ['battle'],
             'boss': ['boss'], 'quiet': []}
LOOPING = {'title', 'battle', 'boss'}


def _bg_build():
    global _tracks, _amb, _oneshots, _ready
    try:
        _amb = _to_sound(_build_ambience(), 0.55)
        _oneshots = {'gull': _to_sound(_gull(), 0.25), 'creak': _to_sound(_creak(), 0.35)}
        for name, samples in _build_tracks().items():
            _tracks[name] = _to_sound(samples, 0.7)
        _ready = True
    except Exception:
        _ready = False


def init():
    global _ok, _sounds, _channels
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(SR, -16, 1, 512)
        freq_, size, ch = pygame.mixer.get_init()
        if freq_ != SR or size != -16:
            pygame.mixer.quit()
            pygame.mixer.init(SR, -16, 1, 512)
            freq_, size, ch = pygame.mixer.get_init()
        _channels = ch
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(2)
        _sounds = _build()
        _ok = True
        import threading
        threading.Thread(target=_bg_build, daemon=True).start()
    except Exception:
        _ok = False


def play(name):
    if _ok and sfx_on and name in _sounds:
        try:
            _sounds[name].play()
        except Exception:
            pass


def set_mood(mood):
    """'title', 'sea', 'port', 'battle', 'boss' or 'quiet'. Switching fades the current tune out."""
    global _mood, _playing, _gap
    if mood == _mood:
        return
    _mood = mood
    if _ok:
        try:
            pygame.mixer.Channel(0).fadeout(1500)
        except Exception:
            pass
    _playing = None
    _gap = 1.6 if mood in LOOPING or mood == 'port' else 6.0


def update(dt):
    """Called every frame: runs the playlist (with quiet stretches at sea) and the ocean ambience."""
    global _playing, _gap, _amb_t
    if not _ok or not _ready:
        return
    try:
        amb = pygame.mixer.Channel(1)
        if _mood != 'title' and not amb.get_busy():
            amb.play(_amb, loops=-1, fade_ms=2000)
            amb.set_volume(0.5 if _mood != 'battle' else 0.3)
        elif _mood == 'title' and amb.get_busy():
            amb.fadeout(1000)
        if _mood != 'title':
            _amb_t -= dt
            if _amb_t <= 0:
                _amb_t = random.uniform(7, 18)
                pick = random.choice(['gull', 'gull', 'creak', 'creak'] + (['bell'] if _mood == 'port' else []))
                snd = _oneshots.get(pick) or _sounds.get(pick)
                if snd:
                    snd.set_volume(0.5)
                    snd.play()
        mus = pygame.mixer.Channel(0)
        if not music_on:
            if mus.get_busy():
                mus.fadeout(500)
            return
        if mus.get_busy():
            return
        if _playing is not None and _mood not in LOOPING:
            # a tune just ended: leave a quiet stretch of sea before the next one
            _playing = None
            _gap = random.uniform(25, 50) if _mood == 'sea' else random.uniform(12, 20)
            return
        _gap -= dt
        if _gap > 0:
            return
        names = PLAYLISTS.get(_mood, [])
        if not names:
            return
        name = random.choice(names)
        snd = _tracks.get(name)
        if snd:
            mus.set_volume(0.35)
            mus.play(snd, loops=-1 if _mood in LOOPING else 0, fade_ms=1500)
            _playing = name
    except Exception:
        pass


def start_music():
    set_mood('title')


def toggle_music():
    global music_on
    music_on = not music_on
