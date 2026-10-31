# -*- coding: utf-8 -*-
"""帧渲染器：按时间 t 画出整幅画面（图 + 文字面板）。"""
import math
from PIL import Image
from draw import Canvas, mix, clamp01, ease, ease_out, F, FONT_SANS
from geom import *
from model import ENT, CAT, LW, DASH, STEPS, build, INTRO_DUR, OUTRO_DUR

W, H = 1920, 1080
SS = 2
SC = 7.4
OX, OY = 1160.0, 560.0
PANEL = (1332, 118, 1888, 1012)
INK = (32, 38, 46)
GREY = (118, 128, 142)
LGREY = (176, 184, 196)
ACC = (206, 92, 58)
BG = (255, 255, 255)
LINE = (228, 233, 240)
BLUE = (32, 106, 204)

SCHED, TOTAL = build()

FADE = {}
ITEM_OF = {}
for _s in SCHED:
    for _it in _s['items']:
        if _it['kind'] == 'fade':
            FADE.setdefault(id(_it['ent']), []).append((_it['rng'], _it['t0'], _it['dur']))
        elif _it['kind'] == 'draw':
            ITEM_OF[id(_it['ent'])] = (_it, _s['idx'])

BOOST = (0.0, 0.0)
for _s in SCHED:
    for _it in _s['items']:
        if _it['kind'] == 'boost':
            BOOST = (_it['t0'], _it['dur'])


# ------------------------------------------------------------------ 工具
def in_ang(a, r0, r1):
    if abs(r1-r0) >= 359.99:
        return True
    a = a % 360.0
    r0m, r1m = r0 % 360.0, r1 % 360.0
    if abs(r1m-r0m) < 1e-9:
        return False
    if r0m <= r1m:
        return r0m <= a <= r1m
    return a >= r0m or a <= r1m


def _alpha_arc(ent, a, t):
    for r, t0, d in FADE.get(id(ent), []):
        if 'a0' in r and in_ang(a, r['a0'], r['a1']):
            return 1.0 - ease(clamp01((t-t0)/d))
    return 1.0


def split_arc(a0, a1, ent, t):
    if not FADE.get(id(ent)):
        return [(a0, a1, 1.0)]
    n = max(16, int(abs(a1-a0)/0.4))
    out, start, prev = [], a0, _alpha_arc(ent, a0, t)
    for i in range(1, n+1):
        a = a0 + (a1-a0)*i/n
        al = _alpha_arc(ent, a, t)
        if abs(al-prev) > 1e-6:
            out.append((start, a, prev))
            start, prev = a, al
    out.append((start, a1, prev))
    return [o for o in out if abs(o[1]-o[0]) > 1e-9]


def split_line(p1, p2, ent, t):
    lst = FADE.get(id(ent), [])
    if not lst:
        return [(p1, p2, 1.0)]
    cuts, info = {0.0, 1.0}, []
    for r, t0, d in lst:
        if 'u0' not in r:
            continue
        u0, u1 = max(0.0, r['u0']), min(1.0, r['u1'])
        info.append((u0, u1, 1.0 - ease(clamp01((t-t0)/d))))
        cuts.update([u0, u1])
    cuts = sorted(cuts)
    out = []
    for i in range(len(cuts)-1):
        u0, u1 = cuts[i], cuts[i+1]
        if u1-u0 < 1e-6:
            continue
        um = (u0+u1)/2
        al = 1.0
        for a0, a1, aa in info:
            if a0 <= um <= a1:
                al = aa
                break
        q1 = (p1[0]+(p2[0]-p1[0])*u0, p1[1]+(p2[1]-p1[1])*u0)
        q2 = (p1[0]+(p2[0]-p1[0])*u1, p1[1]+(p2[1]-p1[1])*u1)
        out.append((q1, q2, al))
    return out


def boost_at(t):
    t0, d = BOOST
    return ease(clamp01((t-t0)/d))


def ent_color(cat, outline, boost):
    c = CAT[cat]
    if outline:
        return mix(c, CAT['final'], boost)
    if boost > 0:
        return mix(c, (208, 215, 224), boost*0.5)
    return c


def ent_width(cat, outline, boost):
    w = LW[cat]
    if outline:
        w = w + (LW['final']-w)*boost
    return w


