# -*- coding: utf-8 -*-
"""程序化配乐 / 音效：全部用 numpy 合成，与画面时间轴同步。

声音层次：
  1) 底噪垫：缓慢和弦（很轻）
  2) 每步切换：柔和铃音
  3) 画线：铅笔摩擦（噪声包络）
  4) 画弧：起笔/收笔"圆规"轻响 + 划弧时的轻微摩擦
  5) 尺寸数字出现：轻"嗒"
"""
import math, wave
import numpy as np

SR = 44100


def _env(n, a=0.15, r=0.4):
    """余弦包络"""
    t = np.linspace(0, 1, n)
    e = np.ones(n)
    na = max(1, int(n*a))
    nr = max(1, int(n*r))
    e[:na] = 0.5 - 0.5*np.cos(np.pi*np.arange(na)/na)
    e[-nr:] *= 0.5 + 0.5*np.cos(np.pi*np.arange(nr)/nr)
    return e


def bell(dur=1.6, f=880.0, amp=0.16):
    n = int(dur*SR)
    t = np.arange(n)/SR
    w = (np.sin(2*np.pi*f*t)*0.6 + np.sin(2*np.pi*f*1.5*t)*0.22 +
         np.sin(2*np.pi*f*2.0*t)*0.12)
    e = np.exp(-t*3.2)
    return amp*w*e


def tick(amp=0.09, f=1500.0):
    n = int(0.05*SR)
    t = np.arange(n)/SR
    rs = np.random.RandomState(7)
    noise = rs.randn(n)*np.exp(-t*900)
    return amp*(0.55*noise + 0.45*np.sin(2*np.pi*f*t)*np.exp(-t*160))


def stroke(dur=0.4, amp=0.05):
    n = max(64, int(dur*SR))
    rs = np.random.RandomState(3)
    noise = rs.randn(n)
    k = 24
    noise = np.convolve(noise, np.ones(k)/k, mode='same')
    e = _env(n, 0.25, 0.5)
    return amp*noise*e*3.0


def pad(total, amp=0.085):
    n = int(total*SR)
    out = np.zeros(n)
    chords = [(110.0, 164.81, 220.0), (98.0, 146.83, 196.0),
              (87.31, 130.81, 174.61), (82.41, 123.47, 164.81),
              (110.0, 164.81, 220.0)]
    seg = total/len(chords)
    for i, ch in enumerate(chords):
        s = int(i*seg*SR)
        e = int(min(n, (i+1)*seg*SR))
        m = e-s
        if m <= 0:
            continue
        t = np.arange(m)/SR
        env = _env(m, 0.35, 0.35)
        w = np.zeros(m)
        for f in ch:
            w += np.sin(2*np.pi*f*t)*0.5 + np.sin(2*np.pi*f*2*t)*0.12
        out[s:e] += amp*w*env
    # 轻微呼吸
    t = np.arange(n)/SR
    out *= (0.85 + 0.15*np.sin(2*np.pi*0.07*t))
    return out


def build(sched, total, path, preview=False):
    n = int(total*SR)
    L = np.zeros(n)
    R = np.zeros(n)
    L += pad(total)

    def put(sig, t0, pan=0.0):
        s = int(t0*SR)
        if s < 0 or s >= n:
            return
        m = min(len(sig), n-s)
        L[s:s+m] += sig[:m]*(1.0-max(0.0, pan)*0.5)
        R[s:s+m] += sig[:m]*(1.0+min(0.0, pan)*0.5)

    # 步骤切换铃音 + 各图元音效
    for si, st in enumerate(sched):
        put(bell(1.8, 784.0 if si % 2 == 0 else 880.0, 0.13), st['t0'], -0.2)
        for it in st['items']:
            if it['kind'] == 'draw':
                e = it['ent']
                if e['kind'] == 'A':
                    put(tick(0.075, 1400.0), it['t0'], -0.3)
                    put(stroke(it['dur']*0.9, 0.028), it['t0'], -0.3)
                    put(tick(0.055, 1800.0), it['t0']+it['dur'], 0.3)
                elif e['kind'] == 'L':
                    put(stroke(it['dur']*0.95, 0.032), it['t0'], -0.15)
                elif e['kind'] == 'DIM':
                    put(tick(0.05, 2200.0), it['t0']+it['dur']*0.80, 0.35)
                elif e['kind'] == 'P':
                    put(tick(0.04, 2600.0), it['t0'], 0.2)
            elif it['kind'] == 'fade':
                put(stroke(0.5, 0.016), it['t0'], 0.1)
            elif it['kind'] == 'boost':
                put(bell(3.0, 523.25, 0.10), it['t0'], 0.0)
                put(bell(3.2, 659.25, 0.08), it['t0']+0.25, 0.25)
                put(bell(3.6, 783.99, 0.07), it['t0']+0.5, -0.25)
    # 片头 / 片尾
    put(bell(3.0, 440.0, 0.10), 0.4, 0.0)
    put(bell(3.4, 554.37, 0.08), 1.2, -0.2)
    put(bell(4.0, 659.25, 0.09), total-8.0, 0.0)
    put(bell(4.4, 880.0, 0.08), total-6.6, 0.2)

    mix = np.stack([L, R], axis=1)
    peak = np.abs(mix).max()
    if peak > 0:
        mix = mix/peak*0.86
    # 首尾淡入淡出
    f = int(1.2*SR)
    mix[:f] *= np.linspace(0, 1, f)[:, None]
    mix[-f:] *= np.linspace(1, 0, f)[:, None]
    data = (mix*32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path
