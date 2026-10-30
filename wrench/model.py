# -*- coding: utf-8 -*-
"""作图实体 + 时间轴。

原则：
  · 每条线 / 每段弧只画一次（不重复描画）；多余部分在"修剪"一步淡出；
  · 圆弧一律由"半径尺寸线"绕圆心转动扫出；
  · 求圆心的辅助弧、平移辅助线单独成步，逐条出现。
"""
import math
from geom import *

# ------------------------------------------------------------------ 颜色与线宽
CAT = {
    'axis':  (198, 60, 58),
    'aux':   (146, 160, 178),
    'known': (32, 106, 204),
    'mid':   (14, 140, 88),
    'conn':  (206, 122, 16),
    'dim':   (58, 68, 84),
    'pt':    (206, 64, 48),
    'final': (28, 30, 34),
}
LW = {'axis': 0.55, 'aux': 0.5, 'known': 0.95, 'mid': 0.95, 'conn': 0.95,
      'dim': 0.5, 'pt': 0.8, 'final': 2.6}
DASH = {'axis': [11, 2.4, 1.2, 2.4], 'aux': [3.0, 2.2]}

ENT = []


def L(step, cat, p1, p2, outline=False, erase=None, dash=None):
    e = dict(kind='L', step=step, cat=cat, p1=p1, p2=p2, outline=outline, erase=erase,
             dash=dash if dash is not None else DASH.get(cat))
    ENT.append(e); return e


def A(step, cat, c, r, a0, a1, outline=False, erase=None, dash=None):
    e = dict(kind='A', step=step, cat=cat, c=c, r=r, a0=a0, a1=a1, outline=outline,
             erase=erase, dash=dash if dash is not None else DASH.get(cat))
    ENT.append(e); return e


def P(step, p, label=None, lp=(0, 0), cat='pt', tan=False):
    ENT.append(dict(kind='P', step=step, cat=cat, p=p, label=label, lp=lp, tan=tan))
    return ENT[-1]


def DIM(step, dkind, **kw):
    e = dict(kind='DIM', step=step, cat='dim', dkind=dkind)
    e.update(kw)
    ENT.append(e); return e


# ------------------------------------------------------------------ 手柄边线工具
DH = (NS[1], -NS[0])                      # 手柄边线方向（+x）


def hpt(side, t):
    """手柄边线上参数 t 处的点（side=+1 上边线，-1 下边线）"""
    return add(mul(NS, C_TOP if side > 0 else C_BOT), DH, t)


def hparam(side, p):
    return (p[0] - (C_TOP if side > 0 else C_BOT)*NS[0]) * DH[0] + \
           (p[1] - (C_TOP if side > 0 else C_BOT)*NS[1]) * DH[1]


# ================================================================== 1 基准线
L(1, 'axis', (-160, 0), (28, 0))
L(1, 'axis', (0, -26), (0, 30))
L(1, 'axis', (-120, -26), (-120, 30))
P(1, O1, 'O1', (2.4, 3.6))
P(1, O2, 'O2', (-2.4, 3.6))
DIM(1, 'lin', p1=(0, 0), p2=(-120, 0), off=-36.0, text='120')

# ================================================================== 2 R14
A(2, 'known', O1, R_H1, 0.0, 360.0, outline=True,
  erase=[dict(step=14, a0=ang(O1, P1B), a1=ang(O1, P1A) + 360.0),
         dict(step=14, a0=ang(O1, T_F1A), a1=ang(O1, T_F1B))])
DIM(2, 'rad', c=O1, a=128.0, r=R_H1, text='R14', lead=8.0)

# ================================================================== 3 R18
A(3, 'known', O2, R_H2, 0.0, 360.0, outline=True,
  erase=[dict(step=14, a0=ang(O2, TB1A), a1=ang(O2, TB2A)),
         dict(step=14, a0=ang(O2, T_F2B), a1=ang(O2, T_F2A))])
DIM(3, 'rad', c=O2, a=112.0, r=R_H2, text='R18', lead=8.0)