# ------------------------------------------------------------------ 图元
def draw_point(cv, e, color, p):
    if p <= 0:
        return
    s = ease_out(min(1.0, p*1.7))
    q = e['p']
    if e.get('tan'):
        cv.ring(q, 1.15*s, color, 0.7)
        cv.dot(q, 0.42*s, color)
        return
    cv.cross(q, 2.4*s, color, 0.8)
    cv.dot(q, 0.5*s, color)
    if e.get('label') and p > 0.30:
        a = clamp01((p-0.30)/0.5)
        lp = (q[0]+e['lp'][0], q[1]+e['lp'][1])
        anc = 'lm' if e['lp'][0] > 0 else ('rm' if e['lp'][0] < 0 else 'mm')
        cv.text(lp, e['label'], 3.7*SC, mix(BG, color, a), anchor=anc, bold=True,
                halo=BG if a < 0.98 else None)


def draw_dim(cv, e, color, p, tsize=None):
    tsize = tsize or 3.6*SC
    if p <= 0:
        return
    k = e['dkind']
    if k == 'lin':
        p1, p2, off = e['p1'], e['p2'], e.get('off', 0.0)
        d = norm(sub(p2, p1))
        nrm = perp(d)
        q1 = add(p1, nrm, off)
        q2 = add(p2, nrm, off)
        Ln = dist(q1, q2)
        small = Ln < 7.0
        pe = clamp01(p/0.30)
        for a, b in ((p1, q1), (p2, q2)):
            if dist(a, b) < 1e-6:
                continue
            u = norm(sub(b, a))
            aa = add(a, u, 0.6)
            bb = add(b, u, 1.4)
            cv.polyline([aa, add(aa, sub(bb, aa), ease_out(pe))], color, 0.42)
        if p < 0.30:
            return
        pl = clamp01((p-0.30)/0.32)
        mid = mul(add(q1, q2), 0.5)
        if small:
            a1 = add(q1, d, -2.4)
            a2 = add(q2, d, 2.4)
            k = ease_out(pl)
            cv.polyline([add(mid, sub(a1, mid), k), add(mid, sub(a2, mid), k)], color, 0.42)
        else:
            k = ease_out(pl)
            cv.polyline([add(mid, sub(q1, mid), k), add(mid, sub(q2, mid), k)], color, 0.42)
        if p < 0.62:
            return
        pa = clamp01((p-0.62)/0.16)
        ang1 = math.degrees(math.atan2(d[1], d[0]))
        if pa > 0:
            if small:
                cv.arrow(q1, ang1 + 180.0, 2.4*pa, color)
                cv.arrow(q2, ang1, 2.4*pa, color)
            else:
                cv.arrow(q1, ang1, 2.4*pa, color)
                cv.arrow(q2, ang1 + 180.0, 2.4*pa, color)
        if p < 0.78:
            return
        pt = clamp01((p-0.78)/0.22)
        angd = math.degrees(math.atan2(d[1], d[0]))
        rot = -angd
        if rot > 90:
            rot -= 180
        if rot < -90:
            rot += 180
        if 'toff' in e:
            tpos = add(mid, e['toff'])
        else:
            tpos = add(mid, nrm, (2.2 if off >= 0 else -2.2) if not small else 3.0)
        col = mix(BG, color, ease_out(pt))
        if abs(rot) < 1:
            cv.text(tpos, e['text'], tsize, col, anchor='mm', halo=BG)
        else:
            cv.text_rot(tpos, e['text'], tsize, col, rot=0.0, halo=BG)
    elif k == 'rad':
        c, a, r, lead = e['c'], e['a'], e['r'], e.get('lead', 7.0)
        tip = cv.arc_pt(c, r, a)
        dv = (math.cos(rad(a)), math.sin(rad(a)))
        p1 = clamp01(p/0.55)
        s = add(c, dv, 1.0)
        cv.polyline([s, add(s, sub(tip, s), ease_out(p1))], color, 0.42)
        if p > 0.5:
            cv.arrow(tip, a, 2.4*clamp01((p-0.5)/0.18), color)
        if p > 0.68:
            pt = clamp01((p-0.68)/0.32)
            tp = add(tip, dv, lead*0.5+2.4)
            rot = -a
            while rot > 90:
                rot -= 180
            while rot < -90:
                rot += 180
            col = mix(BG, color, ease_out(pt))
            if abs(rot) < 1:
                cv.text(tp, e['text'], tsize, col, anchor='mm', halo=BG)
            else:
                cv.text_rot(tp, e['text'], tsize, col, rot=0.0, halo=BG)
    elif k == 'ang':
        v, a0, a1, r = e['v'], e['a0'], e['a1'], e['r']
        pa = clamp01(p/0.58)
        cv.arc(v, r, a0, a0+(a1-a0)*ease_out(pa), color, 0.42)
        if p > 0.58:
            pk = clamp01((p-0.58)/0.16)
            for aa, sgn in ((a0, -1), (a1, 1)):
                tp = cv.arc_pt(v, r, aa)
                cv.arrow(tp, aa + 90*sgn + 180.0, 2.3*pk, color)
        if p > 0.74:
            pt = clamp01((p-0.74)/0.26)
            am = (a0+a1)/2.0
            tp = e.get('tpos') or cv.arc_pt(v, r+4.6, am)
            cv.text(tp, e['text'], tsize, mix(BG, color, ease_out(pt)), anchor='mm', halo=BG)


