import os

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

TEXT = '#222222'
GRID = '#8a8a8a'
BLUE, BLUE_FILL = '#0072B2', '#DCEAF7'
ORANGE, ORANGE_FILL = '#E69F00', '#FBE3B0'
GREEN, GREEN_FILL = '#009E73', '#CDEFE3'
PURPLE, PURPLE_FILL = '#CC79A7', '#F3DDEA'
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

    def path(self, d, stroke=GRID, sw=1.5, arrow=False, fill='none'):
        m = " marker-end='url(#arrow)'" if arrow else ''
        self.add(f"<path d='{d}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{m}/>")

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


def grid(svg, x0, y0, rows, cols, cell, fill=BLUE_FILL, stroke=GRID, sw=1, dash=None):
    for r in range(rows):
        for c in range(cols):
            svg.rect(x0 + c * cell, y0 + r * cell, cell, cell, fill=fill, stroke=stroke, sw=sw, dash=dash)


# ---------------------------------------------------------------------------
# 1. stride / padding / dilation
def conv_params():
    cell = 24
    svg = SVG(1060, 480)
    panels = [
        dict(title='k = 3, stride = 1', H=5, pad=0, s=1, d=1),
        dict(title='k = 3, stride = 2', H=5, pad=0, s=2, d=1),
        dict(title='k = 3, padding = 1', H=5, pad=1, s=1, d=1),
        dict(title='k = 3, dilation = 2', H=7, pad=0, s=1, d=2),
    ]
    for i, p in enumerate(panels):
        x0 = 30 + i * 262
        n = p['H'] + 2 * p['pad']
        k_eff = 1 + p['d'] * 2
        H_out = (p['H'] + 2 * p['pad'] - k_eff) // p['s'] + 1
        svg.text(x0 + 100, 30, p['title'], size=16, weight='bold')
        gx, gy = x0 + 100 - n * cell / 2, 50
        for r in range(n):
            for c in range(n):
                is_pad = r < p['pad'] or c < p['pad'] or r >= n - p['pad'] or c >= n - p['pad']
                svg.rect(gx + c * cell, gy + r * cell, cell, cell,
                         fill='white' if is_pad else BLUE_FILL, dash='3,3' if is_pad else None)
                if is_pad:
                    svg.text(gx + c * cell + cell / 2, gy + r * cell + cell / 2 + 5, '0', size=11, color='#999')
        # первая позиция ядра — заливка, вторая — пунктирная рамка
        for u in range(3):
            for v in range(3):
                svg.rect(gx + v * p['d'] * cell, gy + u * p['d'] * cell, cell, cell,
                         fill=ORANGE, opacity=0.75, stroke=ORANGE, sw=1)
        svg.rect(gx + p['s'] * cell, gy, k_eff * cell, k_eff * cell, stroke=ORANGE, sw=2.5, dash='6,4')
        svg.rect(gx, gy, k_eff * cell, k_eff * cell, stroke=ORANGE, sw=2.5)
        # выход
        oy = gy + n * cell + 45
        svg.line(x0 + 100, gy + n * cell + 8, x0 + 100, oy - 8, stroke=TEXT, sw=1.5, arrow=True)
        ox = x0 + 100 - H_out * cell / 2
        grid(svg, ox, oy, H_out, H_out, cell, fill=GREEN_FILL)
        svg.rect(ox, oy, cell, cell, fill=GREEN, opacity=0.8, stroke=GREEN)
        if H_out > 1:
            svg.rect(ox + cell, oy, cell, cell, stroke=GREEN, sw=2.5, dash='5,3')
        svg.text(x0 + 100, oy + H_out * cell + 24, f'{p["H"]}×{p["H"]} → {H_out}×{H_out}', size=15)
    svg.text(530, 465, 'заливка — первая позиция ядра, пунктир — следующая позиция; '
                       'серые нули — padding', size=13, color='#555')
    svg.save('conv_params.svg')


