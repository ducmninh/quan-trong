"""Audio management and synthesized sound effects + background music."""
import array
import math
import random
import pygame

_TYPE_SOUND: pygame.mixer.Sound | None = None
_FOOT_SOUND: pygame.mixer.Sound | None = None
_ALARM_SOUND: pygame.mixer.Sound | None = None
_WIN_LEVEL_SOUND: pygame.mixer.Sound | None = None
_SHOOT_SOUND: pygame.mixer.Sound | None = None
_STOP_SOUND: pygame.mixer.Sound | None = None
_PICKUP_SOUND: pygame.mixer.Sound | None = None
_HURT_SOUND: pygame.mixer.Sound | None = None
_COIN_SOUND: pygame.mixer.Sound | None = None
_BGM_SOUNDS: list = []  # background music per level
_current_bgm_channel: pygame.mixer.Channel | None = None
_initialized = False


def _make_sound(sample_rate: int, buf: array.array) -> pygame.mixer.Sound | None:
    try:
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


def _generate_bgm(level_idx: int, sample_rate: int = 44100) -> pygame.mixer.Sound | None:
    """Generate a short looping background music track per level."""
    bpm = 100 + level_idx * 15
    beat_dur = 60.0 / bpm
    bars = 4
    beats_per_bar = 4
    total_beats = bars * beats_per_bar
    total_dur = total_beats * beat_dur
    n_samples = int(sample_rate * total_dur)

    # Different musical scales per level for variety
    scales = [
        [261, 293, 329, 349, 392, 440, 493],  # C major (bright)
        [261, 293, 311, 349, 392, 415, 466],  # C minor (mysterious)
        [261, 293, 329, 369, 392, 440, 493],  # C lydian (adventurous)
        [261, 293, 311, 349, 392, 415, 493],  # C harmonic minor (tense)
        [261, 311, 329, 392, 415, 523, 622],  # Pentatonic minor (epic)
    ]
    scale = scales[level_idx % len(scales)]

    buf = array.array('h', [0] * n_samples)
    rng = random.Random(42 + level_idx)

    # Bass line pattern
    bass_notes = [scale[0] // 2, scale[2] // 2, scale[3] // 2, scale[4] // 2]

    for beat in range(total_beats):
        beat_start = int(beat * beat_dur * sample_rate)
        beat_end = min(n_samples, int((beat + 1) * beat_dur * sample_rate))

        # Bass: play on every beat
        bass_freq = bass_notes[beat % len(bass_notes)]
        for i in range(beat_start, beat_end):
            t = (i - beat_start) / sample_rate
            env = max(0, 1.0 - t / beat_dur) * 0.6
            val = math.sin(2 * math.pi * bass_freq * t)
            buf[i] = max(-32000, min(32000, buf[i] + int(3000 * env * val)))

        # Melody: play on every other beat with random notes
        if beat % 2 == 0:
            mel_freq = rng.choice(scale)
            for i in range(beat_start, beat_end):
                t = (i - beat_start) / sample_rate
                env = max(0, 1.0 - t / (beat_dur * 0.8)) * 0.4
                val = math.sin(2 * math.pi * mel_freq * t)
                val += 0.3 * math.sin(2 * math.pi * mel_freq * 2 * t)  # harmonic
                buf[i] = max(-32000, min(32000, buf[i] + int(2000 * env * val)))

        # Hi-hat rhythm (noise) on every beat
        hat_dur = int(0.05 * sample_rate)
        for i in range(beat_start, min(beat_start + hat_dur, beat_end)):
            t = (i - beat_start) / sample_rate
            env = max(0, 1.0 - t / 0.05) * 0.2
            noise = rng.uniform(-1, 1)
            buf[i] = max(-32000, min(32000, buf[i] + int(1500 * env * noise)))

        # Kick drum on beats 0 and 2
        if beat % beats_per_bar in (0, 2):
            kick_dur = int(0.1 * sample_rate)
            for i in range(beat_start, min(beat_start + kick_dur, beat_end)):
                t = (i - beat_start) / sample_rate
                env = max(0, 1.0 - t / 0.1)
                freq_sweep = 150 * (1.0 - t / 0.1) + 40
                val = math.sin(2 * math.pi * freq_sweep * t)
                buf[i] = max(-32000, min(32000, buf[i] + int(4000 * env * val)))

    return _make_sound(sample_rate, buf)


def init() -> None:
    global _TYPE_SOUND, _FOOT_SOUND, _ALARM_SOUND, _WIN_LEVEL_SOUND
    global _SHOOT_SOUND, _STOP_SOUND, _PICKUP_SOUND, _HURT_SOUND
    global _COIN_SOUND, _BGM_SOUNDS, _initialized

    if _initialized:
        return
    _initialized = True

    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=2048)
    except Exception:
        return

    sample_rate = 44100

    try:
        # --- Type click ---
        duration = 0.02
        freq = 1000
        n = int(sample_rate * duration)
        buf = array.array('h', [0] * n)
        for i in range(n):
            env = math.exp(-i * 10 / n)
            noise = math.sin(i * 0.5) * 0.2
            val = math.sin(2 * math.pi * freq * i / sample_rate) + noise
            buf[i] = int(8000 * env * val)
        _TYPE_SOUND = _make_sound(sample_rate, buf)
        if _TYPE_SOUND:
            _TYPE_SOUND.set_volume(0.8)

        # --- Footstep ---
        dur_f = 0.04
        freq_f = 150
        n_f = int(sample_rate * dur_f)
        buf_f = array.array('h', [0] * n_f)
        for i in range(n_f):
            env = math.exp(-i * 20 / n_f)
            buf_f[i] = int(10000 * env * math.sin(2 * math.pi * freq_f * i / sample_rate))
        _FOOT_SOUND = _make_sound(sample_rate, buf_f)
        if _FOOT_SOUND:
            _FOOT_SOUND.set_volume(0.5)

        # --- Alarm ---
        dur_a = 0.5
        n_a = int(sample_rate * dur_a)
        buf_a = array.array('h', [0] * n_a)
        for i in range(n_a):
            f = 800 if (i // 5000) % 2 == 0 else 600
            buf_a[i] = int(8000 * math.sin(2 * math.pi * f * i / sample_rate))
        _ALARM_SOUND = _make_sound(sample_rate, buf_a)
        if _ALARM_SOUND:
            _ALARM_SOUND.set_volume(0.4)

        # --- Win level (arpeggio) ---
        dur_w = 0.6
        n_w = int(sample_rate * dur_w)
        buf_w = array.array('h', [0] * n_w)
        for i in range(n_w):
            notes = [440, 554, 659, 880]
            f = notes[(i // 6000) % 4]
            env = 1.0 - (i / n_w)
            buf_w[i] = int(10000 * env * math.sin(2 * math.pi * f * i / sample_rate))
        _WIN_LEVEL_SOUND = _make_sound(sample_rate, buf_w)
        if _WIN_LEVEL_SOUND:
            _WIN_LEVEL_SOUND.set_volume(0.6)

        # --- Shoot ---
        dur_s = 0.1
        n_s = int(sample_rate * dur_s)
        buf_s = array.array('h', [0] * n_s)
        for i in range(n_s):
            env = math.exp(-i * 15 / n_s)
            val = random.uniform(-1, 1)
            buf_s[i] = int(10000 * env * val)
        _SHOOT_SOUND = _make_sound(sample_rate, buf_s)
        if _SHOOT_SOUND:
            _SHOOT_SOUND.set_volume(0.5)

        # --- Stop time ---
        dur_st = 0.5
        n_st = int(sample_rate * dur_st)
        buf_st = array.array('h', [0] * n_st)
        for i in range(n_st):
            f = 400 * (1.0 - (i / n_st))
            buf_st[i] = int(8000 * math.sin(2 * math.pi * f * i / sample_rate))
        _STOP_SOUND = _make_sound(sample_rate, buf_st)
        if _STOP_SOUND:
            _STOP_SOUND.set_volume(0.6)

        # --- Pickup ---
        dur_p = 0.1
        n_p = int(sample_rate * dur_p)
        buf_p = array.array('h', [0] * n_p)
        for i in range(n_p):
            f_p = 1200
            env = math.exp(-i * 20 / n_p)
            buf_p[i] = int(8000 * env * math.sin(2 * math.pi * f_p * i / sample_rate))
        _PICKUP_SOUND = _make_sound(sample_rate, buf_p)
        if _PICKUP_SOUND:
            _PICKUP_SOUND.set_volume(0.4)

        # --- Hurt ---
        dur_h = 0.15
        n_h = int(sample_rate * dur_h)
        buf_h = array.array('h', [0] * n_h)
        for i in range(n_h):
            env = 1.0 - (i / n_h)
            val = random.uniform(-1, 1)
            buf_h[i] = int(12000 * env * val)
        _HURT_SOUND = _make_sound(sample_rate, buf_h)
        if _HURT_SOUND:
            _HURT_SOUND.set_volume(0.6)

        # --- Coin pickup (higher pitched happy ding) ---
        dur_c = 0.15
        n_c = int(sample_rate * dur_c)
        buf_c = array.array('h', [0] * n_c)
        for i in range(n_c):
            t = i / sample_rate
            env = math.exp(-i * 12 / n_c)
            val = math.sin(2 * math.pi * 1600 * t) + 0.5 * math.sin(2 * math.pi * 2400 * t)
            buf_c[i] = int(6000 * env * val)
        _COIN_SOUND = _make_sound(sample_rate, buf_c)
        if _COIN_SOUND:
            _COIN_SOUND.set_volume(0.5)

        # --- Background music per level ---
        for lvl_idx in range(5):
            bgm = _generate_bgm(lvl_idx, sample_rate)
            if bgm:
                bgm.set_volume(0.25)
            _BGM_SOUNDS.append(bgm)

    except Exception:
        pass


def play_type() -> None:
    if _TYPE_SOUND:
        _TYPE_SOUND.play()


def play_foot() -> None:
    if _FOOT_SOUND:
        _FOOT_SOUND.play()


def play_alarm() -> None:
    if _ALARM_SOUND:
        _ALARM_SOUND.play()


def play_win() -> None:
    if _WIN_LEVEL_SOUND:
        _WIN_LEVEL_SOUND.play()


def play_shoot() -> None:
    if _SHOOT_SOUND:
        _SHOOT_SOUND.play()


def play_stop() -> None:
    if _STOP_SOUND:
        _STOP_SOUND.play()


def play_pickup() -> None:
    if _PICKUP_SOUND:
        _PICKUP_SOUND.play()


def play_hurt() -> None:
    if _HURT_SOUND:
        _HURT_SOUND.play()


def play_coin() -> None:
    if _COIN_SOUND:
        _COIN_SOUND.play()


def play_bgm(level_idx: int) -> None:
    """Start looping background music for the given level."""
    global _current_bgm_channel
    stop_bgm()
    if level_idx < len(_BGM_SOUNDS) and _BGM_SOUNDS[level_idx]:
        try:
            _current_bgm_channel = _BGM_SOUNDS[level_idx].play(loops=-1)
        except Exception:
            pass


def stop_bgm() -> None:
    """Stop any currently playing background music."""
    global _current_bgm_channel
    if _current_bgm_channel:
        try:
            _current_bgm_channel.stop()
        except Exception:
            pass
        _current_bgm_channel = None