def draw_entities(cv, t, cur_step):
    boost = boost_at(t)
    for e in ENT:
        st = e['step']
        if st > cur_step:
            continue
        item = ITEM_OF.get(id(e))
        if st == cur_step and item is not None:
            it, _ = item
            p = clamp01((t-it['t0'])/it['dur'])
        else:
            p = 1.0
        if p <= 0:
            continue
        col = ent_color(e['cat'], e.get('outline'), boost)
        w = ent_width(e['cat'], e.get('outline'), boost)
        anim = (p < 1.0 and st == cur_step and item is not None)
        if e['kind'] == 'L':
            if anim:
                q = (e['p1'][0]+(e['p2'][0]-e['p1'][0])*p, e['p1'][1]+(e['p2'][1]-e['p1'][1])*p)
                cv.polyline([e['p1'], q], col, w, e['dash'])
                if p < 0.995:
                    cv.glow(q, 1.5, col, 0.35)
            else:
                for q1, q2, al in split_line(e['p1'], e['p2'], e, t):
                    if al <= 0.012:
                        continue
                    cv.polyline([q1, q2], mix(BG, col, al), w, e['dash'])
        elif e['kind'] == 'A':
            if anim:
                a_end = e['a0'] + (e['a1']-e['a0'])*p
                cv.arc(e['c'], e['r'], e['a0'], a_end, col, w, e['dash'])
                tip = cv.arc_pt(e['c'], e['r'], a_end)
                cv.polyline([e['c'], tip], mix(col, BG, 0.25), max(0.38, w*0.5))
                angt = math.degrees(math.atan2(tip[1]-e['c'][1], tip[0]-e['c'][0]))
                cv.arrow(tip, angt + 180.0, 2.5, col)
                cv.cross(e['c'], 1.3, mix(col, BG, 0.35), 0.42)
                cv.glow(tip, 1.7, col, 0.38)
            else:
                for s0, s1, al in split_arc(e['a0'], e['a1'], e, t):
                    if al <= 0.012:
                        continue
                    cv.arc(e['c'], e['r'], s0, s1, mix(BG, col, al), w, e['dash'])
        elif e['kind'] == 'P':
            draw_point(cv, e, col, p)
        elif e['kind'] == 'DIM':
            draw_dim(cv, e, col, p)


# ------------------------------------------------------------------ 版式
def draw_sheet(cv):
    cv.d.rectangle([0, 0, W*SS, H*SS], fill=BG)
    # 图框（双线）
    cv.rect_px(26, 112, 1310, 1006, outline=(176, 186, 198), w=1.6)
    cv.rect_px(33, 119, 1303, 999, outline=(206, 214, 224), w=0.8)
    cv.d.rectangle([0, 0, W*SS, 104*SS], fill=(248, 250, 253))
    cv.d.line([(0, 104*SS), (W*SS, 104*SS)], fill=LINE, width=2*SS)
    for gx in range(-150, 40, 10):
        px = OX + gx*SC
        if 40 < px < 1300:
            cv.d.line([(px*SS, 126*SS), (px*SS, 1004*SS)], fill=(246, 249, 252), width=SS)
    for gy in range(-46, 46, 10):
        py = OY - gy*SC
        if 126 < py < 1004:
            cv.d.line([(40*SS, py*SS), (1300*SS, py*SS)], fill=(246, 249, 252), width=SS)