# ---------------------------------------------------------------------------
# 2. каналы: C_in -> C_out
def cuboid(svg, x, y, w, h, d, fill, stroke=GRID, opacity=1.0, sw=1):
    # фронт (w x h) в точке (x, y), глубина d уходит вверх-вправо
    dx, dy = d * 0.6, -d * 0.45
    svg.poly([(x, y), (x + dx, y + dy), (x + w + dx, y + dy), (x + w, y)], fill, stroke, sw, opacity)       # верх
    svg.poly([(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)], fill, stroke, sw, opacity)  # бок
    svg.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw, opacity)                    # фронт


def conv_channels():
    svg = SVG(1060, 380)
    # вход C_in x H x W: глубина = каналы
    x, y = 60, 120
    cuboid(svg, x, y, 170, 170, 70, BLUE_FILL)
    cuboid(svg, x + 20, y + 30, 45, 45, 70, ORANGE, stroke=ORANGE, opacity=0.55)   # патч по всем каналам
    svg.text(x + 105, y + 205, 'x: C_in × H × W', size=16)
    svg.text(x + 105, 70, 'патч k × k × C_in', size=14, color='#9a6a00')

    # фильтр o
    fx, fy = 340, 150
    cuboid(svg, fx, fy, 45, 45, 70, ORANGE_FILL, stroke=ORANGE, sw=1.5)
    svg.text(fx + 45, fy + 80, 'фильтр w[o]:', size=14)
    svg.text(fx + 45, fy + 100, 'C_in × k × k', size=14)
    svg.text(290, 175, '⊙', size=26)
    svg.text(fx + 45, fy + 132, 'сумма по c, u, v + b[o]', size=13, color='#555')

    # один выходной канал
    ox, oy = 560, 130
    svg.line(470, 175, 540, 175, stroke=TEXT, sw=1.5, arrow=True)
    cuboid(svg, ox, oy, 130, 130, 6, GREEN_FILL, stroke=GREEN)
    svg.rect(ox + 16, oy + 22, 13, 13, fill=GREEN, stroke=GREEN)
    svg.text(ox + 65, oy + 160, 'y[o]: H_out × W'
             '_out', size=15)
    svg.text(ox + 65, oy + 180, 'один выходной канал', size=13, color='#555')

    # стек из C_out каналов
    sx, sy = 810, 140
    svg.line(715, 175, 790, 175, stroke=TEXT, sw=1.5, arrow=True)
    svg.text(752, 160, '× C_out', size=13)
    cuboid(svg, sx, sy, 130, 130, 80, GREEN_FILL, stroke=GREEN)
    svg.text(sx + 90, sy + 160, 'y: C_out × H'
             '_out × W_out',
             size=15)
    svg.text(530, 355, 'weight: (C_out, C_in, k, k) — C_out фильтров, каждый смотрит на все C_in каналов',
             size=14, color='#555')
    svg.save('conv_channels.svg')


# ---------------------------------------------------------------------------
# 4. groups
def kernel_glyph(svg, cx, y, k, label):
    c = 9
    for u in range(k):
        for v in range(k):
            svg.rect(cx - k * c / 2 + v * c, y + u * c, c, c, fill=ORANGE_FILL, stroke=ORANGE)
    svg.text(cx, y + k * c + 15, label, size=12, color='#555')


