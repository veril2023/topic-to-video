# -*- coding: utf-8 -*-
"""【运动审计模板】复制本文件为新集脚本，改三张表即可。

用法：
    1) 复制为 <项目根>/_audit/audit_motion.py
    2) 重写三张表 MOVES_WHOLE / MOVES_REG / HOLDS
       —— 必须按本集 HTML 的**实测 onset** 填，不能按 mk() 推算（见 R6 第 28 条）
    3) 跑：python audit_motion.py <帧目录>

判据（双向，都判 FAIL）：
    A. 该动的动：动画拍的 0.5s（12 帧 @24fps）帧差  > 0.30%
    B. 不该动的不动：定格拍的 0.5s 帧差            < 0.10%

两张表的分工：
    MOVES_WHOLE  整帧占比够大的动画（大的入场、整块换内容）
    MOVES_REG    细小矢量（线条、节点、小图标）——整帧分母下天然 <0.30%，
                 必须用**容器窄带区域**做分母，否则永远误判成"没动"
    HOLDS        设计上应当静止的拍

为什么必须实测 onset：
    mk(scene, idx) 给的是**句起点**，元素动画的真实 onset 由句内子事件决定，
    可能早好几秒。按推算值取样会落在静止段，得到假 FAIL。
    做法：逐帧扫亮像素数找到数值跳变的那一帧，再把采样窗口跨在它上面（±0.25s）。
"""
import sys

import numpy as np
from PIL import Image

# 帧目录由命令行传入
D = sys.argv[1] if len(sys.argv) > 1 else "frames/"
if not D.endswith(('/', '\\')):
    D += '/'

CROP_Y0 = 230   # 裁切口：去掉顶部角标上沿
CROP_Y1 = 1330  # 裁切口：去掉底部字幕带


def gray(f):
    return np.asarray(
        Image.open(D + "frame_%06d.jpg" % f).convert("L")
    ).astype(int)[CROP_Y0:CROP_Y1, :]


def whole(f):
    """整帧帧差（0.5s = 12 帧 @24fps），返回变化像素占比 %。"""
    return (np.abs(gray(f + 12) - gray(f)) > 10).mean() * 100


def region(f, x0, x1, y0, y1):
    """窄带区域帧差。坐标为屏幕坐标，自动换算成裁切后的局部坐标。"""
    a, b = gray(f), gray(f + 12)
    ly0, ly1 = y0 - CROP_Y0, y1 - CROP_Y0
    aa, bb = a[ly0:ly1, x0:x1], b[ly0:ly1, x0:x1]
    return (np.abs(bb - aa) > 10).mean() * 100


# ─── 表 1：整帧能测出来的动画拍 ───────────────────────────────
# (标签, onset 秒)
MOVES_WHOLE = [
    ("片头入场", 0.7),
    # ("××逐行", 88.6),
]

# ─── 表 2：细小矢量，用容器窄带测 ─────────────────────────────
# (标签, onset 秒, x0, x1, y0, y1)
MOVES_REG = [
    ("线条生长", 127.2, 60, 890, 760, 795),   # 线身实测 20px 高 → 用 ±15px 窄带
    # ("节点点亮", 158.4, 80, 840, 440, 1000),
]

# ─── 表 3：设计上应当静止的拍 ─────────────────────────────────
HOLDS = [
    ("落定特写", 7.0),
    # ("终场卡定格", 235.2),
]

bad = 0
print("=== A. 该动的动（0.5s 帧差，整帧 >0.30%）===")
for tag, t in MOVES_WHOLE:
    r = whole(int(round(t * 24)))
    ok = r > 0.30
    bad += 0 if ok else 1
    print("  %-10s t=%6.1f  ratio=%6.3f%%  %s" % (tag, t, r, "动 OK" if ok else "FAIL 不动"))

print("=== A2. 细小矢量（容器窄带内 >0.30%）===")
for tag, t, x0, x1, y0, y1 in MOVES_REG:
    r = region(int(round(t * 24)), x0, x1, y0, y1)
    ok = r > 0.30
    bad += 0 if ok else 1
    print("  %-10s t=%6.1f  带区[%4d-%4d,%4d-%4d] ratio=%6.3f%%  %s"
          % (tag, t, x0, x1, y0, y1, r, "动 OK" if ok else "FAIL 不动"))

print("=== B. 不该动的不动（0.5s 帧差 <0.10%）===")
for tag, t in HOLDS:
    r = whole(int(round(t * 24)))
    ok = r < 0.10
    bad += 0 if ok else 1
    print("  %-10s t=%6.1f  ratio=%6.3f%%  %s" % (tag, t, r, "静 OK" if ok else "FAIL 在动"))

print("VERDICT:", "PASS" if bad == 0 else "FAIL %d" % bad)
sys.exit(0 if bad == 0 else 1)
