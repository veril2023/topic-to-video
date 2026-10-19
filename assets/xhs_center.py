# -*- coding: utf-8 -*-
"""XHS 视觉重心分析：对已渲染 PNG 做行投影，量化「图形区内容是否居中」。

判据（全部实测，不靠目测）：
  · 内容首行 / 末行        —— 内容实际占据的纵向区间
  · 上留白 / 下留白        —— 内容区间到 art 区上下边界的空白
  · 加权重心               —— 按每行墨迹量加权的 y 均值，与 art 区中线比
  · 最大空白断层           —— 内容中间连续无墨迹的最大行数及位置
用法：python xhs_center.py <png> [<png> ...]
      python xhs_center.py --dir <输出目录>   # 批量扫该目录全部 PNG
"""
import os
import sys

from PIL import Image

# art svg 在页面上的纵向范围（MEASURE=1 实测，九张一致）
ART_TOP, ART_BOT = 591, 1179
# 背景参考取 art 区左上角 40×40（无内容区）
BG_SAMPLE = (40, 40)


def analyze(path):
    """墨迹判定：不与背景做固定色比对（背景有 radial/linear 渐变，固定基准会整行误判），
    改用「暖金色 或 高亮度」双路——本系列所有内容色（amber 金 / bone 骨白 / 浅色标签）
    都落在这两路里，深色渐变底不会命中。"""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if h < ART_BOT:
        return None

    rows = []
    for y in range(ART_TOP, ART_BOT):
        line = im.crop((0, y, w, y + 1)).getdata()
        n = 0
        for r, g, b in line:
            lum = (r * 299 + g * 587 + b * 114) // 1000
            warm = r > 140 and (r - b) > 40 and (r - g) > 15   # 琥珀金
            bright = lum > 165                                 # 骨白 / 浅色字
            if warm or bright:
                n += 1
        rows.append(n)

    total = sum(rows)
    if total == 0:
        return dict(name=os.path.basename(path), empty=True)

    first = next(i for i, v in enumerate(rows) if v > 2)
    last = len(rows) - 1 - next(i for i, v in enumerate(reversed(rows)) if v > 2)

    # 加权重心（行号 → art 区像素坐标）
    mid = (ART_TOP + ART_BOT) / 2.0
    cen = sum((ART_TOP + i) * v for i, v in enumerate(rows)) / total

    # 最大空白断层
    gap = cur = 0
    gap_at = 0
    for i, v in enumerate(rows):
        if v <= 2:
            cur += 1
            if cur > gap:
                gap, gap_at = cur, ART_TOP + i - cur
        else:
            cur = 0

    span = ART_BOT - ART_TOP
    # 页面像素 → viewBox 单位（art svg 高 588px 对应 viewBox 560，缩放 1.05）
    K = 560.0 / span

    def vb(v):
        return round((v - ART_TOP) * K, 1)

    cen_vb = (cen - ART_TOP) * K
    first_vb = (ART_TOP + first - ART_TOP) * K
    last_vb = (ART_TOP + last - ART_TOP) * K

    # ★ 目标是「内容块几何中心对齐 art 区中线 280」，不是墨迹加权重心——
    #   加权重心会被底部大字/粗线拉偏，导致块居中但观感下沉（或上浮）。
    #   实测：某集封面用加权重心对齐后块跑到偏上 85px，下方空 181px。
    geo_mid = (first_vb + last_vb) / 2.0
    dy_raw = 280 - geo_mid
    # 夹紧：平移后内容必须仍在 [8, 552] 内，否则会撞 F1 越界
    dy = max(-(first_vb - 8), min(dy_raw, 552 - last_vb))
    return dict(
        name=os.path.basename(path), empty=False,
        first=ART_TOP + first, last=ART_TOP + last,
        first_vb=round(first_vb, 1), last_vb=round(last_vb, 1),
        top_pad=first, bot_pad=span - last,
        center=round(cen, 1), mid=round(mid, 1),
        dev=round(cen - mid, 1), dev_pct=round((cen - mid) / span * 100, 1),
        cen_vb=round(cen_vb, 1), dy_vb=round(dy, 1),
        geo_mid=round(geo_mid, 1), dy_raw=round(dy_raw, 1),
        dy_pct=round(dy / 560 * 100, 2),
        gap=gap, gap_at=gap_at, gap_pct=round(gap / span * 100, 1),
    )


def main():
    args = sys.argv[1:]
    if args and args[0] == '--dir':
        d = args[1]
        files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.png')]
    else:
        files = args
    rows = []
    for p in files:
        r = analyze(p)
        if r:
            rows.append(r)
    print(f'{"图":<16}{"内容区间(vb)":<16}{"上留":<7}{"下留":<7}{"重心vb":<9}{"偏心%":<8}{"建议平移":<11}{"最大断层"}')
    print('-' * 96)
    for r in rows:
        if r.get('empty'):
            print(f'{r["name"]:<16}EMPTY')
            continue
        flag = ' <<偏下' if r['dev_pct'] > 8 else (' <<偏上' if r['dev_pct'] < -8 else '')
        print(f'{r["name"]:<16}{str(r["first_vb"]) + "-" + str(r["last_vb"]):<16}'
              f'{r["top_pad"]:<7}{r["bot_pad"]:<7}{r["cen_vb"]:<9}'
              f'{r["dev_pct"]:<8}{str(r["dy_vb"]) + "vb / " + str(r["dy_pct"]) + "%":<11}'
              f'{str(r["gap"]) + "@" + str(r["gap_at"])}{flag}')


if __name__ == '__main__':
    main()