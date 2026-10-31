# -*- coding: utf-8 -*-
"""扳手（双头开口扳手）几何模型。

全部由标注尺寸 + 相切条件解出，单位 mm，原点 O1 = 右端头中心，X 向右，Y 向上。
标注尺寸（来自图样）：
    120  两开口中心距（水平基准方向）
    74   手柄槽长（两端半圆圆心距）
    12/14 两开口宽度      R14/R18 两端头外圆
    R8/R14 两开口底圆弧   R16 左端头开口侧外弧（与 R14 同心）
    4/6  开口底圆心距端头中心（沿 15° 方向线）
    1.5  手柄壁厚         R4/R5 槽两端半圆
    R5   端头与手柄的过渡圆角（共 4 处）   15° 开口方向
"""
import math

def rad(d): return math.radians(d)
def ang(c, p): return math.degrees(math.atan2(p[1]-c[1], p[0]-c[0])) % 360.0
def add(p, q, k=1.0): return (p[0]+q[0]*k, p[1]+q[1]*k)
def sub(p, q): return (p[0]-q[0], p[1]-q[1])
def mul(p, k): return (p[0]*k, p[1]*k)
def norm(p):
    L = math.hypot(p[0], p[1]); return (p[0]/L, p[1]/L)
def dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def perp(p): return (-p[1], p[0])

# ------------------------------------------------------------------ 尺寸
L_CC   = 120.0     # 两中心距
R_H1   = 14.0      # 右端头外圆
R_H2   = 18.0      # 左端头外圆
R_B2   = 16.0      # 左端头开口侧外弧（与开口底同心）
R_J1   = 8.0       # 右开口底
R_J2   = 14.0      # 左开口底（图样标注）
R_J2D  = 7.0       # 左开口底实际作图半径（开口宽的一半，与两侧面相切）
W1     = 12.0      # 右开口宽
W2     = 14.0      # 左开口宽
A1     = 4.0       # 右开口底圆心距 O1
A2     = -6.0      # 左开口底弧圆心：在 O2 后方 6mm（图上“6”）
ALPHA  = 15.0      # 开口方向与轴线夹角
RF     = 5.0       # 过渡圆角
SLOT_L = 74.0      # 槽长（两端半圆圆心距）
RS1    = 4.0       # 槽右端半圆
RS2    = 5.0       # 槽左端半圆
WALL   = 1.5       # 壁厚

# ------------------------------------------------------------------ 基准
O1 = (0.0, 0.0)
O2 = (-L_CC, 0.0)
U1 = (math.cos(rad(ALPHA)),  math.sin(rad(ALPHA)))      # 右开口方向
U2 = (-math.cos(rad(ALPHA)), -math.sin(rad(ALPHA)))     # 左开口方向
N  = (-math.sin(rad(ALPHA)), math.cos(rad(ALPHA)))      # 开口方向线的法向

C1 = add(O1, U1, A1)
C2 = add(O2, U2, A2)

# ------------------------------------------------------------------ 右开口（宽 12，底 R8）
H1 = W1/2.0
# 开口侧面与开口底弧 R8 的交点（弦宽 12，弧半径 8 → 半角 asin(6/8)）
_u1 = math.sqrt(R_J1**2 - H1**2)
T1A = add(add(C1, N,  H1), U1, -_u1)
T1B = add(add(C1, N, -H1), U1, -_u1)
_t1 = math.sqrt(R_H1**2 - H1**2) - A1
P1A = add(add(C1, N, H1), U1, _t1)
P1B = add(add(C1, N, -H1), U1, _t1)

# ------------------------------------------------------------------ 左开口（宽 14，底 R14）
H2 = W2/2.0
_u2 = math.sqrt(R_J2D**2 - H2**2)
T2A = add(add(C2, N,  H2), U2, -_u2)
T2B = add(add(C2, N, -H2), U2, -_u2)
_t2 = math.sqrt(R_B2**2 - H2**2)
P2A = add(add(C2, N, H2), U2, _t2)
P2B = add(add(C2, N, -H2), U2, _t2)

# ------------------------------------------------------------------ R18 与 R16 交点
_d  = dist(O2, C2)
_a  = (_d**2 + R_H2**2 - R_B2**2) / (2*_d)
_h  = math.sqrt(max(R_H2**2 - _a**2, 0.0))
_foot = add(O2, U2, _a)
Q1 = add(_foot, N,  _h)
Q2 = add(_foot, N, -_h)

# ------------------------------------------------------------------ 手柄槽
S1 = (-L_CC/2 + SLOT_L/2, 0.0)
S2 = (-L_CC/2 - SLOT_L/2, 0.0)
_sl = (RS2-RS1)/(S1[0]-S2[0])
NS = (0.0, 1.0)      # 槽/手柄一律与轴线平行（不再有 0.77° 倾斜）
K1A = add(S1, NS,  RS1)
K2A = add(S2, NS,  RS2)
K1B = add(S1, NS, -RS1)
K2B = add(S2, NS, -RS2)
G1A = add(S1, NS,  RS1+WALL)
G2A = add(S2, NS,  RS2+WALL)
G1B = add(S1, NS, -(RS1+WALL))
G2B = add(S2, NS, -(RS2+WALL))
C_TOP = RS1 + WALL
C_BOT = -(RS1 + WALL)

