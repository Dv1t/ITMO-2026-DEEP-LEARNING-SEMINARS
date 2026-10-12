"""Схемы для семинаров 5–6 (детекция и сегментация). Запуск: python figures/make_figures.py"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

TEXT = '#222222'
GRID = '#8a8a8a'
MUTED = '#555555'
BLUE, BLUE_FILL = '#0072B2', '#DCEAF7'
ORANGE, ORANGE_FILL = '#E69F00', '#FBE3B0'
GREEN, GREEN_FILL = '#009E73', '#CDEFE3'
PURPLE, PURPLE_FILL = '#CC79A7', '#F3DDEA'
RED = '#D55E00'
GRAY_FILL = '#F2F2F2'
FONT = "font-family='Helvetica, Arial, sans-serif'"


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def rect(self, x, y, w, h, fill='none', stroke=GRID, sw=1, dash=None, opacity=1, rx=0):
        d = f" stroke-dasharray='{dash}'" if dash else ''
        self.add(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{rx}' fill='{fill}' "
                 f"fill-opacity='{opacity}' stroke='{stroke}' stroke-width='{sw}'{d}/>")

    def line(self, x1, y1, x2, y2, stroke=GRID, sw=1, arrow=False, dash=None, opacity=1):
        m = " marker-end='url(#arrow)'" if arrow else ''
        d = f" stroke-dasharray='{dash}'" if dash else ''
        self.add(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' "
                 f"stroke-width='{sw}' stroke-opacity='{opacity}'{m}{d}/>")

    def poly(self, pts, fill, stroke=GRID, sw=1, opacity=1):
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.add(f"<polygon points='{p}' fill='{fill}' fill-opacity='{opacity}' stroke='{stroke}' stroke-width='{sw}'/>")

    def path(self, d, stroke=GRID, sw=1.5, arrow=False, fill='none', dash=None):
        m = " marker-end='url(#arrow)'" if arrow else ''
        ds = f" stroke-dasharray='{dash}'" if dash else ''
        self.add(f"<path d='{d}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{m}{ds}/>")

    def circle(self, x, y, r, fill='white', stroke=TEXT, sw=1.5):
        self.add(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=14, anchor='middle', color=TEXT, weight='normal', italic=False):
        st = " font-style='italic'" if italic else ''
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' fill='{color}' "
                 f"font-weight='{weight}'{st} {FONT}>{s}</text>")

    def save(self, name):
        head = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.w}' height='{self.h}' "
                f"viewBox='0 0 {self.w} {self.h}'>"
                "<defs><marker id='arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
                f"orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{TEXT}'/></marker></defs>"
                f"<rect width='100%' height='100%' fill='white'/>")
        with open(os.path.join(OUT, name), 'w') as f:
            f.write(head + '\n'.join(self.items) + '</svg>')


def cuboid(svg, x, y, w, h, d, fill, stroke=GRID, opacity=1.0, sw=1):
    # фронт (w x h) в точке (x, y), глубина d уходит вверх-вправо
    dx, dy = d * 0.6, -d * 0.45
    svg.poly([(x, y), (x + dx, y + dy), (x + w + dx, y + dy), (x + w, y)], fill, stroke, sw, opacity)
    svg.poly([(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)], fill, stroke, sw, opacity)
    svg.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw, opacity)


def box_iou(a, b):
    iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    area = lambda r: (r[2] - r[0]) * (r[3] - r[1])
    return inter / (area(a) + area(b) - inter)


# ---------------------------------------------------------------------------
# 1. IoU: пересечение, объединение и как выглядят IoU = 0.3 / 0.5 / 0.8
def iou_fig():
    svg = SVG(1060, 330)
    A, B = (0, 0, 130, 130), (60, 50, 190, 180)
    for k, (title, mode) in enumerate([('A ∩ B', 'inter'), ('A ∪ B', 'union')]):
        ox, oy = 30 + k * 230, 70
        if mode == 'union':
            for r in (A, B):
                svg.rect(ox + r[0], oy + r[1], r[2] - r[0], r[3] - r[1], fill=GREEN_FILL, stroke='none')
        else:
            svg.rect(ox + B[0], oy + B[1], A[2] - B[0], A[3] - B[1], fill=GREEN_FILL, stroke='none')
        svg.rect(ox + A[0], oy + A[1], 130, 130, stroke=BLUE, sw=2.5)
        svg.rect(ox + B[0], oy + B[1], 130, 130, stroke=ORANGE, sw=2.5)
        svg.text(ox + 10, oy + 22, 'A', size=18, anchor='start', color=BLUE, weight='bold')
        svg.text(ox + 180, oy + 172, 'B', size=18, anchor='end', color=ORANGE, weight='bold')
        svg.text(ox + 95, 40, title, size=17, weight='bold')
    svg.text(245, 300, 'IoU = |A ∩ B| / |A ∪ B|', size=17)

    svg.line(490, 30, 490, 310, stroke='#cccccc')
    svg.text(775, 40, 'одинаковые квадраты, сдвиг по диагонали', size=15, color=MUTED)
    s = 110
    for k, target in enumerate([0.3, 0.5, 0.8]):
        delta = s * (1 - math.sqrt(2 * target / (1 + target)))   # IoU = (s - d)^2 / (2 s^2 - (s - d)^2)
        a, b = (0, 0, s, s), (delta, delta, s + delta, s + delta)
        ox, oy = 530 + k * 180, 85
        svg.rect(ox + b[0], oy + b[1], s - delta, s - delta, fill=GREEN_FILL, stroke='none')
        svg.rect(ox, oy, s, s, stroke=BLUE, sw=2.5)
        svg.rect(ox + delta, oy + delta, s, s, stroke=ORANGE, sw=2.5)
        svg.text(ox + (s + delta) / 2, oy + s + 75, f'IoU = {box_iou(a, b):.2f}', size=16, weight='bold')
    svg.save('iou.svg')


# ---------------------------------------------------------------------------
# 2. кодирование бокса относительно anchor
def box_encoding():
    svg = SVG(1060, 350)
    # anchor: центр (xa, ya), размер wa x ha;  GT: центр (x, y), размер w x h
    xa, ya, wa, ha = 200, 140, 200, 200
    x, y, w, h = 270, 95, 250, 150
    svg.rect(xa - wa / 2, ya - ha / 2, wa, ha, stroke=ORANGE, sw=2.5, dash='8,5')
    svg.rect(x - w / 2, y - h / 2, w, h, stroke=BLUE, sw=2.5)
    svg.text(xa - wa / 2 + 8, ya + ha / 2 - 10, 'anchor a', size=15, anchor='start', color=ORANGE, weight='bold')
    svg.text(x + w / 2 - 8, y - h / 2 + 22, 'GT b', size=15, anchor='end', color=BLUE, weight='bold')
    svg.circle(xa, ya, 5, fill=ORANGE, stroke=ORANGE)
    svg.circle(x, y, 5, fill=BLUE, stroke=BLUE)
    svg.text(xa - 10, ya + 22, '(x_a, y_a)', size=13, anchor='end', color=ORANGE)
    svg.text(x + 10, y - 10, '(x, y)', size=13, anchor='start', color=BLUE)
    # сдвиг центра
    svg.line(xa, ya, x - 4, ya, stroke=TEXT, sw=1.8, arrow=True)
    svg.line(x, ya, x, y + 7, stroke=TEXT, sw=1.8, arrow=True)
    svg.text((xa + x) / 2, ya + 22, 't_x · w_a', size=14)
    svg.text(x + 8, (ya + y) / 2 + 12, 't_y · h_a', size=14, anchor='start')
    # ширины
    yb = 270
    svg.line(xa - wa / 2, yb, xa + wa / 2, yb, stroke=ORANGE, sw=1.5)
    svg.line(xa - wa / 2, yb - 6, xa - wa / 2, yb + 6, stroke=ORANGE, sw=1.5)
    svg.line(xa + wa / 2, yb - 6, xa + wa / 2, yb + 6, stroke=ORANGE, sw=1.5)
    svg.text(xa, yb + 22, 'w_a', size=14, color=ORANGE)
    yb = 305
    svg.line(x - w / 2, yb, x + w / 2, yb, stroke=BLUE, sw=1.5)
    svg.line(x - w / 2, yb - 6, x - w / 2, yb + 6, stroke=BLUE, sw=1.5)
    svg.line(x + w / 2, yb - 6, x + w / 2, yb + 6, stroke=BLUE, sw=1.5)
    svg.text(x + w / 2 + 10, yb + 5, 'w = w_a · exp(t_w)', size=14, anchor='start', color=BLUE)

    tx0 = 650
    svg.text(tx0, 50, 'encode:  b, a  →  t', size=16, anchor='start', weight='bold')
    rows = ['t_x = (x − x_a) / w_a', 't_y = (y − y_a) / h_a', 't_w = log(w / w_a)', 't_h = log(h / h_a)']
    for i, r in enumerate(rows):
        svg.text(tx0 + 20, 82 + 26 * i, r, size=15, anchor='start')
    svg.text(tx0, 210, 'decode:  t, a  →  b', size=16, anchor='start', weight='bold')
    rows = ['x = x_a + t_x · w_a', 'w = w_a · exp(t_w)']
    for i, r in enumerate(rows):
        svg.text(tx0 + 20, 242 + 26 * i, r, size=15, anchor='start')
    svg.text(tx0, 315, 'сеть предсказывает t, а не координаты b', size=14, anchor='start', color=MUTED)
    svg.save('box_encoding.svg')


# ---------------------------------------------------------------------------
# 3. детектор: ResNet18 -> FPN -> общая голова на каждом уровне
def detector():
    svg = SVG(1060, 400)
    # вход
    svg.rect(20, 140, 100, 100, fill=BLUE_FILL, stroke=BLUE, sw=1.5)
    svg.text(70, 130, 'x: 3 × 320²', size=14)
    svg.line(125, 190, 160, 190, stroke=TEXT, sw=1.8, arrow=True)
    # backbone: C3, C4, C5
    svg.rect(165, 60, 175, 280, fill=GRAY_FILL, stroke=GRID, sw=1.5, rx=8)
    svg.text(252, 85, 'ResNet18 (ImageNet)', size=14, weight='bold')
    feats = [('C3', '128 × 40²', 'stride 8', 70), ('C4', '256 × 20²', 'stride 16', 52), ('C5', '512 × 10²', 'stride 32', 36)]
    ys = [280, 200, 130]
    for (name, shape, stride, s), y in zip(feats, ys):
        svg.rect(180, y - s / 2, s * 0.6, s, fill=BLUE_FILL, stroke=BLUE, sw=1.3)
        svg.text(180 + s * 0.6 + 8, y - 2, f'{name}: {shape}', size=12, anchor='start')
        svg.text(180 + s * 0.6 + 8, y + 14, stride, size=11, anchor='start', color=MUTED)
    # FPN
    svg.line(345, 200, 380, 200, stroke=TEXT, sw=1.8, arrow=True)
    svg.rect(385, 40, 160, 320, fill=GREEN_FILL, stroke=GREEN, sw=1.5, rx=8)
    svg.text(465, 63, 'FPN, 128 каналов', size=14, weight='bold')
    levels = [('P̃3', '40²'), ('P̃4', '20²'), ('P̃5', '10²'), ('P̃6', '5²')]
    py = [315, 240, 170, 105]
    for (name, grid), y in zip(levels, py):
        svg.rect(400, y - 18, 130, 36, fill='white', stroke=GREEN, sw=1.3, rx=5)
        svg.text(465, y + 5, f'{name}: {grid}', size=13)
        svg.line(535, y, 625, 205, stroke=GRID, sw=1.2, arrow=True)
    # голова
    svg.rect(630, 150, 165, 110, fill=PURPLE_FILL, stroke=PURPLE, sw=1.5, rx=8)
    svg.text(712, 178, 'одна голова', size=14, weight='bold')
    svg.text(712, 198, 'на каждом уровне', size=12, color=MUTED)
    svg.text(712, 220, 'cls: conv 3×3 ×2 → K·A', size=12)
    svg.text(712, 240, 'box: conv 3×3 ×2 → 4·A', size=12)
    for k, (out, sub) in enumerate([('(B, N, K)', 'логиты классов, sigmoid'), ('(B, N, 4)', 'поправки t к anchors')]):
        y = 175 + k * 60
        svg.line(800, y, 840, y, stroke=TEXT, sw=1.6, arrow=True)
        svg.text(848, y + 5, out, size=15, anchor='start')
        svg.text(848, y + 24, sub, size=12, anchor='start', color=MUTED)
    svg.text(530, 388, 'выходы уровней склеиваются: N = (40² + 20² + 10² + 5²) · A = 19 125 anchors, A = 9', size=14, color=MUTED)
    svg.save('detector.svg')


# ---------------------------------------------------------------------------
# 4. U-Net с энкодером ResNet18, вход 3 × 256²
def unet():
    svg = SVG(1100, 600)
    enc = [('conv1', 64, 128), ('layer1', 64, 64), ('layer2', 128, 32), ('layer3', 256, 16), ('layer4', 512, 8)]
    bar_w = {64: 18, 128: 26, 256: 36, 512: 48}
    bar_h = {128: 120, 64: 92, 32: 68, 16: 50, 8: 36}
    level_y = [40, 175, 290, 385, 465]
    enc_x = [40, 140, 240, 345, 455]
    centers = []
    for l, (name, c, s) in enumerate(enc):
        w, h = bar_w[c], bar_h[s]
        x, y = enc_x[l], level_y[l]
        svg.rect(x, y, w, h, fill=BLUE_FILL, stroke=BLUE, sw=1.3)
        svg.text(x + w / 2, y - 6, str(c), size=13)
        svg.text(x - 6, y + h / 2 + 4, f'{s}²', size=12, anchor='end', color=MUTED)
        svg.text(x + w / 2, y + h + 15, name, size=11, color=MUTED)
        centers.append((x, x + w, y + h / 2))
        if l < 4:
            svg.line(x + w / 2, y + h + 20, enc_x[l + 1] + 4, level_y[l + 1] - 16, stroke=RED, sw=2, arrow=True)
    # декодер: уровни 3, 2, 1, 0 (снизу вверх)
    prev_top = (centers[4][1] + 2, level_y[4] + 6)
    for k, l in enumerate([3, 2, 1, 0]):
        c, s = enc[l][1], enc[l][2]
        w, h = bar_w[c], bar_h[s]
        x, y = [600, 710, 820, 930][k], level_y[l]
        svg.rect(x - 2 * w - 6, y, w, h, fill=ORANGE_FILL, stroke=ORANGE, sw=1.3)   # копия энкодера
        svg.rect(x - w - 2, y, w, h, fill=GREEN_FILL, stroke=GREEN, sw=1.3)         # upsampling
        for j in range(2):                                                             # DoubleConv
            svg.rect(x + 6 + j * (w + 4), y, w, h, fill=GREEN_FILL, stroke=GREEN, sw=1.3)
        right = x + 6 + 2 * w + 4
        svg.text(x + 6 + w + 2, y - 6, str(c), size=13)
        svg.line(prev_top[0], prev_top[1], x - w / 2 - 2, y + h + 6, stroke=GREEN, sw=2, arrow=True)
        svg.line(centers[l][1] + 6, centers[l][2], x - 2 * w - 12, centers[l][2], stroke=ORANGE, sw=2, dash='7,5', arrow=True)
        prev_top = (right + 2, y + 12)
    svg.text(560, level_y[0] + bar_h[128] / 2 - 8, 'копия + concat', size=13, color='#9a6a00')
    # голова: up ×2 до 256², conv 1×1 -> 21 класс
    hx, hy = prev_top[0] + 8, level_y[0] + bar_h[128] / 2
    svg.line(hx, hy, hx + 30, hy, stroke=GREEN, sw=2, arrow=True)
    svg.rect(hx + 34, hy - 60, 12, 120, fill=PURPLE_FILL, stroke=PURPLE, sw=1.3)
    svg.text(hx + 40, hy + 78, '21 × 256²', size=13)
    svg.text(hx + 40, hy + 95, 'up ×2, conv 1×1', size=11, color=MUTED)
    # грубые логиты: conv 1×1 по layer4, up ×32, прибавляются к выходу декодера (раздел 12)
    lx, ly = centers[4][1] + 4, centers[4][2]
    svg.path(f'M{lx:.1f},{ly:.1f} L{lx + 20:.1f},{ly:.1f} L{lx + 20:.1f},556 L1080,556 L1080,{hy + 30:.1f} L{hx + 50:.1f},{hy + 30:.1f}',
             stroke=PURPLE, sw=2, dash='7,5', arrow=True)
    svg.text(lx + 30, 580, 'грубые логиты: conv 1×1 по layer4, up ×32 — прибавляются к выходу декодера',
             size=13, anchor='start', color='#a0507f')
    items = [(BLUE, 'энкодер: ResNet18 с ImageNet'), (RED, 'сжатие ×2 (stride / max-pool)'),
             (GREEN, 'ConvTranspose2d 2×2, stride 2 и DoubleConv'), (ORANGE, 'skip: копия карты энкодера, concat по каналам')]
    for i, (col, label) in enumerate(items):
        x, ly = 600, 470 + i * 20
        svg.line(x, ly - 5, x + 26, ly - 5, stroke=col, sw=3)
        svg.text(x + 34, ly, label, size=13, anchor='start')
    svg.save('unet.svg')


# ---------------------------------------------------------------------------
# 5. FPN детектора: C3..C5 -> P3..P6
def fpn():
    svg = SVG(1060, 520)
    levels = [('C3', '128 × 40²', 110), ('C4', '256 × 20²', 76), ('C5', '512 × 10²', 48)]
    ys = [400, 270, 150]
    cx_c, cx_p, cx_o = 150, 520, 740
    for (name, shape, s), y in zip(levels, ys):
        cuboid(svg, cx_c - s / 2, y - s / 2 + 10, s, s, 24, BLUE_FILL, stroke=BLUE)
        svg.text(cx_c - s / 2 - 12, y + 10, name, size=16, anchor='end', weight='bold', color=BLUE)
        svg.text(cx_c - s / 2 - 12, y + 28, shape, size=12, anchor='end', color=MUTED)
    for k in range(2):
        svg.line(cx_c, ys[k] - levels[k][2] / 2 - 4, cx_c, ys[k + 1] + levels[k + 1][2] / 2 + 14, stroke=TEXT, sw=1.6, arrow=True)
    svg.text(cx_c + 70, 490, 'bottom-up: ResNet18', size=14, color=MUTED)
    for (name, _, s), y in zip(levels, ys):
        p = 'P' + name[1]
        top = name == 'C5'
        svg.line(cx_c + s / 2 + 24, y, cx_p - (2 if top else 40), y, stroke=ORANGE, sw=2, arrow=True)
        svg.text((cx_c + cx_p) / 2 + 20, y - 8, 'conv 1×1', size=13, color='#9a6a00')
        if not top:
            svg.circle(cx_p - 22, y, 14)
            svg.text(cx_p - 22, y + 6, '+', size=20)
        svg.rect(cx_p + 4, y - s / 2, s * 0.55, s, fill=GREEN_FILL, stroke=GREEN, sw=1.5)
        svg.text(cx_p + 4 + s * 0.275, y + 6, p, size=15, weight='bold', color=GREEN)
        svg.line(cx_p + 4 + s * 0.55 + 6, y, cx_o - 10, y, stroke=TEXT, sw=1.5, arrow=True)
        svg.text((cx_p + cx_o) / 2 + 30, y - 8, 'conv 3×3', size=12, color=MUTED)
        svg.rect(cx_o, y - 22, 100, 44, fill=GRAY_FILL, stroke=GRID, rx=6)
        svg.text(cx_o + 50, y + 5, f'P̃{name[1]}: 128 ch', size=13)
    for k in (2, 1):
        svg.path(f'M {cx_p - 22} {ys[k] + (2 if k == 2 else 16)} L {cx_p - 22} {ys[k - 1] - 16}', stroke=GREEN, sw=2, arrow=True)
        svg.text(cx_p - 32, (ys[k] + ys[k - 1]) / 2 + 4, 'up ×2', size=13, anchor='end', color=GREEN)
    # P6: свёртка со stride 2 поверх P5
    y6 = 55
    svg.line(cx_o + 50, ys[2] - 24, cx_o + 50, y6 + 24, stroke=TEXT, sw=1.5, arrow=True)
    svg.text(cx_o + 58, (ys[2] + y6) / 2 + 4, 'conv 3×3, stride 2', size=12, anchor='start', color=MUTED)
    svg.rect(cx_o, y6 - 22, 100, 44, fill=GRAY_FILL, stroke=GRID, rx=6)
    svg.text(cx_o + 50, y6 + 5, 'P̃6: 128 ch', size=13)
    svg.text(cx_p + 10, 490, 'top-down + lateral', size=14, color=MUTED)
    svg.rect(905, 110, 140, 150, fill=PURPLE_FILL, stroke=PURPLE, rx=8)
    for i, t in enumerate(['детекция:', 'одна голова', 'на каждом', 'уровне P̃3–P̃6', '(раздел 6)']):
        svg.text(975, 140 + 20 * i, t, size=13, weight='bold' if i == 0 else 'normal')
    svg.rect(905, 300, 140, 150, fill=ORANGE_FILL, stroke=ORANGE, rx=8)
    for i, t in enumerate(['сегментация:', 'все P̃ → up', 'до P̃3, сумма,', 'conv 1×1, up', '(раздел 16)']):
        svg.text(975, 330 + 20 * i, t, size=13, weight='bold' if i == 0 else 'normal')
    svg.line(865, y6, 865, ys[0], stroke=TEXT, sw=1.5)
    for y in [y6] + ys:
        svg.line(cx_o + 102, y, 865, y, stroke=TEXT, sw=1.5)
    svg.line(865, 185, 900, 185, stroke=TEXT, sw=1.5, arrow=True)
    svg.line(865, 375, 900, 375, stroke=TEXT, sw=1.5, arrow=True)
    svg.save('fpn.svg')


# ---------------------------------------------------------------------------
# 6. RoIPool vs RoIAlign
def roi_align_fig():
    svg = SVG(1060, 500)
    cell, n = 44, 8
    box = (1.3, 1.6, 6.4, 5.7)   # в клетках карты признаков
    for k, title in enumerate(['RoIPool: округление', 'RoIAlign: без округления']):
        ox, oy = 60 + k * 520, 70
        svg.text(ox + n * cell / 2, 40, title, size=17, weight='bold')
        for r in range(n):
            for c in range(n):
                svg.rect(ox + c * cell, oy + r * cell, cell, cell, fill=GRAY_FILL, stroke='#bbbbbb')
        x1, y1, x2, y2 = (v * cell for v in box)
        svg.rect(ox + x1, oy + y1, x2 - x1, y2 - y1, stroke=TEXT, sw=1.5, dash='6,4')
        if k == 0:
            qx1, qy1, qx2, qy2 = (round(v) for v in box)            # границы бокса -> целые клетки
            svg.rect(ox + qx1 * cell, oy + qy1 * cell, (qx2 - qx1) * cell, (qy2 - qy1) * cell,
                     fill=ORANGE_FILL, opacity=0.6, stroke=ORANGE, sw=2.5)
            mx, my = qx1 + (qx2 - qx1) // 2, qy1 + (qy2 - qy1) // 2   # 2 x 2 ячейки неравного размера
            svg.line(ox + mx * cell, oy + qy1 * cell, ox + mx * cell, oy + qy2 * cell, stroke=ORANGE, sw=2.5)
            svg.line(ox + qx1 * cell, oy + my * cell, ox + qx2 * cell, oy + my * cell, stroke=ORANGE, sw=2.5)
            svg.text(ox + n * cell / 2, oy + n * cell + 30, 'бокс и ячейки 2×2 прилипают к сетке:', size=14)
            svg.text(ox + n * cell / 2, oy + n * cell + 50, 'ячейки разного размера, сдвиг до половины клетки', size=14)
        else:
            svg.rect(ox + x1, oy + y1, x2 - x1, y2 - y1, fill=GREEN_FILL, opacity=0.5, stroke=GREEN, sw=2.5)
            bw, bh = (x2 - x1) / 2, (y2 - y1) / 2
            svg.line(ox + x1 + bw, oy + y1, ox + x1 + bw, oy + y2, stroke=GREEN, sw=2.5)
            svg.line(ox + x1, oy + y1 + bh, ox + x2, oy + y1 + bh, stroke=GREEN, sw=2.5)
            pts = []
            for by in range(2):
                for bx in range(2):
                    for sy in range(2):
                        for sx in range(2):   # sampling_ratio = 2: 2 x 2 точки в ячейке
                            px = x1 + bx * bw + (sx + 0.5) * bw / 2
                            py = y1 + by * bh + (sy + 0.5) * bh / 2
                            pts.append((px, py))
            # билинейная интерполяция одной точки по 4 центрам клеток
            px, py = pts[0]
            c0x, c0y = math.floor(px / cell - 0.5), math.floor(py / cell - 0.5)
            for dx in (0, 1):
                for dy in (0, 1):
                    qx, qy = (c0x + dx + 0.5) * cell, (c0y + dy + 0.5) * cell
                    svg.line(ox + px, oy + py, ox + qx, oy + qy, stroke=BLUE, sw=1.3)
                    svg.circle(ox + qx, oy + qy, 3.5, fill=BLUE, stroke=BLUE, sw=1)
            for px, py in pts:
                svg.circle(ox + px, oy + py, 4, fill=RED, stroke=RED, sw=1)
            svg.text(ox + n * cell / 2, oy + n * cell + 30, 'ячейки 2×2 точно по боксу, в каждой 2×2 точки;', size=14)
            svg.text(ox + n * cell / 2, oy + n * cell + 50, 'значение в точке — билинейно по 4 соседним клеткам', size=14)
    svg.save('roi_align.svg')


if __name__ == '__main__':
    iou_fig()
    box_encoding()
    detector()
    unet()
    fpn()
    roi_align_fig()
    print(sorted(f for f in os.listdir(OUT) if f.endswith('.svg')))