# ================================================================== 4 15° 方向线
L(4, 'axis', add(O1, U1, -19.0), add(O1, U1, 26.0))
L(4, 'axis', add(O2, U2, -19.0), add(O2, U2, 26.0))
DIM(4, 'ang', v=O1, a0=0.0, a1=ALPHA, r=17.0, text='15°', tpos=(16.5, -5.5))
DIM(4, 'ang', v=O2, a0=180.0, a1=180.0 + ALPHA, r=17.0, text='15°', tpos=(-138.0, -13.0))

# ================================================================== 5 C1 C2
DIM(5, 'lin', p1=O1, p2=C1, off=7.0, text='4')
P(5, C1, 'C1', (2.6, -4.6))
DIM(5, 'lin', p1=O2, p2=C2, off=7.0, text='6')
P(5, C2, 'C2', (3.0, -4.0))

# ================================================================== 6 开口底圆弧
A(6, 'mid', C1, R_J1, ang(C1, T1A), ang(C1, T1B), outline=True)
DIM(6, 'rad', c=C1, a=214.0, r=R_J1, text='R8', lead=8.0)
A(6, 'mid', C2, R_J2D, ang(C2, T2A), ang(C2, T2B) + (360.0 if ang(C2, T2B) < ang(C2, T2A) else 0.0), outline=True)
DIM(6, 'rad', c=C2, a=160.0, r=R_J2D, text='R14', lead=9.0)

# ================================================================== 7 开口两侧面
L(7, 'mid', T1A, P1A, outline=True)
L(7, 'mid', T1B, P1B, outline=True)
L(7, 'mid', T2A, P2A, outline=True)
L(7, 'mid', T2B, P2B, outline=True)
DIM(7, 'lin', p1=add(P1A, U1, 3.0), p2=add(P1B, U1, 3.0), off=0.0, text='12')
DIM(7, 'lin', p1=add(P2A, U2, 3.0), p2=add(P2B, U2, 3.0), off=0.0, text='14')

# ================================================================== 8 R16 外弧
A(8, 'mid', C2, R_B2, ang(C2, TB1B), ang(C2, P2A), outline=True)
A(8, 'mid', C2, R_B2, ang(C2, P2B), ang(C2, TB2B), outline=True)
P(8, Q1, tan=True)
P(8, Q2, tan=True)
A(8, 'conn', FB1, RF, ang(FB1, TB1A), ang(FB1, TB1B), outline=True)
A(8, 'conn', FB2, RF, ang(FB2, TB2A), ang(FB2, TB2B), outline=True)
DIM(8, 'rad', c=C2, a=250.0, r=R_B2, text='R16', lead=7.0)

# ================================================================== 9 槽端圆心
L(9, 'aux', (-60, -17), (-60, 17))
DIM(9, 'lin', p1=S1, p2=S2, off=26.0, text='74')
P(9, S1, 'S1', (0.0, -3.4))
P(9, S2, 'S2', (0.0, -3.4))

# ================================================================== 10 槽端半圆 + 侧边
A(10, 'conn', S1, RS1, 90.0, -90.0, outline=True)
A(10, 'conn', S2, RS2, 90.0, 270.0, outline=True)
L(10, 'conn', K1A, K2A, outline=True)
L(10, 'conn', K1B, K2B, outline=True)

# ================================================================== 11 手柄两侧
_tA0, _tA1 = -106.0, -11.0
_LA = L(11, 'conn', hpt(+1, _tA0), hpt(+1, _tA1), outline=True,
        erase=[dict(step=14, u0=0.0, u1=(hparam(+1, T_L2A) - _tA0)/(_tA1 - _tA0)),
               dict(step=14, u0=(hparam(+1, T_L1A) - _tA0)/(_tA1 - _tA0), u1=1.0)])
_LB = L(11, 'conn', hpt(-1, _tA0), hpt(-1, _tA1), outline=True,
        erase=[dict(step=14, u0=0.0, u1=(hparam(-1, T_L2B) - _tA0)/(_tA1 - _tA0)),
               dict(step=14, u0=(hparam(-1, T_L1B) - _tA0)/(_tA1 - _tA0), u1=1.0)])
DIM(11, 'lin', p1=hpt(+1, -40.0), p2=add(hpt(+1, -40.0), NS, WALL), off=0.0, text='1.5', toff=(0.0, 6.2))