def connect(svg, xa, xb, y0, step, C, per, colored):
    group_colors = [BLUE, ORANGE, GREEN, PURPLE]
    for a in range(C):
        for b in range(C):
            if a // per != b // per:
                continue
            col = group_colors[(a // per) % 4] if colored else GRID
            svg.line(xa + 14, y0 + a * step + 10, xb - 2, y0 + b * step + 10,
                     stroke=col, sw=1.6 if colored else 1, opacity=0.85)


def channel_column(svg, x, y0, step, C, per, fill, colored, default):
    group_colors = [BLUE, ORANGE, GREEN, PURPLE]
    for a in range(C):
        col = group_colors[(a // per) % 4] if colored else default
        svg.rect(x - 6, y0 + a * step, 20, 20, fill=fill, stroke=col, sw=2)


def groups():
    svg = SVG(1060, 470)
    C, y0, step = 8, 120, 30
    panels = [('groups = 1', 'обычная', 1, '64 линии · 9 = 576'),
              ('groups = 4', 'grouped', 4, '16 линий · 9 = 144'),
              ('groups = C_in = 8', 'depthwise', 8, '8 линий · 9 = 72')]
    for i, (title, kind, g, params) in enumerate(panels):
        x0 = 35 + i * 255
        per = C // g
        svg.text(x0 + 85, 28, title, size=16, weight='bold')
        svg.text(x0 + 85, 47, kind, size=14, color='#555')
        kernel_glyph(svg, x0 + 85, 60, 3, 'ядро 3×3')
        xs_in, xs_out = x0 + 20, x0 + 150
        connect(svg, xs_in, xs_out, y0, step, C, per, colored=g > 1)
        channel_column(svg, xs_in, y0, step, C, per, BLUE_FILL, g > 1, BLUE)
        channel_column(svg, xs_out + 4, y0, step, C, per, GREEN_FILL, g > 1, GREEN)
        svg.text(xs_in + 4, y0 + C * step + 16, 'in', size=13, color='#555')
        svg.text(xs_out + 12, y0 + C * step + 16, 'out', size=13, color='#555')
        svg.text(x0 + 85, y0 + C * step + 44, f'веса: {params}', size=14)

    # depthwise separable: depthwise 3x3 -> pointwise 1x1
    x0 = 35 + 3 * 255
    svg.text(x0 + 105, 28, 'depthwise → pointwise', size=16, weight='bold')
    svg.text(x0 + 105, 47, 'depthwise separable', size=14, color='#555')
    xs_in, xs_mid, xs_out = x0 + 10, x0 + 105, x0 + 200
    kernel_glyph(svg, (xs_in + xs_mid) / 2 + 4, 60, 3, 'ядро 3×3')
    kernel_glyph(svg, (xs_mid + xs_out) / 2 + 4, 69, 1, 'ядро 1×1')
    connect(svg, xs_in, xs_mid, y0, step, C, 1, colored=True)
    connect(svg, xs_mid + 4, xs_out, y0, step, C, C, colored=False)
    channel_column(svg, xs_in, y0, step, C, 1, BLUE_FILL, True, BLUE)
    channel_column(svg, xs_mid + 4, y0, step, C, 1, GRAY_FILL, True, GRID)
    channel_column(svg, xs_out + 4, y0, step, C, C, GREEN_FILL, False, GREEN)
    svg.text(xs_in + 4, y0 + C * step + 16, 'in', size=13, color='#555')
    svg.text(xs_out + 12, y0 + C * step + 16, 'out', size=13, color='#555')
    svg.text(x0 + 105, y0 + C * step + 44, 'веса: 8·9 + 64·1 = 136', size=14)

    svg.text(530, 452, 'каждая линия — ядро k×k между парой каналов; число линий × k² = число весов '
                       '(C_in = C_out = 8, без bias)', size=14, color='#555')
    svg.save('groups.svg')


# ---------------------------------------------------------------------------
# 5. receptive field (1D), по той же рекурсии, что в ноутбуке
def rf_panel(svg, x0, y0, width, layers, names, title, n_in):
    cell = min(26, width / n_in)
    row_gap = 58
    L = len(layers)
    # позиции нейронов слоя l во входных координатах (левый край RF)
    pos = [[float(i) for i in range(n_in)]]
    js, rs = [1], [1]
    for (k, s, d) in layers:
        prev = pos[-1]
        n_out = (len(prev) - (1 + d * (k - 1))) // s + 1
        # центр нейрона = среднее центров его входов
        pos.append([(prev[i * s] + prev[i * s + d * (k - 1)]) / 2 for i in range(n_out)])
        rs.append(rs[-1] + d * (k - 1) * js[-1])
        js.append(js[-1] * s)
    # активные нейроны: от центрального на верхнем слое вниз
    active = [set() for _ in range(L + 1)]
    active[L] = {len(pos[L]) // 2}
    edges = []
    for l in range(L, 0, -1):
        k, s, d = layers[l - 1]
        for i in active[l]:
            for u in range(k):
                src = i * s + u * d
                active[l - 1].add(src)
                edges.append((l, i, src))
    xmid = x0 + width / 2
    offset = xmid - (n_in - 1) / 2 * cell

    def cx(l, i):
        return offset + pos[l][i] * cell

    def cy(l):
        return y0 + (L - l) * row_gap + 30

    svg.text(x0, y0 + 8, title, size=15, anchor='start', weight='bold')
    for (l, i, src) in edges:
        svg.line(cx(l, i), cy(l) + cell * 0.4, cx(l - 1, src), cy(l - 1) - cell * 0.4, stroke=ORANGE, sw=1.3, opacity=0.8)
    for l in range(L + 1):
        for i in range(len(pos[l])):
            on = i in active[l]
            fill = (GREEN if l == L else ORANGE_FILL) if on else (BLUE_FILL if l == 0 else GRAY_FILL)
            svg.rect(cx(l, i) - cell * 0.4, cy(l) - cell * 0.4, cell * 0.8, cell * 0.8,
                     fill=fill, stroke=ORANGE if on and l < L else GRID, sw=1.5 if on else 0.8)
        label = 'input' if l == 0 else names[l - 1]
        svg.text(x0 + 10, cy(l) + 5, label, size=13, anchor='start', color='#555')
        svg.text(x0 + width + 5, cy(l) + 5, f'r = {rs[l]}', size=14, anchor='end')
    return y0 + L * row_gap + 60


def receptive_field_fig():
    svg = SVG(1060, 770)
    y = 20
    y = rf_panel(svg, 20, y, 1020, [(3, 1, 1)] * 3, ['conv3', 'conv3', 'conv3'],
                 'A: три свёртки 3×3 — рост линейный', n_in=21)
    y = rf_panel(svg, 20, y + 10, 1020, [(3, 1, 1), (2, 2, 1), (3, 1, 1)], ['conv3', 'pool2, s2', 'conv3'],
                 'B: conv → pool (stride 2) → conv — после stride шаг сетки удваивается', n_in=21)
    rf_panel(svg, 20, y + 10, 1020, [(3, 1, 1), (3, 1, 2), (3, 1, 4)], ['conv3', 'conv3 d2', 'conv3 d4'],
             'C: dilation 1, 2, 4 — рост экспоненциальный', n_in=31)
    svg.save('receptive_field.svg')


# ---------------------------------------------------------------------------
# 6. residual block
def residual():
    svg = SVG(1060, 300)
    y = 180
    boxes = [('conv 3×3', 170), ('BN + ReLU', 310), ('conv 3×3', 450), ('BN', 590)]
    svg.text(60, y + 6, 'x', size=22, italic=True)
    svg.line(78, y, 150, y, stroke=TEXT, sw=1.8, arrow=True)
    for i, (label, bx) in enumerate(boxes):
        svg.rect(bx - 20, y - 26, 110, 52, fill=BLUE_FILL, stroke=BLUE, sw=1.5, rx=8)
        svg.text(bx + 35, y + 6, label, size=15)
        if i < len(boxes) - 1:
            svg.line(bx + 90, y, bx + 118, y, stroke=TEXT, sw=1.8, arrow=True)
    svg.text(385, y + 55, 'F(x)', size=18, italic=True)
    svg.line(680, y, 738, y, stroke=TEXT, sw=1.8, arrow=True)
    svg.circle(755, y, 16)
    svg.text(755, y + 7, '+', size=22)
    svg.line(771, y, 820, y, stroke=TEXT, sw=1.8, arrow=True)
    svg.rect(830, y - 26, 80, 52, fill=BLUE_FILL, stroke=BLUE, sw=1.5, rx=8)
    svg.text(870, y + 6, 'ReLU', size=15)
    svg.line(910, y, 960, y, stroke=TEXT, sw=1.8, arrow=True)
    svg.text(990, y + 6, 'y', size=22, italic=True)
    # skip
    svg.path(f'M 110 {y} L 110 70 L 755 70 L 755 {y - 18}', stroke=GREEN, sw=2.5, arrow=True)
    svg.text(430, 58, 'identity: x   (или 1×1 conv со stride, если shapes различаются)', size=15, color=GREEN)
    svg.text(530, 285, 'z = x + F(x):   ∂z/∂x = I + ∂F/∂x,   y = ReLU(z)', size=16)
    svg.save('residual.svg')


# ---------------------------------------------------------------------------
# 7. pooling: max / avg / global average на одном входе 4x4
def pooling():
    svg = SVG(1060, 330)
    X = [[1, 3, 2, 0], [5, 6, 1, 2], [7, 2, 9, 4], [0, 1, 3, 8]]
    win_colors = [(BLUE, BLUE_FILL), (ORANGE, ORANGE_FILL), (GREEN, GREEN_FILL), (PURPLE, PURPLE_FILL)]
    cell = 46
    x0, y0 = 40, 80
    svg.text(x0 + 2 * cell, 50, 'x: 4 × 4', size=16, weight='bold')
    for r in range(4):
        for c in range(4):
            col, fill = win_colors[(r // 2) * 2 + c // 2]
            svg.rect(x0 + c * cell, y0 + r * cell, cell, cell, fill=fill, stroke=GRID)
            svg.text(x0 + c * cell + cell / 2, y0 + r * cell + cell / 2 + 6, str(X[r][c]), size=17)
    for k, (col, _) in enumerate(win_colors):
        r0, c0 = divmod(k, 2)
        svg.rect(x0 + 2 * c0 * cell + 2, y0 + 2 * r0 * cell + 2, 2 * cell - 4, 2 * cell - 4, stroke=col, sw=3)

    def out_grid(ox, title, vals, fmt):
        svg.text(ox + cell, 50, title, size=16, weight='bold')
        for k, v in enumerate(vals):
            r0, c0 = divmod(k, 2)
            col, fill = win_colors[k]
            svg.rect(ox + c0 * cell, y0 + cell + r0 * cell, cell, cell, fill=fill, stroke=col, sw=2.5)
            svg.text(ox + c0 * cell + cell / 2, y0 + cell + r0 * cell + cell / 2 + 6, fmt(v), size=16)

    windows = [[X[2 * r0 + u][2 * c0 + v] for u in range(2) for v in range(2)] for r0 in range(2) for c0 in range(2)]
    svg.line(x0 + 4 * cell + 15, y0 + 2 * cell, 300, y0 + 2 * cell, stroke=TEXT, sw=1.5, arrow=True)
    out_grid(320, 'MaxPool 2×2', [max(w) for w in windows], lambda v: f'{v}')
    out_grid(520, 'AvgPool 2×2', [sum(w) / 4 for w in windows], lambda v: f'{v:g}')
    gx = 780
    svg.text(gx + 90, 50, 'global avg pool', size=16, weight='bold')
    svg.rect(gx + 67, y0 + 1.5 * cell, cell, cell, fill=GRAY_FILL, stroke=TEXT, sw=2)
    svg.text(gx + 67 + cell / 2, y0 + 1.5 * cell + cell / 2 + 6, f'{sum(sum(r) for r in X) / 16:g}', size=15)
    svg.text(gx + 90, y0 + 3.3 * cell, 'среднее по всей карте:', size=13, color='#555')
    svg.text(gx + 90, y0 + 3.3 * cell + 18, '(C, H, W) → (C, 1, 1)', size=13, color='#555')
    svg.text(530, 310, 'stride = 2, окна не перекрываются; весов нет — только фиксированная функция от окна',
             size=14, color='#555')
    svg.save('pooling.svg')


conv_params()
conv_channels()
groups()
receptive_field_fig()
residual()
pooling()
print(sorted(os.listdir(OUT)))
