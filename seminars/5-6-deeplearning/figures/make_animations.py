"""Анимации для семинаров 5–6. Запуск: python figures/make_animations.py"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle
import torch
from torchvision.ops import box_iou

OUT = os.path.dirname(os.path.abspath(__file__))
GREEN, RED, GRAY, OBJECT_FILL = '#009E73', '#D55E00', '#8a8a8a', '#E8E8E8'


def n_boxes(n):
    # 1 бокс, 2–4 бокса, 5+ боксов
    if n % 10 == 1 and n % 100 != 11:
        return f'{n} бокс'
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f'{n} бокса'
    return f'{n} боксов'


# ---------------------------------------------------------------------------
# NMS по шагам: взять лучший, погасить пересекающиеся с ним, повторить
def nms_steps(boxes, iou_thr):
    status = ['pending'] * len(boxes)
    states = [(status.copy(), f'{n_boxes(len(boxes))} до NMS, по убыванию score')]
    for i in range(len(boxes)):
        if status[i] != 'pending':
            continue
        iou = box_iou(boxes[i:i + 1], boxes)[0]
        hit = [j for j in range(len(boxes)) if status[j] == 'pending' and j != i and iou[j] > iou_thr]
        shown = status.copy()
        shown[i] = 'current'
        for j in hit:
            shown[j] = 'hit'
        states.append((shown, f'оставляем бокс #{i}; IoU > {iou_thr} с ним у {len(hit)} боксов'))
        status[i] = 'kept'
        for j in hit:
            status[j] = 'suppressed'
        states.append((status.copy(), f'гасим {n_boxes(len(hit))}'))
    states.append((status.copy(), f'после NMS: {n_boxes(status.count("kept"))}'))
    return states


def nms_animation(iou_thr=0.5):
    gen = torch.Generator().manual_seed(4)
    objects = torch.tensor([[10., 12., 46., 70.], [52., 10., 90., 40.], [40., 50., 86., 88.]])
    boxes, scores = [], []
    for k, obj in enumerate(objects):
        size = (obj[2:] - obj[:2]).repeat(2)
        for j in range(5):
            boxes.append(obj + (torch.rand(4, generator=gen) - 0.5) * 0.3 * size * (j > 0))
            scores.append(0.93 - 0.06 * k - 0.11 * j + 0.04 * torch.rand(1, generator=gen).item())
    boxes, scores = torch.stack(boxes), torch.tensor(scores)
    order = scores.argsort(descending=True)
    boxes, scores = boxes[order], scores[order]
    states = nms_steps(boxes, iou_thr)

    style = {'pending': dict(edgecolor=GRAY, linewidth=1.2, linestyle='-'),
             'current': dict(edgecolor=GREEN, linewidth=3.5, linestyle='-'),
             'hit': dict(edgecolor=RED, linewidth=2, linestyle='--'),
             'kept': dict(edgecolor=GREEN, linewidth=2.5, linestyle='-')}
    fig, (ax, ax_list) = plt.subplots(1, 2, figsize=(11, 5.6), gridspec_kw={'width_ratios': [1.5, 1]})

    def update(t):
        status, caption = states[t]
        ax.clear()
        ax_list.clear()
        for obj in objects:
            x1, y1, x2, y2 = obj.tolist()
            ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor=OBJECT_FILL, edgecolor='none'))
        for i, (x1, y1, x2, y2) in enumerate(boxes.tolist()):
            if status[i] != 'suppressed':
                ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, **style[status[i]]))
        ax.set_xlim(0, 96)
        ax.set_ylim(96, 0)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(caption, fontsize=12)
        colors = {'pending': GRAY, 'current': GREEN, 'hit': RED, 'kept': GREEN, 'suppressed': '#cccccc'}
        for i, s in enumerate(scores.tolist()):
            text = f'#{i:<2}  score {s:.2f}' + {'kept': '  ✓', 'current': '  ✓', 'suppressed': '  ✗', 'hit': '  ✗'}.get(status[i], '')
            ax_list.text(0.05, 1 - (i + 1) / (len(scores) + 1), text, fontsize=11, family='monospace',
                         color=colors[status[i]], weight='bold' if status[i] in ('current', 'kept') else 'normal')
        ax_list.axis('off')
        ax_list.set_title('боксы по убыванию score', fontsize=12)

    frames = list(range(len(states))) + [len(states) - 1] * 3
    FuncAnimation(fig, update, frames=frames).save(os.path.join(OUT, 'nms.gif'), writer=PillowWriter(fps=0.8), dpi=70)
    plt.close(fig)


if __name__ == '__main__':
    nms_animation()
    print(sorted(f for f in os.listdir(OUT) if f.endswith('.gif')))
