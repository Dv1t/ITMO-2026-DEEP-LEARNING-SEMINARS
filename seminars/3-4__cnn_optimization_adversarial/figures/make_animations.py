"""Анимации для раздела про свёртки. Запуск: python figures/make_animations.py"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle
import numpy as np
import torch
import torch.nn.functional as F

OUT = os.path.dirname(os.path.abspath(__file__))
BLUE_FILL, ORANGE, ORANGE_FILL = '#DCEAF7', '#E69F00', '#FBE3B0'
GREEN, GREEN_FILL, GRID = '#009E73', '#CDEFE3', '#8a8a8a'


def draw_grid(ax, M, fills, title, fontsize=15, highlight=None, hl_color=ORANGE, show=None):
    # fills: матрица цветов; show: маска, какие числа печатать
    ax.clear()
    n, m = M.shape
    for r in range(n):
        for c in range(m):
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=fills[r][c], edgecolor=GRID, linewidth=1))
            if show is None or show[r, c]:
                ax.text(c + 0.5, r + 0.5, f'{M[r, c]:.0f}', ha='center', va='center', fontsize=fontsize)
    if highlight is not None:
        r0, c0, h, w = highlight
        ax.add_patch(Rectangle((c0, r0), w, h, fill=False, edgecolor=hl_color, linewidth=3.5))
    ax.set_xlim(-0.1, m + 0.1)
    ax.set_ylim(n + 0.1, -0.1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=15)


def signed(v):
    return f'({v:.0f})' if v < 0 else f'{v:.0f}'


# ---------------------------------------------------------------------------
# 1. ядро скользит по картинке — те же x_small и w_small, что в разделе 2
def conv_sliding():
    torch.manual_seed(0)
    x = torch.randint(0, 10, (5, 5)).float()
    w = torch.tensor([[1., 0., -1.], [2., 0., -2.], [1., 0., -1.]])
    y = F.conv2d(x[None, None], w[None, None])[0, 0]
    x, w, y = x.numpy(), w.numpy(), y.numpy()

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), gridspec_kw={'width_ratios': [5, 3, 3]})
    caption = fig.text(0.5, 0.04, '', ha='center', fontsize=13)
    positions = [(i, j) for i in range(3) for j in range(3)]

    def update(t):
        i, j = positions[min(t, 8)]
        in_fill = [[ORANGE_FILL if i <= r < i + 3 and j <= c < j + 3 else BLUE_FILL for c in range(5)] for r in range(5)]
        draw_grid(axes[0], x, in_fill, 'x', highlight=(i, j, 3, 3))
        draw_grid(axes[1], w, [[ORANGE_FILL] * 3] * 3, 'w (Sobel)')
        done = np.zeros((3, 3), bool)
        for k in range(min(t, 8) + 1):
            done[positions[k]] = True
        out_fill = [[GREEN if (r, c) == (i, j) else (GREEN_FILL if done[r, c] else 'white') for c in range(3)] for r in range(3)]
        draw_grid(axes[2], y, out_fill, 'y = conv2d(x, w)', highlight=(i, j, 1, 1), hl_color=GREEN, show=done)
        terms = ' + '.join(f'{x[i + u, j + v]:.0f}·{signed(w[u, v])}' for u in range(3) for v in range(3) if w[u, v] != 0)
        caption.set_text(f'y[{i}, {j}] = {terms} = {y[i, j]:.0f}')

    frames = list(range(9)) + [8] * 3
    FuncAnimation(fig, update, frames=frames).save(os.path.join(OUT, 'conv_sliding.gif'), writer=PillowWriter(fps=1), dpi=80)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. несколько входных каналов -> один выходной канал
def conv_channels_anim():
    rng = np.random.default_rng(1)
    C = 3
    x = rng.integers(0, 4, size=(C, 5, 5)).astype(float)
    w = rng.integers(-1, 2, size=(C, 3, 3)).astype(float)
    b = 1.0
    y = F.conv2d(torch.tensor(x)[None], torch.tensor(w)[None], torch.tensor([b], dtype=torch.float64))[0, 0].numpy()
    partial = np.array([[[np.sum(x[c, i:i + 3, j:j + 3] * w[c]) for j in range(3)] for i in range(3)] for c in range(C)])
    assert np.allclose(partial.sum(0) + b, y)

    tints = ['#F8D5D0', '#D5EDD5', '#D6E4F7']   # «R», «G», «B»
    fig = plt.figure(figsize=(13, 6.6))
    gs = fig.add_gridspec(2, 4, width_ratios=[5, 5, 5, 4], height_ratios=[5, 3.2])
    ax_x = [fig.add_subplot(gs[0, c]) for c in range(C)]
    ax_w = [fig.add_subplot(gs[1, c]) for c in range(C)]
    ax_y = fig.add_subplot(gs[:, 3])
    caption = fig.text(0.5, 0.02, '', ha='center', fontsize=14)
    positions = [(i, j) for i in range(3) for j in range(3)]

    def update(t):
        i, j = positions[min(t, 8)]
        for c in range(C):
            fill = [[ORANGE_FILL if i <= r < i + 3 and j <= cc < j + 3 else tints[c] for cc in range(5)] for r in range(5)]
            draw_grid(ax_x[c], x[c], fill, f'x[c={c}]', fontsize=13, highlight=(i, j, 3, 3))
            draw_grid(ax_w[c], w[c], [[ORANGE_FILL] * 3] * 3, f'w[o, c={c}]   s{c} = {partial[c, i, j]:.0f}', fontsize=13)
        done = np.zeros((3, 3), bool)
        for k in range(min(t, 8) + 1):
            done[positions[k]] = True
        out_fill = [[GREEN if (r, cc) == (i, j) else (GREEN_FILL if done[r, cc] else 'white') for cc in range(3)] for r in range(3)]
        draw_grid(ax_y, y, out_fill, 'y[o]: один канал', highlight=(i, j, 1, 1), hl_color=GREEN, show=done)
        s = ' + '.join(signed(partial[c, i, j]) for c in range(C))
        caption.set_text(f'y[o, {i}, {j}] = s0 + s1 + s2 + b = {s} + {b:.0f} = {y[i, j]:.0f}')

    frames = list(range(9)) + [8] * 3
    FuncAnimation(fig, update, frames=frames).save(os.path.join(OUT, 'conv_multichannel.gif'), writer=PillowWriter(fps=1), dpi=75)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. PGD в 2D: шаг ascent и проекция на шар L_inf / L_2
def pgd_2d():
    th = np.deg2rad(30)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    H = R @ np.diag([1.0, 5.0]) @ R.T
    c = np.array([2.6, 1.0])
    x0, eps, alpha, steps = np.zeros(2), 1.0, 0.25, 10

    def loss(z):
        d = z - c
        return -0.5 * np.einsum('...i,ij,...j->...', d, H, d)

    def grad(z):
        return H @ (c - z)

    def run(kind):
        z, history = x0.copy(), []
        for _ in range(steps):
            g = grad(z)
            if kind == 'inf':
                proposal = z + alpha * np.sign(g)
                projected = np.clip(proposal, x0 - eps, x0 + eps)
            else:
                proposal = z + alpha * g / np.linalg.norm(g)
                delta = proposal - x0
                projected = x0 + delta * min(1.0, eps / np.linalg.norm(delta))
            history.append((z.copy(), proposal, projected))
            z = projected
        return history

    runs = {'inf': run('inf'), '2': run('2')}
    colors = {'inf': ORANGE, '2': '#CC79A7'}
    labels = {'inf': r'PGD $L_\infty$: $\alpha\,\mathrm{sign}(g)$ + clip', '2': r'PGD $L_2$: $\alpha\, g/\|g\|$ + масштаб'}
    fgsm = x0 + eps * np.sign(grad(x0))

    xs, ys = np.meshgrid(np.linspace(-1.8, 2.8, 300), np.linspace(-1.8, 2.0, 300))
    Z = loss(np.stack([xs, ys], -1))
    fig, ax = plt.subplots(figsize=(8.5, 7.2))

    def update(frame):
        k, phase = divmod(frame, 2)
        k = min(k, steps - 1)
        ax.clear()
        ax.contour(xs, ys, Z, levels=15, cmap='Greys', linewidths=0.8)
        ax.add_patch(Rectangle((x0[0] - eps, x0[1] - eps), 2 * eps, 2 * eps, fill=False, edgecolor=ORANGE, lw=2))
        ax.add_patch(plt.Circle(x0, eps, fill=False, edgecolor='#CC79A7', lw=2))
        ax.plot(*x0, 'ko', ms=7)
        ax.text(x0[0] - 0.08, x0[1] - 0.15, 'x', fontsize=14, ha='right')
        ax.plot(*c, 'kx', ms=10, mew=2)
        ax.text(c[0] + 0.07, c[1] + 0.07, 'max L', fontsize=11)
        ax.plot(*fgsm, marker='*', color='gray', ms=16, ls='none', label=f'FGSM, L = {loss(fgsm):.2f}')
        for kind, hist in runs.items():
            done = [h[2] for h in hist[:k]] if phase == 0 else [h[2] for h in hist[:k + 1]]
            path = np.array([x0] + done)
            ax.plot(path[:, 0], path[:, 1], 'o-', color=colors[kind], ms=5, lw=1.8,
                    label=f'{labels[kind]}, L = {loss(path[-1]):.2f}')
            z, proposal, projected = hist[k]
            ax.annotate('', xy=proposal, xytext=z, arrowprops=dict(arrowstyle='->', color=colors[kind], lw=1.5, ls='--'))
            ax.plot(*proposal, 'o', mfc='white', mec=colors[kind], ms=7)
            if phase == 1 and np.linalg.norm(proposal - projected) > 1e-9:
                ax.annotate('', xy=projected, xytext=proposal, arrowprops=dict(arrowstyle='->', color='black', lw=1.3, ls=':'))
        ax.set_xlim(-1.8, 2.8)
        ax.set_ylim(-1.8, 2.0)
        ax.set_aspect('equal')
        ax.legend(loc='lower right', fontsize=9)
        ax.set_title(f'шаг {k + 1}: ' + ('ascent (пунктир)' if phase == 0 else 'проекция обратно в шар (точки)'), fontsize=13)

    frames = list(range(2 * steps)) + [2 * steps - 1] * 3
    FuncAnimation(fig, update, frames=frames).save(os.path.join(OUT, 'pgd_2d.gif'), writer=PillowWriter(fps=1.2), dpi=75)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Sobel на «видео» 512x512: кадры = batch, одна F.conv2d на все кадры
def sobel_scene(t, T, size=512):
    yy, xx = torch.meshgrid(torch.arange(size, dtype=torch.float32), torch.arange(size, dtype=torch.float32), indexing='ij')
    phase = 2 * np.pi * t / T
    frame = torch.zeros(size, size)
    cx = 70 + 250 * t / T                                            # круг едет вправо
    frame[(xx - cx) ** 2 + (yy - 80) ** 2 < 45 ** 2] = 1.0
    u = (xx - 380) * np.cos(phase / 2) + (yy - 330) * np.sin(phase / 2)   # прямоугольник вращается
    v = -(xx - 380) * np.sin(phase / 2) + (yy - 330) * np.cos(phase / 2)
    frame[(u.abs() < 90) & (v.abs() < 25)] = 0.6
    frame[(yy > 330) & (yy < 480) & (xx > 30) & (xx - 30 < (yy - 330))] = 0.8   # треугольник стоит
    ex, ey = 190 + 40 * np.cos(phase), 245 + 40 * np.sin(phase)       # эллипс ходит по кругу
    frame[((xx - ex) / 55) ** 2 + ((yy - ey) / 28) ** 2 < 1] = 0.9
    r_ring = 40 + 15 * np.sin(phase)                                 # кольцо пульсирует
    dist = ((xx - 430) ** 2 + (yy - 110) ** 2).sqrt()
    frame[(dist < r_ring) & (dist > r_ring - 15)] = 0.7
    sy = 150 + 120 * t / T                                           # квадрат едет вниз
    frame[(xx > 40) & (xx < 90) & (yy > sy) & (yy < sy + 50)] = 0.5
    c, s_ = np.cos(-phase / 2), np.sin(-phase / 2)                   # крест вращается
    cu = (xx - 255) * c + (yy - 450) * s_
    cv = -(xx - 255) * s_ + (yy - 450) * c
    frame[((cu.abs() < 45) & (cv.abs() < 10)) | ((cu.abs() < 10) & (cv.abs() < 45))] = 1.0
    blob = torch.exp(-((xx - 462) ** 2 + (yy - 462) ** 2) / (2 * 20 ** 2))   # мягкий шар без резкой границы
    return torch.maximum(frame, blob)


def sobel_video(T=48, fps=12):
    w = torch.tensor([[1., 0., -1.], [2., 0., -2.], [1., 0., -1.]])
    kernels = torch.stack([w, w.T])[:, None]                         # (2, 1, 3, 3)
    video = torch.stack([sobel_scene(t, T) for t in range(T)])[:, None]   # (T, 1, 512, 512)
    edges = F.conv2d(video, kernels, padding=1)                     # (T, 2, 512, 512)
    magnitude = edges.pow(2).sum(dim=1).sqrt()
    blob_max = magnitude[:, 420:505, 420:505].max().item()
    print(f'max |grad| on sharp edges: {magnitude.max().item():.2f}, on soft blob: {blob_max:.2f}')

    fig, axes = plt.subplots(2, 2, figsize=(11, 11))
    vmax = edges.abs().max()
    panels = [(video[:, 0], 'input', 'gray', 0, 1),
              (edges[:, 0], 'Sobel x', 'coolwarm', -vmax, vmax),
              (edges[:, 1], 'Sobel y', 'coolwarm', -vmax, vmax),
              (magnitude, 'magnitude', 'magma', 0, magnitude.max())]
    images = []
    for ax, (frames, title, cmap, lo, hi) in zip(axes.flat, panels):
        images.append(ax.imshow(frames[0], cmap=cmap, vmin=lo, vmax=hi))
        ax.set_title(title, fontsize=14)
        ax.axis('off')
    plt.tight_layout()

    def update(t):
        for im, (frames, *_) in zip(images, panels):
            im.set_data(frames[t])

    FuncAnimation(fig, update, frames=T).save(os.path.join(OUT, 'sobel_video.gif'), writer=PillowWriter(fps=fps), dpi=100)
    plt.close(fig)


if __name__ == '__main__':
    conv_sliding()
    conv_channels_anim()
    pgd_2d()
    sobel_video()
    print(sorted(f for f in os.listdir(OUT) if f.endswith('.gif')))