# ================================================================== 12 R5 圆角（右）
A(12, 'aux', O1, R_H1 + RF, ang(O1, F1A) - 26.0, ang(O1, F1A) + 12.0)
L(12, 'aux', hpt(+1, -34.0), hpt(+1, -6.0), erase=dict(step=14, u0=0.0, u1=1.0),
  dash=None)
# 上面这条是"平移 5 的辅助线"，单独再画一条（真正用到的一段）
ENT.pop()
_aux12 = L(12, 'aux', add(hpt(+1, -34.0), NS, RF), add(hpt(+1, -6.0), NS, RF),
           erase=dict(step=14, u0=0.0, u1=1.0))
P(12, F1A, 'F1', (0.0, 3.2))
A(12, 'conn', F1A, RF, ang(F1A, T_F1A), ang(F1A, T_L1A), outline=True)
A(12, 'aux', O1, R_H1 + RF, ang(O1, F1B) - 12.0, ang(O1, F1B) + 26.0)
_aux12b = L(12, 'aux', add(hpt(-1, -34.0), NS, -RF), add(hpt(-1, -6.0), NS, -RF),
            erase=dict(step=14, u0=0.0, u1=1.0))
P(12, F1B, 'F2', (0.0, -3.6))
A(12, 'conn', F1B, RF, ang(F1B, T_F1B), ang(F1B, T_L1B), outline=True)

# ================================================================== 13 R5 圆角（左）
A(13, 'aux', O2, R_H2 + RF, ang(O2, F2A) - 26.0, ang(O2, F2A) + 12.0)
_aux13 = L(13, 'aux', add(hpt(+1, -114.0), NS, RF), add(hpt(+1, -86.0), NS, RF),
           erase=dict(step=14, u0=0.0, u1=1.0))
P(13, F2A, 'F3', (0.0, 3.2))
A(13, 'conn', F2A, RF, ang(F2A, T_F2A), ang(F2A, T_L2A), outline=True)
A(13, 'aux', O2, R_H2 + RF, ang(O2, F2B) - 12.0, ang(O2, F2B) + 26.0)
_aux13b = L(13, 'aux', add(hpt(-1, -114.0), NS, -RF), add(hpt(-1, -86.0), NS, -RF),
            erase=dict(step=14, u0=0.0, u1=1.0))
P(13, F2B, 'F4', (0.0, -3.6))
A(13, 'conn', F2B, RF, ang(F2B, T_F2B), ang(F2B, T_L2B), outline=True)

# 12/13 步的两条平移辅助线只用于求圆心，修剪时擦掉
_aux12['erase'] = dict(step=14, u0=0.0, u1=1.0)
_aux12b['erase'] = dict(step=14, u0=0.0, u1=1.0)
_aux13['erase'] = dict(step=14, u0=0.0, u1=1.0)
_aux13b['erase'] = dict(step=14, u0=0.0, u1=1.0)

# 求圆心的辅助弧同样在修剪时擦掉
for _e in ENT:
    if _e['kind'] == 'A' and _e['cat'] == 'aux' and _e['step'] in (12, 13):
        _e['erase'] = dict(step=14, u0=0.0, u1=1.0)
# 第 9 步的槽对称中心线保留（细点画线）

# ================================================================== 14 修剪（淡出）
# 只处理"擦除"，实体本身在第 14 步不新增

# ================================================================== 15 描深（全局加粗）

