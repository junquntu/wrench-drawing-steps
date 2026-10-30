# -*- coding: utf-8 -*-
"""超采样画布：mm 坐标 → 像素，支持虚线、圆弧、箭头、旋转文字、透明混色。"""
import math, os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_CAND = [
    os.environ.get('FONT_CJK', ''),
    os.path.join(_HERE, '..', 'assets', 'NotoSansCJKsc-Regular.otf'),
    os.path.join(_HERE, '..', 'assets', 'NotoSansCJKsc-Bold.otf'),
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
]
FONT_SANS = next((p for p in _CAND if p and os.path.exists(p)), _CAND[1])
FONT_BOLD = FONT_SANS
_fc = {}

def F(path, size):
    k = (path, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

def mix(c, bg, t):
    """c 向 bg 混合 t（t=0 → c，t=1 → bg）"""
    t = max(0.0, min(1.0, t))
    return tuple(int(c[i]*(1-t) + bg[i]*t) for i in range(3))

def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)

def ease(x):
    """smoothstep"""
    x = clamp01(x)
    return x*x*(3-2*x)

def ease_out(x):
    x = clamp01(x)
    return 1 - (1-x)**3

def ease_in(x):
    x = clamp01(x)
    return x**3


class Canvas:
    def __init__(self, w, h, ss=2, bg=(255, 255, 255)):
        self.W, self.H, self.SS, self.bg = w, h, ss, bg
        self.img = Image.new('RGB', (w*ss, h*ss), bg)
        self.d = ImageDraw.Draw(self.img)
        self.ox, self.oy, self.sc = 0.0, 0.0, 1.0

    # ---------------- 坐标
    def set_mm(self, ox, oy, sc):
        self.ox, self.oy, self.sc = ox, oy, sc

    def P(self, p):
        return ((self.ox + p[0]*self.sc)*self.SS, (self.oy - p[1]*self.sc)*self.SS)

    # ---------------- 基础
    def _seg(self, a, b, color, w):
        self.d.line([a, b], fill=color, width=max(1, int(round(w*self.SS))))

    def polyline(self, pts, color, w=1.0, dash=None):
        if len(pts) < 2:
            return
        P = [self.P(p) for p in pts]
        if dash is None:
            for i in range(len(P)-1):
                self._seg(P[i], P[i+1], color, w)
            if w*self.SS >= 3 and len(P) <= 24:      # 圆头，避免折线拐角缺口
                r = w*self.SS/2.0
                for q in P[1:-1]:
                    self.d.ellipse([q[0]-r, q[1]-r, q[0]+r, q[1]+r], fill=color)
            return
        pat = [x*self.SS for x in dash]
        idx, rem, on = 0, pat[0], True
        for i in range(len(P)-1):
            a, b = P[i], P[i+1]
            L = math.hypot(b[0]-a[0], b[1]-a[1])
            if L == 0:
                continue
            t = 0.0
            while t < L - 1e-9:
                step = min(rem, L-t)
                if on:
                    p0 = (a[0]+(b[0]-a[0])*t/L, a[1]+(b[1]-a[1])*t/L)
                    p1 = (a[0]+(b[0]-a[0])*(t+step)/L, a[1]+(b[1]-a[1])*(t+step)/L)
                    self._seg(p0, p1, color, w)
                t += step
                rem -= step
                if rem <= 1e-9:
                    idx = (idx+1) % len(pat)
                    rem = pat[idx]
                    on = not on

    def arc(self, c, r, a0, a1, color, w=1.0, dash=None, seg=2.0):
        """角度制，逆时针为正；由 a0 → a1（方向随增量符号）"""
        n = max(6, int(abs(a1-a0)/seg)+1)
        pts = []
        for i in range(n+1):
            a = math.radians(a0 + (a1-a0)*i/n)
            pts.append((c[0]+r*math.cos(a), c[1]+r*math.sin(a)))
        self.polyline(pts, color, w, dash)

    def arc_pt(self, c, r, a):
        a = math.radians(a)
        return (c[0]+r*math.cos(a), c[1]+r*math.sin(a))

    def dot(self, p, r, color):
        x, y = self.P(p)
        r *= self.SS
        self.d.ellipse([x-r, y-r, x+r, y+r], fill=color)

    def ring(self, p, r, color, w=1.0):
        x, y = self.P(p)
        r *= self.SS
        self.d.ellipse([x-r, y-r, x+r, y+r], outline=color, width=max(1, int(w*self.SS)))

    def glow(self, p, r, color, alpha=0.35):
        """软光点（用同心圆逼近）"""
        for k in range(6):
            f = (k+1)/6.0
            self.dot(p, r*f, mix(color, self.bg, 1-alpha*f*f))

    def cross(self, p, r, color, w=0.9):
        x, y = self.P(p)
        r *= self.SS
        self.d.line([(x-r, y), (x+r, y)], fill=color, width=max(1, int(w*self.SS)))
        self.d.line([(x, y-r), (x, y+r)], fill=color, width=max(1, int(w*self.SS)))

    def arrow(self, tip, ang_deg, size=2.6, color=(0, 0, 0)):
        a = math.radians(ang_deg)
        L, Wd = size, size*0.30
        bx, by = tip[0]-L*math.cos(a), tip[1]-L*math.sin(a)
        p1 = (bx + Wd*math.sin(a), by - Wd*math.cos(a))
        p2 = (bx - Wd*math.sin(a), by + Wd*math.cos(a))
        self.d.polygon([self.P(tip), self.P(p1), self.P(p2)], fill=color)

    # ---------------- 文字
    def text(self, p, s, size, color=(0, 0, 0), anchor='lm', bold=False, halo=None):
        x, y = self.P(p)
        f = F(FONT_SANS, size*self.SS)
        if halo is not None:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                self.d.text((x+dx*self.SS, y+dy*self.SS), s, font=f, fill=halo, anchor=anchor)
        if bold:
            for dx, dy in ((0, 0), (0.6, 0), (0, 0.6), (0.6, 0.6)):
                self.d.text((x+dx*self.SS, y+dy*self.SS), s, font=f, fill=color, anchor=anchor)
        else:
            self.d.text((x, y), s, font=f, fill=color, anchor=anchor)

    def text_px(self, x, y, s, size, color=(0, 0, 0), anchor='la', bold=False):
        f = F(FONT_SANS, size*self.SS)
        if bold:
            for dx, dy in ((0, 0), (0.6, 0), (0, 0.6), (0.6, 0.6)):
                self.d.text(((x+dx)*self.SS, (y+dy)*self.SS), s, font=f, fill=color, anchor=anchor)
        else:
            self.d.text((x*self.SS, y*self.SS), s, font=f, fill=color, anchor=anchor)

    def text_rot(self, p, s, size, color, rot=90, halo=None):
        """绕自身中心旋转（rot 为屏幕角度，顺时针为正）"""
        f = F(FONT_SANS, size*self.SS)
        bb = f.getbbox(s)
        tw, th = max(bb[2]-bb[0], 1), max(bb[3]-bb[1], 1)
        mask = Image.new('L', (int(tw)+20, int(th)+20), 0)
        md = ImageDraw.Draw(mask)
        md.text((10-bb[0], 10-bb[1]), s, font=f, fill=255)
        mask = mask.rotate(-rot, expand=True)
        x, y = self.P(p)
        if halo is not None:
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                self.img.paste(halo, (int(x-mask.width/2+dx*self.SS), int(y-mask.height/2+dy*self.SS)), mask)
        layer = Image.new('RGB', mask.size, color)
        self.img.paste(layer, (int(x-mask.width/2), int(y-mask.height/2)), mask)

    def rect_px(self, x0, y0, x1, y1, fill=None, outline=None, w=1.0, radius=0):
        box = [x0*self.SS, y0*self.SS, x1*self.SS, y1*self.SS]
        self.d.rounded_rectangle(box, radius=radius*self.SS, fill=fill,
                                 outline=outline, width=max(1, int(w*self.SS)))

    def save(self, path):
        out = self.img.resize((self.W, self.H), Image.LANCZOS)
        out.save(path)
        return out

    def image(self):
        return self.img.resize((self.W, self.H), Image.LANCZOS)