def draw_header(cv, step, t):
    cv.text_px(46, 16, '扳手 · 尺规作图分步图解', 25, INK, bold=True)
    cv.text_px(46, 56, '双头开口扳手  ·  15 步  ·  每一步给出圆心位置、半径与尺寸线', 14.2, GREY)
    cv.text_px(1876, 16, '制图：DeepSeek XH', 13.5, GREY, anchor='ra')
    cv.text_px(1876, 40, '来自 414', 13.5, GREY, anchor='ra')
    if step is None:
        return
    cv.text_px(1876, 66, '第 %d 步 / 共 %d 步' % (step, len(STEPS)), 14.0, ACC, anchor='ra')
    n = len(STEPS)
    for k in range(n):
        cx = 1876 - (n-1-k)*12.5
        fill = ACC if k+1 <= step else (255, 255, 255)
        outl = ACC if k+1 <= step else (206, 214, 224)
        cv.d.ellipse([(cx-3.2)*SS, (95-3.2)*SS, (cx+3.2)*SS, (95+3.2)*SS],
                     fill=fill, outline=outl, width=SS)


NOSTART = '。，、；：）」』】！？%”’·'


def wrap(cv, s, size, maxw):
    f = F(FONT_SANS, size*SS)
    out, line = [], ''
    for ch in s:
        if ch == '\n':
            out.append(line); line = ''; continue
        tst = line+ch
        if f.getlength(tst)/SS > maxw and line and ch not in NOSTART:
            out.append(line); line = ch
        else:
            line = tst
    if line:
        out.append(line)
    return out


def block(cv, x, y, wd, lines, size=15.5, color=INK, lh=1.62, bullet=None, gap=0.34):
    yy = y
    for s in lines:
        for k, ln in enumerate(wrap(cv, s, size, wd-(16 if bullet else 0))):
            if bullet and k == 0:
                cv.text_px(x, yy, bullet, size, ACC, bold=True)
            cv.text_px(x+(16 if bullet else 0), yy, ln, size, color)
            yy += size*lh
        yy += size*gap
    return yy


def draw_panel(cv, step, t):
    x0, y0, x1, y1 = PANEL
    cv.rect_px(x0, y0, x1, y1, fill=(252, 253, 255), outline=LINE, w=1.2, radius=10)
    if step is None:
        return
    meta = STEPS[step-1]
    x = x0+26
    wd = (x1-x0)-52
    cv.text_px(x, y0+12, '%02d' % step, 38, ACC, bold=True)
    cv.text_px(x+64, y0+18, meta['name'], 19.5, INK, bold=True)
    cv.text_px(x+64, y0+48, '第 %d 步 / 共 %d 步' % (step, len(STEPS)), 12.0, LGREY)
    cv.d.line([(x*SS, (y0+74)*SS), ((x1-26)*SS, (y0+74)*SS)], fill=LINE, width=2*SS)
    y = y0+88
    cv.text_px(x, y, '本 步 操 作', 13.0, ACC, bold=True)
    cv.d.line([(x*SS, (y+20)*SS), ((x+50)*SS, (y+20)*SS)], fill=ACC, width=2*SS)
    y = block(cv, x, y+32, wd, meta['bullets'], 14.0, INK, 1.62, bullet='·')
    yb = max(y+12, y0+256)
    cv.d.line([(x*SS, (yb-8)*SS), ((x1-26)*SS, (yb-8)*SS)], fill=LINE, width=2*SS)
    cv.text_px(x, yb+6, '作 图 要 点', 13.0, BLUE, bold=True)
    block(cv, x, yb+34, wd, meta['notes'], 13.2, (62, 72, 86), 1.58)
    # 图例
    yl = y0+428
    cv.d.line([(x*SS, yl*SS), ((x1-26)*SS, yl*SS)], fill=LINE, width=2*SS)
    cv.text_px(x, yl+10, '图 例', 12.0, GREY, bold=True)
    items = [('axis', '基准线（细点画线）'), ('known', '已知线段'), ('mid', '中间线段'),
             ('conn', '连接线段'), ('aux', '作图辅助线')]
    for k, (c, txt) in enumerate(items):
        yy = yl+36+k*21
        p1 = ((x-OX)/SC, (OY-yy)/SC)
        p2 = ((x+34-OX)/SC, (OY-yy)/SC)
        if c == 'axis':
            cv.polyline([p1, p2], CAT[c], 1.0, DASH['axis'])
        elif c == 'aux':
            cv.polyline([p1, p2], CAT[c], 0.9, DASH['aux'])
        else:
            cv.polyline([p1, p2], CAT[c], 1.9)
        cv.text_px(x+44, yy-7.5, txt, 11.8, (72, 82, 94))
    # 进度
    yp = y0+572
    cv.d.line([(x*SS, yp*SS), ((x1-26)*SS, yp*SS)], fill=LINE, width=2*SS)
    cv.text_px(x, yp+8, '进 度', 12.0, GREY, bold=True)
    for k, st in enumerate(STEPS):
        yy = yp+32+k*18.4
        cur = (k+1 == step)
        done = (k+1 < step)
        if cur:
            cv.rect_px(x-8, yy-3, x1-18, yy+15, fill=(253, 240, 232), radius=4)
        col = ACC if cur else ((110, 122, 138) if done else (186, 193, 203))
        cv.text_px(x, yy, '%02d' % (k+1), 10.2, col, bold=cur)
        cv.text_px(x+25, yy, st['short'], 11.2,
                   (44, 52, 62) if (cur or done) else (158, 166, 176), bold=cur)