# ------------------------------------------------------------------ 步骤文字
STEPS = [
 dict(name='画基准线', short='基准线', bullets=[
     '画水平基准线（扳手对称轴），两端各超出轮廓 5～8mm。',
     '在轴线上定 O1；自 O1 沿轴线量 120 得 O2，作两条竖直基准线。',
     '两条竖线就是两端头圆心，也是全部尺寸的起算线。',
   ], notes=[
     '基准线用细点画线，线型 长—短—短。',
     '120 是两开口的中心距，从 O1 一次量到 O2，不要分段量。']),
 dict(name='右端头外圆 R14', short='R14 外圆', bullets=[
     '针尖插 O1，张开 14mm，画 R14 整圆。',
     '先画整圆；开口处多余的一段，留到修剪时擦掉。',
     '半径尺寸自圆心引出，箭头指在圆周上。',
   ], notes=['圆心＝两条基准线交点，半径＝R14，直接用尺量取。']),
 dict(name='左端头外圆 R18', short='R18 外圆', bullets=[
     '针尖插 O2，张开 18mm，画 R18 整圆。',
     '两端头一大一小：右 R14、左 R18，不要画反。',
     'R18 是左端头主轮廓，后面 R16 弧要与它相交。',
   ], notes=['同一张图上两个端头半径不同，量半径前先看清是哪一端。']),
 dict(name='画 15° 开口方向线', short='15° 方向线', bullets=[
     '过 O1 作与轴线成 15° 的方向线（细点画线）。',
     '过 O2 同样作 15°，方向相反，两端对称。',
     '用圆弧尺寸线标出 15°，箭头指在轴线与方向线上。',
   ], notes=['方向线是开口的对称中心：开口两侧面、开口底圆心都在它上面或与它对称。']),
 dict(name='定开口底圆心 C1、C2', short='开口底圆心', bullets=[
     '自 O1 沿方向线量 4mm 得 C1（右开口底圆心）。',
     '自 O2 沿方向线量 6mm 得 C2（左开口底圆心）。',
     '尺寸 4、6 的尺寸线与方向线平行，尺寸界线垂直于方向线。',
   ], notes=['两个圆心都落在各自的方向线上，尺寸从端头中心量起，不从外圆量。']),
 dict(name='画开口底圆弧 R8、R14', short='开口底 R8/R14', bullets=[
     '针尖插 C1，张开 8mm，画 R8 弧（约 180°，从一侧划到另一侧）。',
     '针尖插 C2，张开 14mm，画 R14 弧（同样约 180°）。',
     '只画需要的一段，不画整圆。',
   ], notes=['这两段弧就是开口的“底”，后面两侧面必须与它相切。']),
 dict(name='作开口两侧面', short='开口两侧面', bullets=[
     '过 R8 弧两端点作方向线的平行线，两线相距 12（右开口）。',
     '过 R14 弧两端点作平行线，相距 14（左开口）。',
     '四条线与端头外圆的交点，就是开口的两个“角点”。',
   ], notes=['两侧面与开口底弧相切，切点就是量宽度的起点；尺寸 12、14 标在两线之间。']),
 dict(name='左端头 R16 外弧与 R5 过渡', short='R16 外弧', bullets=[
     '针尖仍插 C2，张开 16mm，画 R16 弧（与 R14 同心）。',
     'R16 与 R14 同心 ⇒ 开口后壁厚 2mm，处处相等。',
     'R16 与 R18 两弧相交，交点附近用 R5 圆角过渡：圆心距 O2 为 18-5=13、距 C2 为 16-5=11。',
     '针尖插该交点，张开 5mm，自上弧切点划到下弧切点。',
   ], notes=['R16 的来历：先定开口底 R14，再“加壁厚”得到外轮廓 R16；两弧用 R5 收口，轮廓才顺。']),
 dict(name='定手柄槽两端圆心', short='槽端圆心', bullets=[
     '在 O1O2 的中点作竖直细线，作为槽的对称中心。',
     '自对称中心向两侧各量 37，得槽端圆心 S1、S2（总长 74）。',
     '尺寸 74 是两端半圆的圆心距，不是槽的总长。',
   ], notes=['74 的两条尺寸界线分别过 S1、S2，垂直于轴线。']),
 dict(name='画槽端半圆与两侧边', short='槽与侧边', bullets=[
     '针尖插 S1，张开 4mm，画右端半圆 R4。',
     '针尖插 S2，张开 5mm，画左端半圆 R5。',
     '作两半圆的两条外公切线，就是槽的两侧边。',
   ], notes=['R4≠R5 ⇒ 槽是锥形：右端宽 8、左端宽 10，两侧边不平行于轴线。']),
 dict(name='画手柄两侧（壁厚 1.5）', short='手柄两侧', bullets=[
     '把槽的两侧边向外平移 1.5mm，得手柄的两条外缘线。',
     '尺寸 1.5 的箭头指在槽边线与手柄边线之间。',
     '壁厚处处相等 1.5，所以手柄也是锥形。',
   ], notes=['先有槽、后有线：手柄边线是槽边线的等距线，不能随手画。']),
 dict(name='R5 过渡圆角（右端头）', short='R5 圆角·右', bullets=[
     '求圆心：以 O1 为圆心 R=14+5=19 画辅助弧。',
     '手柄边线向外平移 5 画辅助线，与辅助弧的交点即 F1。',
     '针尖插 F1，张开 5mm，自外圆切点划到手柄边线切点。',
     '下侧同样处理，得 F2。',
   ], notes=['圆角同时与端头外圆、手柄边线相切 ⇒ 圆心＝两“等距线”的交点（半径相加）。']),
 dict(name='R5 过渡圆角（左端头）', short='R5 圆角·左', bullets=[
     '以 O2 为圆心 R=18+5=23 画辅助弧。',
     '平移 5 的辅助线与它相交，得 F3。',
     '针尖插 F3，张开 5mm 划弧；下侧同理得 F4。',
   ], notes=['左端头外圆大，辅助半径是 23，别沿用右端的 19。']),
 dict(name='修剪多余图线', short='修剪', bullets=[
     '擦掉 R14 圆在开口处的一段（两角点之间）。',
     '擦掉 R18 圆在手柄处的一段（两圆角切点之间）。',
     '擦掉手柄边线两端超出圆角切点的部分。',
     '擦掉求圆心的辅助弧与平移辅助线。',
   ], notes=['只擦多余线段，已画好的轮廓一条都不要动。']),
 dict(name='描深与完成', short='描深完成', bullets=[
     '外轮廓、开口、槽、圆角用粗实线描深（粗:细 ≈ 3:1）。',
     '中心线、尺寸线保持细线，不得描粗。',
     '核对尺寸：120、74、12、14、R14、R18、R16、R8、R14、4、6、1.5、15°、R5 全部标齐。',
   ], notes=['描深顺序：先曲线后直线、先上后下、先左后右，避免蹭脏图面。']),
]

