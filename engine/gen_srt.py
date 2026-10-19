#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_srt.py — 从 timeline.js 生成外挂字幕

用法：
    python engine/gen_srt.py <集目录> [--max 19]

说明：
    画面里的字幕是烧进去的（由 engine.js 排版），这个 srt 是给平台上传用的。
    两者的换行宽度特意不同：画面里受安全区限制只能 17 字一行；
    srt 由播放器自己排版，19 字更接近自然阅读节奏，不会出现过度碎行。

    只有一句话在画面里被标了 nosub（因为画面本身就是那句话），这里仍然照常输出，
    否则用户关掉画面字幕后会发现漏了一句。
"""
import io
import json
import os
import re
import sys


def ts(x):
    x = max(0.0, x)
    h = int(x // 3600)
    m = int((x % 3600) // 60)
    s = int(x % 60)
    ms = int(round((x - int(x)) * 1000))
    if ms == 1000:
        ms, s = 0, s + 1
    return '%02d:%02d:%02d,%03d' % (h, m, s, ms)


def wrap(text, max_len):
    """按标点优先断行，超长再硬切，最多两行（第三行会被播放器挡住）。"""
    parts = re.findall(r'[^，。？！、：；]+[，。？！、：；]?', text) or [text]
    lines, cur = [], ''
    for p in parts:
        while len(p) > max_len:
            if cur:
                lines.append(cur)
                cur = ''
            lines.append(p[:max_len])
            p = p[max_len:]
        if len(cur + p) <= max_len:
            cur += p
        else:
            if cur:
                lines.append(cur)
            cur = p
    if cur:
        lines.append(cur)
    while len(lines) > 2:
        lines = [lines[0], ''.join(lines[1:])]
    return lines or ['']


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    ep_dir = os.path.abspath(args[0])
    max_len = 19
    if '--max' in sys.argv:
        max_len = int(sys.argv[sys.argv.index('--max') + 1])

    tl = os.path.join(ep_dir, 'timeline.js')
    if not os.path.isfile(tl):
        print('找不到 %s（先跑 build_audio.py）' % tl)
        return 2

    s = io.open(tl, encoding='utf-8-sig').read()
    data = json.loads(s[s.find('{'):s.rfind('}') + 1])
    subs = data.get('subtitles', [])
    if not subs:
        print('timeline.js 里没有 subtitles')
        return 2

    out = []
    for i, cu in enumerate(subs, 1):
        out.append(str(i))
        out.append(ts(cu['start']) + ' --> ' + ts(cu['end']))
        out.append('\n'.join(wrap(cu['text'], max_len)))
        out.append('')

    name = os.path.basename(ep_dir)
    m = re.match(r'(\d+)_(.*)', name)
    fname = ('第%s集-%s' % (m.group(1), m.group(2)) if m else name) + '.srt'
    path = os.path.join(ep_dir, fname)
    io.open(path, 'w', encoding='utf-8-sig', newline='\n').write('\n'.join(out))
    print('OK  %s  (%d 条)' % (path, len(subs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