# ------------------------------------------------------------------ 过渡圆角 R5（4 处）
def _fillet_center(O, R, side):
    cc = (C_TOP if side > 0 else C_BOT) + side * RF
    D = perp(NS)
    if side < 0:
        D = mul(D, -1)
    v = sub(mul(NS, cc), O)
    b = 2 * (v[0]*D[0] + v[1]*D[1])
    c = v[0]**2 + v[1]**2 - (R+RF)**2
    disc = b*b - 4*c
    if disc < 0:
        return None
    s1 = (-b + math.sqrt(disc))/2.0
    s2 = (-b - math.sqrt(disc))/2.0
    cands = [add(mul(NS, cc), D, s1), add(mul(NS, cc), D, s2)]
    cands.sort(key=lambda p: abs(p[0] - (-L_CC/2)))
    return cands[0]

F1A = _fillet_center(O1, R_H1, +1)
F1B = _fillet_center(O1, R_H1, -1)
F2A = _fillet_center(O2, R_H2, +1)
F2B = _fillet_center(O2, R_H2, -1)

def _tan_on_circle(O, R, F):
    return add(O, norm(sub(F, O)), R)

T_F1A = _tan_on_circle(O1, R_H1, F1A)
T_F1B = _tan_on_circle(O1, R_H1, F1B)
T_F2A = _tan_on_circle(O2, R_H2, F2A)
T_F2B = _tan_on_circle(O2, R_H2, F2B)

def _tan_on_line(F, NS, c):
    k = NS[0]*F[0] + NS[1]*F[1]
    return sub(F, mul(NS, k - c))

T_L1A = _tan_on_line(F1A, NS, C_TOP)
T_L1B = _tan_on_line(F1B, NS, C_BOT)
T_L2A = _tan_on_line(F2A, NS, C_TOP)
T_L2B = _tan_on_line(F2B, NS, C_BOT)


# ------------------------------------------------------------------ R18 与 R16 之间的 R5 过渡圆角
def _cc(c1, r1, c2, r2, pick_upper=True):
    d = dist(c1, c2)
    a = (d*d + r1*r1 - r2*r2) / (2*d)
    h = math.sqrt(max(r1*r1 - a*a, 0.0))
    f = add(c1, norm(sub(c2, c1)), a)
    n = perp(norm(sub(c2, c1)))
    p1 = add(f, n, h); p2 = add(f, n, -h)
    if pick_upper:
        return p1 if p1[1] > p2[1] else p2
    return p2 if p1[1] > p2[1] else p1

FB1 = _cc(O2, R_H2-RF, C2, R_B2-RF, True)     # 上侧过渡圆心
FB2 = _cc(O2, R_H2-RF, C2, R_B2-RF, False)    # 下侧过渡圆心
TB1A = add(O2, norm(sub(FB1, O2)), R_H2)      # 与 R18 的切点（上）
TB1B = add(C2, norm(sub(FB1, C2)), R_B2)      # 与 R16 的切点（上）
TB2A = add(O2, norm(sub(FB2, O2)), R_H2)      # 与 R18 的切点（下）
TB2B = add(C2, norm(sub(FB2, C2)), R_B2)      # 与 R16 的切点（下）

def sweep(a0, a1, ccw=True):
    d = (a1 - a0) % 360.0
    return d if ccw else d - 360.0

if __name__ == '__main__':
    for n, v in [('O1', O1), ('O2', O2), ('C1', C1), ('C2', C2),
                 ('P1A', P1A), ('P1B', P1B), ('P2A', P2A), ('P2B', P2B),
                 ('Q1', Q1), ('Q2', Q2), ('S1', S1), ('S2', S2),
                 ('NS', NS), ('C_TOP', C_TOP), ('C_BOT', C_BOT),
                 ('F1A', F1A), ('F1B', F1B), ('F2A', F2A), ('F2B', F2B),
                 ('T_F1A', T_F1A), ('T_F2A', T_F2A),
                 ('T_L1A', T_L1A), ('T_L2A', T_L2A)]:
        print('%-6s' % n, '(%.3f, %.3f)' % v)
    print('len', P1A[0] - (O2[0] - R_H2))

# ---------------- 3 方案：R16 弧与开口下侧面相交，交点即羊角 ----------------
_dir16 = norm(add(mul(U2, 1.0), mul(N, -0.55)))     # 左下方向
C16 = add(O2, _dir16, R_H2 - R_B2)                   # 距 O2 = R18-R16 = 2

def _circ_line_pts(c, r, n, cc):
    d = cc - (n[0]*c[0] + n[1]*c[1])
    h = math.sqrt(max(r*r - d*d, 0.0))
    f = add(c, n, d); q = perp(n)
    return [add(f, q, h), add(f, q, -h)]

# 下侧面所在直线：n·x = N·C2 - H2
_c_face = N[0]*C2[0] + N[1]*C2[1] - H2
_Hc = _circ_line_pts(C16, R_B2, N, _c_face)
HORN = max(_Hc, key=lambda p: dist(p, O2))           # 外侧那个交点
P2B = HORN

# R5 圆角：距 C16 = 16+5，且在手柄下侧线外移 5 的线上
_Fc = _circ_line_pts(C16, R_B2 + RF, NS, C_BOT - RF)
F16 = max(_Fc, key=lambda p: p[0])
T16A = add(C16, norm(sub(F16, C16)), R_B2)
T16B = _tan_on_line(F16, NS, C_BOT)