# ------------------------------------------------------------------ 场景
def draw_main(cv, t):
    draw_sheet(cv)
    cur = 1
    for s in SCHED:
        if t >= s['t0']:
            cur = s['idx']
    draw_entities(cv, t, cur)
    draw_header(cv, cur, t)
    draw_panel(cv, cur, t)
    s = SCHED[cur-1]
    dt = t - s['t0']
    if dt < 1.5:
        a = ease(clamp01(dt/0.45)) * (1.0 - ease(clamp01((dt-0.95)/0.5)))
        if a > 0.01:
            txt = 'STEP %02d   %s' % (cur, s['meta']['name'])
            f = F(FONT_SANS, 16*SS)
            tw = f.getlength(txt)/SS
            cv.rect_px(50, 106, 50+tw+26, 142, fill=(255, 255, 255), radius=6)
            cv.text_px(62, 112, txt, 16, mix(BG, ACC, a), bold=True)


def draw_final_figure(cv, t, alpha=1.0):
    for e in ENT:
        if not e.get('outline'):
            continue
        col = mix(BG, CAT['final'], alpha)
        w = LW['final']
        if e['kind'] == 'L':
            for q1, q2, al in split_line(e['p1'], e['p2'], e, 1e9):
                cv.polyline([q1, q2], col, w)
        else:
            for s0, s1, al in split_arc(e['a0'], e['a1'], e, 1e9):
                cv.arc(e['c'], e['r'], s0, s1, col, w)


