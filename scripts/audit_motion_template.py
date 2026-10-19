# -*- coding: utf-8 -*-
"""【运动审计模板】从 ep05 抽出，可直接复制为新集脚本。使用方法：
     1) 复制本文件为 <项目根>/_audit/audit_motion_ep0N_v5.py
     2) 重写三张表：MOVES_WHOLE / MOVES_REG / HOLDS
        —— 必须按本集 standalone0N.html 的**实测 onset** 填，不能按 mk() 推算（见 R6 M-76）
     3) 跑：python audit_motion_ep0N_v5.py <帧目录>
   以下为 ep05 的完整实例，三张表可当参照格式。

ep05 v5 语义运动审计（QC-25c 已作废后的运动验收，双向语义审计；克隆 ep04 版）：

   A. 该动的动：抽样动画拍的 0.5s 帧差（整帧 >0.30%；细小矢量按其容器带区测）
   B. 不该动的不动：抽样定格拍的 0.5s 帧差（应 <0.10%）

ep05 拍表（锚点取自 timeline.js 的 cue 起点 mk(sc,i) + standalone05.html 编排；
采样窗口必须跨在动画 onset 上 —— ep02/ep03/ep04 同款窗口混叠教训：
窗口两端都落在换内容之前/之后 = 帧差为 0 的假 FAIL）。

   整帧动(6):  片头入场 0.7 / 十六字逐行 88.6 / 两问对照板 168.8 /
              预告卡1 229.0 / 预告卡2 232.7 / 阿拉伯算式 68.8(见带区表)
   带区动(13): 筹落桌 5.3 / 铜钱空位 10.9 / 方阵逐列 24.5 / 相减两行 32.2 /
              铜钱逐枚 60.9 / 算式逐项 68.8 / 划掉三根 95.0 / 数轴生长 127.0 /
              年代轴节点 162.2 / 数轴箭头 198.1 / 三领域落点 205.8 /
              对角线伸出 223.1 / 记分牌入场 215.0
   静(7):     筹落定 7.0 / 方阵定格 27.0 / 算式定格 70.6 / 十六字定格 92.0 /
              卡达诺卡定格 150.5 / 三领域定格 210.2 / 终场卡定格 235.2

带区测量动机（ep02/03/04 既定判据）：算筹（20x46 竖条）/ 铜钱（r34）/ 年代轴节点 /
三领域落点 chip 都是细小矢量，在整帧 1080x1100 分母下天然 <0.30%，改用容器带区做分母。
onset 依据（逐条核过 standalone05.html）：
  a1-sticks 5.08 入场，两筹落桌 5.13/5.46（0.55s ease-out）
  a1-money  10.63 入场，收/欠两行 10.78/12.18
  a2-matrix 23.55 入场，四列 23.90/24.32/24.74/25.16（0.45s）
  a2-sub    31.81 入场，两行 32.01/32.51（0.5s）；末列归零 35.30
  a3-coins  60.02 入场，13 枚 60.32+i*0.13（0.4s）
  a3-calc   68.01 入场，5 项 68.21+j*0.30（0.35s），结果 69.86
  a4-16     87.75 入场，逐行 88.00+i*0.55（0.55s）
  a4-demo   93.91 入场，划掉三根 cut=94.86（0.6s fade）
  a4-axis   126.23 入场，rightT=126.58 起 1.2s 生长，刻度 rightT+v*0.32（线身实测 y767-786）
  a5-years  161.69? -> 实测 node1 158.33-158.50 点亮（3 帧瞬时），node2 ≈158.55、node3 ≈159.10；
            旧拍 162.2 落在全部节点点完之后的空档（假 FAIL 教训：窗口必须跨在实测 onset 上）
  a6-axis2  197.72 入场，左箭头 mk(6,4)+0.20=197.82（0.7s）
  a6-fields 203.11 入场，三落点实测 205.3/206.7/209.2（0.45s fade，窗口跨点而非段内）
  a7-square 217.63 入场，对角线 mk(7,2)+1.05=223.34（1.0s；v5-r2 延后避开 a⁄b 残影）
  a7-score  214.83 入场（0.6s fade）
"""
import sys

import numpy as np
from PIL import Image

# 帧目录由命令行传入；缺省用 ep05 作范例
D = sys.argv[1] if len(sys.argv) > 1 else "S1_ep05_负数的羞耻/frames_ep05/"
if not D.endswith(('/', '\\')):
    D += '/'
