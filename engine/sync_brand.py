#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_brand.py — 把 brand.json 编译成品牌资源

产出两个文件（都在项目根）：
  brand.css        颜色变量 + 角标尺寸，被每集的 standalone.html 用 <link> 引入
  brand_mark.html  角标 SVG 片段，由 init_ep.py 填进页面

为什么要编成 CSS 而不是运行时读 JSON：
  浏览器里的页面通过 http:// 加载，读不到项目根的 JSON 文件；而把颜色硬编码进
  每一集，一旦改品牌就要改所有集，必然漂移。编成 CSS 后，改品牌只需重跑本脚本，
  所有集同时生效。

用法：
    python engine/sync_brand.py [项目根]
    不给项目根则从当前工作目录向上找 brand.json
"""
import io
import json
import os
import sys


def project_root(argv):
    if len(argv) > 1 and os.path.isdir(argv[1]):
        return os.path.abspath(argv[1])
    d = os.getcwd()
    for _ in range(6):
        if os.path.isfile(os.path.join(d, 'brand.json')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.getcwd()


def hex_rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    root = project_root(sys.argv)
    bj = os.path.join(root, 'brand.json')
    if not os.path.isfile(bj):
        print('找不到 %s —— 先复制 brand.example.json 为 brand.json 并填写' % bj)
        return 2

    b = json.load(io.open(bj, encoding='utf-8'))

    accent = b.get('accent', '#E0A44B')
    accent_alt = b.get('accent_alt', '#4E8FA6')
    bg = b.get('bg_gradient') or ['#0E1016', '#1B2028']
    card = b.get('card_face', '#151A22')
    text = b.get('text_primary', '#F2F0EA')
    tr, tg, tb = hex_rgb(text)

    corner = b.get('corner_mark') or {}
    bug_left = int(corner.get('left', 60))
    bug_top = int(corner.get('top', 220))
    logo_px = int(corner.get('logo_px', 57))
    name_px = int(corner.get('name_px', 33))

    css = """/* 由 engine/sync_brand.py 从 brand.json 生成，不要手改。
   改品牌请改 brand.json 后重跑： python engine/sync_brand.py */
:root{
  --accent: %(accent)s;
  --accent-alt: %(accent_alt)s;
  --bg0: %(bg0)s;
  --bg1: %(bg1)s;
  --card: %(card)s;
  --text: %(text)s;
  --text-2: rgba(%(tr)d,%(tg)d,%(tb)d,.55);
  --text-3: rgba(%(tr)d,%(tg)d,%(tb)d,.38);
  --line: rgba(%(tr)d,%(tg)d,%(tb)d,.10);
}
#bug{left:%(bug_left)dpx !important;top:%(bug_top)dpx !important}
#bug svg{width:%(logo_px)dpx;height:%(logo_px)dpx}
#bug .bt{font-size:%(name_px)dpx !important}
""" % dict(accent=accent, accent_alt=accent_alt, bg0=bg[0], bg1=bg[1], card=card,
           text=text, tr=tr, tg=tg, tb=tb,
           bug_left=bug_left, bug_top=bug_top, logo_px=logo_px, name_px=name_px)

    out_css = os.path.join(root, 'brand.css')
    io.open(out_css, 'w', encoding='utf-8', newline='\n').write(css)

    # ---- 角标 SVG ----
    logo_file = (b.get('logo_svg_file') or '').strip()
    if logo_file:
        cand = logo_file if os.path.isabs(logo_file) else os.path.join(root, logo_file)
        if os.path.isfile(cand):
            svg = io.open(cand, encoding='utf-8').read()
            # 外部 SVG 可能带自己的 width/height，统一成 1:1 交给 CSS 控制尺寸
            svg = svg.replace('<svg', '<svg class="mark" width="100%" height="100%"', 1)
        else:
            print('⚠ logo_svg_file 指向的文件不存在：%s —— 退回中性几何角标' % cand)
            logo_file = ''
    if not logo_file:
        # 中性几何角标：一个圆环 + 一道弧，不含任何具体品牌语义
        svg = ('<svg viewBox="0 0 240 240" width="100%" height="100%" aria-hidden="true">'
               '<circle cx="120" cy="120" r="104" fill="none" stroke="var(--accent)" stroke-width="10"/>'
               '<path d="M62 150 A72 72 0 0 1 178 150" fill="none" stroke="var(--accent)" '
               'stroke-width="14" stroke-linecap="round" opacity=".55"/>'
               '<circle cx="120" cy="120" r="12" fill="var(--accent)"/></svg>')

    out_mark = os.path.join(root, 'brand_mark.html')
    io.open(out_mark, 'w', encoding='utf-8', newline='\n').write(svg + '\n')

    print('OK  %s' % out_css)
    print('OK  %s%s' % (out_mark, '（自备 logo）' if logo_file else '（中性几何角标）'))
    print('    series=%s  accent=%s  bg=%s→%s' % (b.get('series_name', '?'), accent, bg[0], bg[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