def draw_intro(cv, t):
    cv.d.rectangle([0, 0, W*SS, H*SS], fill=BG)
    cv.d.rectangle([0, 0, W*SS, 8*SS], fill=ACC)
    a1 = ease(clamp01(t/0.9))
    cv.text_px(120, 96, '扳 手', 66, mix(BG, INK, a1), bold=True)
    a2 = ease(clamp01((t-0.4)/0.9))
    cv.text_px(124, 196, '双头开口扳手 · 尺规作图 15 步', 25, mix(BG, (70, 80, 94), a2))
    a3 = ease(clamp01((t-0.9)/0.9))
    cv.text_px(124, 240, '从基准线开始，每一步给出圆心位置、半径、尺寸线与尺寸界线', 15.2,
               mix(BG, GREY, a3))
    cv.text_px(124, 268, '圆弧全部由“半径尺寸线”绕圆心转动扫出 —— 每条线只画一次', 15.2,
               mix(BG, GREY, a3))
    a4 = ease(clamp01((t-1.6)/1.0))
    col = mix(BG, INK, a4)
    cv.text_px(124, 330, '尺 寸 分 析', 14.5, mix(BG, ACC, a4), bold=True)
    cv.d.line([(124*SS, 352*SS), (600*SS, 352*SS)], fill=mix(BG, ACC, a4), width=2*SS)
    rows = ['120  两开口中心距', '74  槽长（两端半圆圆心距）', '12 / 14  开口宽度',
            'R14 / R18  两端头外圆', 'R8 / R14  开口底圆弧', 'R16  左端头开口侧外弧',
            'R4 / R5  槽端半圆', 'R5  过渡圆角（4 处）', '1.5  手柄壁厚', '4 / 6  开口底圆心距']
    yy = 372
    for r in rows:
        cv.text_px(124, yy, r, 14.8, col)
        yy += 28
    cv.text_px(660, 330, '线 段 分 析', 14.5, mix(BG, ACC, a4), bold=True)
    cv.d.line([(660*SS, 352*SS), (1180*SS, 352*SS)], fill=mix(BG, ACC, a4), width=2*SS)
    seg = [('已知线段', '两端头外圆 R14 / R18、15° 开口方向线', BLUE),
           ('中间线段', '开口底弧 R8 / R14、R16 外弧、开口两侧面', (14, 140, 88)),
           ('连接线段', '手柄槽 R4 / R5 与两侧边、R5 过渡圆角', (206, 122, 16))]
    yy = 372
    for nm, ds, c in seg:
        cv.text_px(660, yy, nm, 15.0, mix(BG, c, a4), bold=True)
        cv.text_px(660, yy+24, ds, 13.8, col)
        yy += 62
    cv.text_px(660, yy+2, '顺序：基准线 → 已知 → 中间 → 连接 → 修剪 → 描深', 13.4,
               mix(BG, GREY, a4))
    cv.text_px(1240, 330, '作 图 提 示', 14.5, mix(BG, ACC, a4), bold=True)
    cv.d.line([(1240*SS, 352*SS), (1800*SS, 352*SS)], fill=mix(BG, ACC, a4), width=2*SS)
    tips = ['· 圆心位置一律从基准线量起', '· 半径相加求圆角圆心', '· 尺寸界线垂直被测线段',
            '· 多余线段用“擦”不用“重画”']
    yy = 372
    for s in tips:
        cv.text_px(1240, yy, s, 13.8, col)
        yy += 28
    # 图形预览
    pa = ease(clamp01((t-2.6)/2.4))
    if pa > 0:
        cv.set_mm(1342.0, 862.0, 6.0)
        draw_final_figure(cv, t, alpha=pa*0.92)
        cv.set_mm(OX, OY, SC)
    cv.text_px(1876, 1044, '制图：DeepSeek XH    ·    来自 414', 12.5, mix(BG, GREY, a4),
               anchor='ra')


def draw_outro(cv, t):
    cv.d.rectangle([0, 0, W*SS, H*SS], fill=BG)
    draw_sheet(cv)
    cv.set_mm(OX, OY, SC)
    draw_final_figure(cv, t, alpha=1.0)
    for e in ENT:
        if e['kind'] == 'DIM':
            draw_dim(cv, e, (96, 104, 118), 1.0)
    draw_header(cv, None, t)
    a = ease(clamp01(t/1.2))
    cv.text_px(1360, 146, '作 图 完 成', 30, mix(BG, ACC, a), bold=True)
    cv.text_px(1360, 196, '15 步 · 全部由尺规作出 · 每条线只画一次', 14.5, mix(BG, GREY, a))
    items = ['01 基准线与 120', '02 右端头 R14', '03 左端头 R18', '04 15° 方向线',
             '05 开口底圆心 4 / 6', '06 开口底弧 R8 / R14', '07 开口两侧面 12 / 14',
             '08 R16 外弧', '09 槽端圆心 74', '10 槽与两侧边', '11 手柄两侧 1.5',
             '12 R5 圆角（右）', '13 R5 圆角（左）', '14 修剪', '15 描深']
    yy = 244
    for i, s in enumerate(items):
        aa = ease(clamp01((t-0.5-i*0.10)/0.5))
        cv.text_px(1360, yy, s, 13.0, mix(BG, (70, 80, 94), aa))
        yy += 23
    cv.text_px(1360, 640, '核对：120、74、12、14、4、6、1.5、15°', 13.0, mix(BG, GREY, a))
    cv.text_px(1360, 664, 'R14、R18、R16、R8、R14、R5', 13.0, mix(BG, GREY, a))
    cv.text_px(1876, 1044, '制图：DeepSeek XH    ·    来自 414', 12.5, mix(BG, GREY, a),
               anchor='ra')


def render(t):
    cv = Canvas(W, H, ss=SS)
    cv.set_mm(OX, OY, SC)
    if t < INTRO_DUR:
        draw_intro(cv, t)
    elif t >= TOTAL - OUTRO_DUR:
        draw_outro(cv, t - (TOTAL - OUTRO_DUR))
    else:
        draw_main(cv, t)
    return cv.image()


def render_step_end(i):
    s = SCHED[i-1]
    return render(s['t_end'] - 0.4)