CROP_Y0 = 230  # gray 裁切口（去掉顶部品牌角标上沿 / 底部字幕带 y>1358）


def gray(f):
    return np.asarray(Image.open(D + "frame_%06d.jpg" % f).convert("L")).astype(int)[CROP_Y0:1330, :]


def whole(f):
    return (np.abs(gray(f + 12) - gray(f)) > 10).mean() * 100


def region(f, x0, x1, y0, y1):
    """带区帧差: (x, y) 为屏幕坐标，自动换算成 gray 局部坐标。"""
    a = gray(f); b = gray(f + 12)
    ly0, ly1 = y0 - CROP_Y0, y1 - CROP_Y0
    aa, bb = a[ly0:ly1, x0:x1], b[ly0:ly1, x0:x1]
    return (np.abs(bb - aa) > 10).mean() * 100


MOVES_WHOLE = [("片头入场", 0.7), ("十六字逐行", 88.6), ("两问对照板", 168.8),
               ("预告卡1", 229.0), ("预告卡2", 232.7)]

MOVES_REG = [
    ("筹落桌", 5.3, 80, 840, 600, 1020),        # a1-sticks left80 top600 760x420
    ("铜钱空位", 10.9, 80, 840, 560, 1060),      # a1-money  left80 top560 760x500
    ("方阵逐列", 24.5, 80, 840, 300, 860),       # a2-matrix left80 top300
    ("相减两行", 32.2, 80, 840, 300, 800),       # a2-sub    left80 top300
    ("铜钱逐枚", 60.9, 90, 850, 420, 980),       # a3-coins  left90 top420
    ("算式逐项", 68.8, 80, 840, 560, 1060),      # a3-calc   left80 top560
    ("划掉三根", 95.0, 80, 840, 360, 920),       # a4-demo   left80 top360
    ("数轴生长", 127.2, 60, 890, 760, 795),      # a4-axis 线身 y767-786（实测窄带）
    ("年代轴节点", 158.4, 80, 840, 440, 1000),   # a5-years  node2 onset≈158.55 实测（旧拍 162.2 落空档假 FAIL）
    ("数轴箭头", 198.1, 60, 890, 600, 1020),     # a6-axis2  left60 top600
    ("三领域落点", 206.9, 100, 860, 520, 1080),  # a6-fields node2 onset≈206.72 实测跨点
    ("对角线伸出", 223.6, 190, 890, 420, 1040),  # a7-square left190 top420 700x620
    ("记分牌入场", 215.0, 260, 820, 285, 400),   # a7-score 胶囊 top300 高约 84
]

HOLDS = [("筹落定", 7.0), ("方阵定格", 27.0), ("算式定格", 70.6),
         ("十六字定格", 92.0), ("卡达诺卡定格", 150.5), ("三领域定格", 210.2),
         ("终场卡定格", 235.2)]

bad = 0
print("=== A. 该动的动 (0.5s 帧差, 整帧阈值 >0.30%) ===")
for tag, t in MOVES_WHOLE:
    r = whole(int(round(t * 24)))
    ok = r > 0.30
    bad += 0 if ok else 1
    print("  %-8s t=%6.1f  整帧 ratio=%6.3f%%  %s" % (tag, t, r, "动 OK" if ok else "FAIL 不动!"))

print("=== A2. 细小矢量图: 容器带区内帧差 (阈值 >0.30% of region) ===")
for tag, t, x0, x1, y0, y1 in MOVES_REG:
    r = region(int(round(t * 24)), x0, x1, y0, y1)
    ok = r > 0.30
    bad += 0 if ok else 1
    print("  %-8s t=%6.1f  带区[%4d-%4d,%4d-%4d] ratio=%6.3f%%  %s"
          % (tag, t, x0, x1, y0, y1, r, "动 OK" if ok else "FAIL 不动!"))

print("=== B. 不该动的不动 (0.5s 帧差, 阈值 <0.10%) ===")
for tag, t in HOLDS:
    r = whole(int(round(t * 24)))
    ok = r < 0.10
    bad += 0 if ok else 1
    print("  %-8s t=%6.1f  ratio=%6.3f%%  %s" % (tag, t, r, "静 OK" if ok else "FAIL 在动!"))

print("VERDICT:", "PASS" if bad == 0 else "FAIL %d" % bad)
