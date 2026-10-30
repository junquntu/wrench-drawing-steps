# -*- coding: utf-8 -*-
"""构建入口：静帧 + 总览 + 配乐 + 视频。

用法：
    python wrench/build.py --full       全片（默认）
    python wrench/build.py --preview    只出静帧 + 24 秒样片（快速自检）
"""
import os
import sys
import time
import subprocess

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import model
import render
import audio
from render import SCHED, TOTAL, W, H
from draw import FONT_SANS, F

OUT = os.path.join(ROOT, 'docs')
os.makedirs(OUT, exist_ok=True)
FPS = 30


def log(*a):
    print(*a, flush=True)


def stills():
    files = []
    for i in range(1, len(model.STEPS) + 1):
        t0 = time.time()
        img = render.render_step_end(i)
        p = os.path.join(OUT, 'step%02d.png' % i)
        img.save(p)
        files.append(p)
        log('  still %02d  %-16s %.2fs' % (i, model.STEPS[i-1]['short'], time.time()-t0))
    return files


def contact_sheet(files):
    cols, rows = 3, 5
    tw, th, gap = 600, 338, 22
    Wc = cols*tw + (cols+1)*gap
    Hc = rows*th + (rows+1)*gap + 104
    sheet = Image.new('RGB', (Wc, Hc), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, Wc, 96], fill=(248, 250, 253))
    d.text((34, 20), '扳手 · 尺规作图 15 步总览', font=F(FONT_SANS, 30), fill=(32, 38, 46))
    d.text((34, 60), '双头开口扳手  |  基准线 → 已知 → 中间 → 连接 → 修剪 → 描深  |  制图：DeepSeek XH / 来自 414',
           font=F(FONT_SANS, 13), fill=(120, 128, 142))
    for k, p in enumerate(files):
        r, c = divmod(k, cols)
        x = gap + c*(tw+gap)
        y = 104 + gap + r*(th+gap)
        im = Image.open(p).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x+tw, y+th], outline=(216, 222, 232), width=2)
    out = os.path.join(OUT, '总览-15步.png')
    sheet.save(out)
    log('  contact sheet ->', out)
    return out


def make_audio():
    p = os.path.join(OUT, 'wrench.wav')
    t0 = time.time()
    audio.build(SCHED, TOTAL, p)
    log('  audio %.1fs -> %s' % (time.time()-t0, p))
    return p


def video(path, wav, t0, t1, fps=FPS):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(round((t1-t0)*fps))
    cmd = [exe, '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-r', str(fps), '-i', '-',
           '-ss', '%.3f' % t0, '-i', wav, '-t', '%.3f' % (t1-t0),
           '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
           '-shortest', '-movflags', '+faststart', '-nostats', '-loglevel', 'warning', path]
    log('  ffmpeg frames=%d  %s' % (n, os.path.basename(path)))
    # stderr 写文件而不是 PIPE：否则 ffmpeg 的进度输出会塞满管道，导致互相等待（死锁）
    logpath = path + '.fflog'
    logf = open(logpath, 'wb')
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=logf)
    t_start = time.time()
    try:
        for i in range(n):
            img = render.render(t0 + i/float(fps))
            p.stdin.write(img.tobytes())
            if i % 150 == 0:
                el = time.time()-t_start
                eta = el/max(1, i+1)*(n-i-1)
                log('    frame %5d/%d   %.1fs   eta %.1f min' % (i, n, el, eta/60))
    finally:
        try:
            p.stdin.close()
        except Exception:
            pass
        err = p.stderr.read().decode('utf-8', 'ignore')
        p.wait()
    if p.returncode != 0:
        try:
            log(open(logpath, encoding='utf-8', errors='ignore').read()[-3000:])
        except OSError:
            pass
        raise SystemExit('ffmpeg failed')
    try:
        os.remove(logpath)
    except OSError:
        pass
    log('  video ok  %.1fs  %.1f MB' % (time.time()-t_start,
                                       os.path.getsize(path)/1e6))


def main():
    preview = '--preview' in sys.argv
    t_all = time.time()
    log('== build  mode=%s  total=%.1fs  frames=%d' % ('preview' if preview else 'full',
                                                       TOTAL, int(TOTAL*FPS)))
    files = stills()
    contact_sheet(files)
    wav = make_audio()
    if preview:
        video(os.path.join(OUT, 'preview.mp4'), wav, 6.0, 30.0)
        render.render(4.0).save(os.path.join(OUT, 'poster.png'))
    else:
        video(os.path.join(OUT, '扳手-尺规作图.mp4'), wav, 0.0, TOTAL)
        render.render(TOTAL - 3.0).save(os.path.join(OUT, 'poster.png'))
    try:
        os.remove(wav)
    except OSError:
        pass
    log('== done  %.1f min' % ((time.time()-t_all)/60))


if __name__ == '__main__':
    main()