# ------------------------------------------------------------------ 时间轴
INTRO_DUR = 10.0
OUTRO_DUR = 11.0


def _dur(e):
    if e['kind'] == 'L':
        Ln = dist(e['p1'], e['p2'])
        return max(0.55, min(1.5, 0.35 + Ln*0.028))
    if e['kind'] == 'A':
        sw = abs(e['a1'] - e['a0'])
        return max(0.8, min(3.0, 0.55 + sw/360.0*2.1))
    if e['kind'] == 'P':
        return 0.55
    if e['kind'] == 'DIM':
        return 1.45
    return 0.6


def build():
    """返回 (schedule, total)。schedule: list of step dicts"""
    T = INTRO_DUR
    out = []
    for si, st in enumerate(STEPS, start=1):
        t_start = T
        items = []
        if si == 14:
            k = 0
            for e in ENT:
                er = e.get('erase')
                if not er:
                    continue
                rngs = er if isinstance(er, list) else [er]
                for r in rngs:
                    if r.get('step') != 14:
                        continue
                    items.append(dict(kind='fade', ent=e, rng=r, t0=T + k*0.11, dur=0.95))
                    k += 1
            T += k*0.11 + 0.95
        else:
            for e in [x for x in ENT if x['step'] == si]:
                d = _dur(e)
                items.append(dict(kind='draw', ent=e, t0=T, dur=d))
                T += d + 0.22
        if si == 15:
            items.append(dict(kind='boost', t0=T, dur=3.8))
            T += 3.8
        T += 2.0 if si not in (14, 15) else 1.7
        out.append(dict(idx=si, t0=t_start, t_end=T, items=items, meta=st))
    return out, T + OUTRO_DUR


if __name__ == '__main__':
    sc, total = build()
    for s in sc:
        print('%2d %-16s %6.1f → %6.1f  (%d items)' % (s['idx'], s['meta']['short'],
              s['t0'], s['t_end'], len(s['items'])))
    print('total', total, 'frames', int(total*30))
