# -*- coding: utf-8 -*-
"""QC-27 钩子密度门（v6 新增，2026-10-19）

判定（全部 PASS 才放行）：
  A1  最长无钩子间隔 <= MAX_GAP（默认 25s）
  A2  前 30s 内 >= 1 次提问
  A3  片头结束后 BET_WIN 秒内出现母题赌注句

钩子定义：文本含 ？/? 或 以 吗/呢 结尾
（nosub 的 cue 不参与，因为观众看不到它）

用法：
  python qc27_hooks.py ../ep01_你的主题/timeline.js
  python qc27_hooks.py <timeline.js> --gap 20 --early 30
退出码：0 全 PASS，1 有 FAIL
"""
import json
import os
import re
import sys

MAX_GAP = 25.0
EARLY = 30.0
BET_WIN = 3.0

BET_KEY = re.compile(r"记一分|记 1 分|加一分|加 1 分|我给.{0,8}记|给.{0,6}记分|这一分|下注|押")


def load_timeline(path):
    s = open(path, encoding='utf-8-sig').read()
    s = s[s.find('{'): s.rfind('}') + 1]
    return json.loads(s)


def is_hook(text):
    """钩子判定：中文里 吗/呢 几乎只用于疑问句，出现在句中即算。
    用 in 而非 endswith——转述式提问（…你能减去一个更大的数吗。）也是钩子，
    而 endswith 会漏掉 吗，…／呢 这类后接标点的写法。"""
    t = text.strip()
    if not t:
        return False
    return ('\uff1f' in t) or ('?' in t) or ('\u5417' in t) or ('\u5462' in t)


def fmt(sec):
    return '%.1fs' % sec


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print('用法: python qc27_hooks.py <timeline.js> [--gap 25] [--early 30]')
        return 2
    tl_path = args[0]
    if not os.path.isfile(tl_path):
        print('FAIL 找不到 timeline.js: %s' % tl_path)
        return 2

    gap_max = MAX_GAP
    early = EARLY
    for a in sys.argv[1:]:
        if a.startswith('--gap='):
            gap_max = float(a.split('=', 1)[1])
        if a.startswith('--early='):
            early = float(a.split('=', 1)[1])

    d = load_timeline(tl_path)
    total = float(d.get('total', 0))
    intro = float(d.get('intro', 1.5))
    subs = [x for x in d.get('subtitles', []) if not x.get('nosub')]

    if not subs:
        print('FAIL timeline 里没有可上屏的 cue')
        return 1

    hooks = [x for x in subs if is_hook(x.get('text', ''))]
    hook_ts = [float(x['start']) for x in hooks]

    marks = [0.0] + hook_ts + [total]
    gaps = [(marks[i + 1] - marks[i], marks[i], marks[i + 1]) for i in range(len(marks) - 1)]
    worst, w_from, w_to = max(gaps, key=lambda z: z[0])

    early_hooks = [t for t in hook_ts if t < early]

    bet_cue = None
    for x in subs:
        t0 = float(x['start'])
        if intro - 0.4 <= t0 <= intro + BET_WIN and BET_KEY.search(x.get('text', '')):
            bet_cue = x
            break

    print('=' * 62)
    print('QC-27 钩子密度门   %s' % os.path.basename(tl_path))
    print('总时长 %s  片头 %s  有效 cue %d 条' % (fmt(total), fmt(intro), len(subs)))
    print('-' * 62)

    fails = []

    ok1 = worst <= gap_max
    print('[%s] A1 最长无钩子间隔 %s (%.1f -> %.1f)  上限 %s'
          % ('PASS' if ok1 else 'FAIL', fmt(worst), w_from, w_to, fmt(gap_max)))
    if not ok1:
        fails.append('A1')

    ok2 = len(early_hooks) >= 1
    print('[%s] A2 前 %s 内提问 %d 次  要求 >=1'
          % ('PASS' if ok2 else 'FAIL', fmt(early), len(early_hooks)))
    if not ok2:
        fails.append('A2')

    ok3 = bet_cue is not None
    if ok3:
        bt = bet_cue.get('text', '')
        print('[PASS] A3 赌注句 @%s  %s' % (fmt(float(bet_cue['start'])),
                                             bt[:26] + ('...' if len(bt) > 26 else '')))
    else:
        print('[FAIL] A3 片头后 %s 内未找到母题赌注句（关键词：记一分/我给X记/下注）' % fmt(BET_WIN))
        fails.append('A3')

    print('-' * 62)
    print('钩子 %d 条：%s' % (len(hook_ts), ', '.join(fmt(t) for t in hook_ts)))
    gs = sorted([g for g, _, _ in gaps], reverse=True)[:3]
    print('最大三段空窗：%s' % ' / '.join(fmt(g) for g in gs))
    print('=' * 62)

    if fails:
        print('QC-27 结果：FAIL（%s）—— 回脚本环节补钩子，不要进渲染' % ' '.join(fails))
        return 1
    print('QC-27 结果：PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
