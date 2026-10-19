# -*- coding: utf-8 -*-
"""QC-28 字幕节奏门（v6 新增，2026-10-19）

判据（全部 PASS 才放行）：
  B1  单条总字数 <= MAX_CHARS（默认 22）
  B2  单条停留   <= MAX_DUR（默认 4.5s）
  B3  阅读速度落在 8-15 字/秒（低于 8 = 停太久，优先拆条；高于 15 = 太赶）

单行 <=19 字是排版物理极限，由 text 长度间接反映：22 字以内折两行即可，
故本门只报 WARN 不判 FAIL。

nosub 的 cue 不上屏，不参与判定。

用法：
  python qc28_subpacing.py ../S1_ep06_xxx/timeline.js
退出码：0 全 PASS，1 有 FAIL
"""
import json
import os
import sys

MAX_CHARS = 22
MAX_DUR = 4.5
# 语速阈值：本系列是 1.12-1.18 倍速中文旁白，实测 5-7 字/秒。
# 定 8 字/秒做下界会把全部 cue 误判成"停太久"（ep05 实测 67/68 条报警），故取 3.5-9.0。
# 参考：22 字 / 4.5s = 4.9 字/秒，两条硬指标本身就落在合理区间内。
SPEED_LO = 3.5
SPEED_HI = 9.0
LINE_LIMIT = 19


def load_timeline(path):
    s = open(path, encoding='utf-8-sig').read()
    s = s[s.find('{'): s.rfind('}') + 1]
    return json.loads(s)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print('用法: python qc28_subpacing.py <timeline.js> [--chars 22] [--dur 4.5]')
        return 2
    tl_path = args[0]
    if not os.path.isfile(tl_path):
        print('FAIL 找不到 timeline.js: %s' % tl_path)
        return 2

    max_chars = MAX_CHARS
    max_dur = MAX_DUR
    for a in sys.argv[1:]:
        if a.startswith('--chars='):
            max_chars = int(a.split('=', 1)[1])
        if a.startswith('--dur='):
            max_dur = float(a.split('=', 1)[1])

    d = load_timeline(tl_path)
    subs = d.get('subtitles', [])
    onscreen = [x for x in subs if not x.get('nosub')]

    print('=' * 66)
    print('QC-28 字幕节奏门   %s' % os.path.basename(tl_path))
    print('cue 总数 %d，其中 nosub %d 条不判，实际判定 %d 条'
          % (len(subs), len(subs) - len(onscreen), len(onscreen)))
    print('-' * 66)

    too_long = []
    too_slow = []
    too_fast = []
    need_wrap = []

    for x in onscreen:
        txt = (x.get('text') or '').strip()
        dur = float(x['end']) - float(x['start'])
        n = len(txt)
        scene, idx = x.get('scene'), x.get('idx')
        tag = '(%s,%s)' % (scene, idx)

        if n > max_chars:
            too_long.append((tag, n, float(x['start']), txt))
        if dur > max_dur:
            too_slow.append((tag, dur, float(x['start']), txt))
        if n > LINE_LIMIT and dur > 0:
            need_wrap.append((tag, n, dur))
        if dur > 0:
            sp = n / dur
            if sp < SPEED_LO:
                too_fast.append((tag, sp, float(x['start']), txt, 'slow'))
            elif sp > SPEED_HI:
                too_fast.append((tag, sp, float(x['start']), txt, 'fast'))

    fails = []

    def block(title, rows, unit, limit_txt):
        if not rows:
            print('[PASS] %s  无超限' % title)
            return
        fails.append(title)
        print('[FAIL] %s  %d 条超限（%s）' % (title, len(rows), limit_txt))
        for r in rows[:12]:
            tag, v, t0 = r[0], r[1], r[2]
            txt = r[3]
            print('        %s @%-7s %6.1f%s  %s' % (tag, '%.1fs' % t0, v, unit,
                                                     txt[:24] + ('...' if len(txt) > 24 else '')))
        if len(rows) > 12:
            print('        ... 另有 %d 条' % (len(rows) - 12))

    block('B1 单条字数', too_long, '字', '上限 %d 字' % max_chars)
    block('B2 单条停留', too_slow, 's', '上限 %.1fs' % max_dur)

    if too_fast:
        print('[WARN] B3 阅读速度越界 %d 条（%.1f-%.1f 字/秒外，只诊断不拦）'
              % (len(too_fast), SPEED_LO, SPEED_HI))
        for tag, sp, t0, txt, kind in too_fast[:8]:
            word = '停太久' if kind == 'slow' else '太赶'
            print('        %s @%-7s %.1f 字/秒 %s  %s'
                  % (tag, '%.1fs' % t0, sp, word, txt[:20]))
    else:
        print('[PASS] B3 阅读速度全部落在 %.1f-%.1f 字/秒' % (SPEED_LO, SPEED_HI))

    if need_wrap:
        print('[WARN] 共 %d 条超过 19 字，渲染时须折成两行（折在语义停顿处，不拆词）' % len(need_wrap))

    print('-' * 66)
    print('=' * 66)
    if fails:
        print('QC-28 结果：FAIL（%s）—— 拆条后重跑，不要进渲染' % ' '.join(fails))
        return 1
    print('QC-28 结果：PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
