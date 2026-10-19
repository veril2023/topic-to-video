# -*- coding: utf-8 -*-
"""对 ep21-25 逐集迭代：量重心 → 注入 CENTER_DY → 不够则再量。

渲染器 pageHTML 支持读取 CENTER_DY 表（键=图序 1..9，值=viewBox 单位的垂直平移量），
对 .art svg 施加 translateY，使图形区内容重心落到中线 280。
本脚本负责测量与写表，最终由人工/QC 复核。
用法：python _qc/center_pass.py measure|apply
"""
import io
import os
import re
import subprocess
import sys

BASE = 'E:/AI Storage/workbuddy/数学系列视频/outputs'
PY = 'C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'

EPI = [
    (21, 'violet', 'render_xhs_ep21.js'),
    (22, 'sapphire', 'render_xhs_ep22.js'),
    (23, 'indigo', 'render_xhs_ep23.js'),
    (24, 'wine', 'render_xhs_ep24.js'),
    (25, 'emerald', 'render_xhs_ep25.js'),
]

ANCHOR = 'const NAMES = ['
CSS_ANCHOR = '.art svg { overflow: visible; }'


def measure(ep, pal):
    d = os.path.join(BASE, 'xhs_ep%d' % ep, pal)
    out = subprocess.run([PY, os.path.join(BASE, '_qc', 'xhs_center.py'), '--dir', d],
                         capture_output=True, text=True, encoding='utf-8')
    res = {}
    for line in out.stdout.splitlines()[2:]:
        parts = line.split()
        if len(parts) < 7:
            continue
        name = parts[0]
        idx = int(name[:2])
        dv = parts[6]          # "<vb>vb / <pct>%<gap>@<at>"
        dy = float(dv.split('/')[0].strip().replace('vb', ''))
        res[idx] = dy
    return res


CSS_OLD = '.art svg { width:100%; height:auto; max-height:100%; display:block; }'
CSS_NEW = '.art svg { width:100%; height:auto; max-height:100%; display:block; transform:translateY(var(--dy,0%)); }'
HTML_OLD = '<div class="art">${s.art}</div>'
HTML_NEW = '<div class="art" style="--dy:${(CENTER_DY[s.idx] || 0).toFixed(2)}%">${s.art}</div>'


def apply(ep, js, dys):
    p = os.path.join(BASE, 'xhs_ep%d' % ep, js)
    with io.open(p, 'r', encoding='utf-8') as f:
        t = f.read()

    # 1) CSS：让 art svg 支持垂直平移
    if CSS_OLD in t:
        t = t.replace(CSS_OLD, CSS_NEW, 1)
    elif CSS_NEW not in t:
        print('     !! CSS anchor missing')

    # 2) HTML：按图序注入 --dy
    if HTML_OLD in t:
        t = t.replace(HTML_OLD, HTML_NEW, 1)
    elif HTML_NEW not in t:
        print('     !! HTML anchor missing')

    # 3) CENTER_DY 表（vb 单位 → 百分比 = vb / 560 * 100 = vb / 5.6）
    pcts = {k: round(v / 5.6, 2) for k, v in dys.items()}
    row = ', '.join('%d: %.2f' % (k, v) for k, v in sorted(pcts.items()))
    if 'const CENTER_DY' in t:
        t = re.sub(r'const CENTER_DY = \{[^}]*\};',
                   'const CENTER_DY = { %s };   // 图形区垂直平移（%% of viewBox 高，负=向上），由 _qc/xhs_center.py 实测重心写定' % row,
                   t)
    else:
        table = ('const CENTER_DY = { %s };   // 图形区垂直平移（%% of viewBox 高，负=向上），由 _qc/xhs_center.py 实测重心写定\n\n'
                 % row)
        t = t.replace(ANCHOR, table + ANCHOR, 1)

    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(t)
    return p


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'measure'
    for ep, pal, js in EPI:
        if mode == 'reset':
            # 清零平移量，回到原始坐标，用于重新测量
            zero = {i: 0.0 for i in range(1, 10)}
            print('ep%-3d reset → %s' % (ep, apply(ep, js, zero)))
            continue
        dys = measure(ep, pal)
        print('ep%-3d %s' % (ep, {k: round(v, 1) for k, v in sorted(dys.items())}))
        if mode == 'apply':
            print('     →', apply(ep, js, dys))