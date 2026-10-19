#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_test.py — 改动后跑一遍，确认基础零件没坏

用法：
    python scripts/smoke_test.py

它只测**不需要外部依赖**的部分：不调 TTS、不启浏览器、不需要 ffmpeg。
所以在一台刚 clone 下来、还没装 node 和 Chrome 的机器上也能跑。

测什么：
    T1  gate0.py 四种输入 → 该发两张表的发两张表，该拦的拦住
    T2  init_ep.py → 建出 7 幕骨架，script_lines.json 是合法 JSON
    T3  sync_brand.py → 产出 brand.css 且含配色变量
    T4  静态扫描 → 无 shell=True / os.system / 裸 except / 写死的绝对路径
    T5  文档引用 → SKILL.md / README.md 里提到的仓库内路径都真实存在

不测什么：渲染出片、TTS 合成、质检门的判据正确性。
那些要靠真实跑一集（见 README「快速开始」），自动测只会测出假绿。

退出码：0 全过；1 有 FAIL。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

_rows = []


def add(ok, name, detail=''):
    _rows.append((ok, name, detail))
    print('%s  %-34s %s' % ('PASS' if ok else 'FAIL', name, detail))


def run(args, cwd=None):
    """跑一个子进程，返回 (returncode, 合并输出)。"""
    p = subprocess.Popen([PY] + args, cwd=cwd or ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0]
    if not isinstance(out, str):
        out = out.decode('utf-8', 'replace')
    return p.returncode, out


# ---------------------------------------------------------------- T1 gate0
def t1_gate0():
    cases = [
        # (输入, 必须出现的串, 必须不出现的串)
        ('为什么井盖是圆的',
         ['[3] 三问', '[4] 输入契约', '| 8 | 配音方案', '✓ 把上面 [3] 和 [4] 两张表原样发给用户'],
         ['主题太粗']),
        ('量子力学',
         ['主题太粗', '降颗粒度'],
         ['✓ 把上面 [3] 和 [4] 两张表原样发给用户']),
        ('给我讲讲养生偏方治病',
         ['D 级风险', '不要开工'],
         ['✓ 把上面 [3] 和 [4] 两张表原样发给用户']),
        ('帮我按《数学之美》做一系列视频',
         ['[3] 三问', '[4] 输入契约'],
         []),
    ]
    for topic, must, must_not in cases:
        rc, out = run(['scripts/gate0.py', topic])
        miss = [m for m in must if m not in out]
        bad = [m for m in must_not if m in out]
        detail = ''
        if rc != 0:
            detail = '退出码 %d' % rc
        elif miss:
            detail = '缺：' + ' / '.join(miss)
        elif bad:
            detail = '不该出现：' + ' / '.join(bad)
        add(rc == 0 and not miss and not bad, 'T1 gate0 · "%s"' % topic[:14], detail)


# --------------------------------------------------------------- T2 init_ep
def t2_init_ep():
    tmp = tempfile.mkdtemp(prefix='ttv_smoke_')
    try:
        rc, out = run(['engine/init_ep.py', tmp, '3', '为什么井盖是圆的'])
        if rc != 0:
            add(False, 'T2 init_ep 建骨架', '退出码 %d' % rc)
            return
        ep = os.path.join(tmp, '03_为什么井盖是圆的')
        if not os.path.isdir(ep):
            ep = [os.path.join(tmp, d) for d in os.listdir(tmp) if d.startswith('03_')][0]
        ok_files = all(os.path.isfile(os.path.join(ep, f))
                       for f in ('standalone.html', 'script_lines.json'))
        add(ok_files, 'T2 init_ep 建骨架', '两个文件' if ok_files else '缺文件')

        lines = json.load(io.open(os.path.join(ep, 'script_lines.json'), encoding='utf-8'))
        scenes = [x for x in lines if isinstance(x, dict) and 'sentences' in x]
        # 只铺 1 幕的话，粗心的人会做出一条 30 秒的"视频"还能过所有格式门
        add(len(scenes) == 7, 'T2 init_ep 铺 7 幕', '实际 %d 幕' % len(scenes))

        html = io.open(os.path.join(ep, 'standalone.html'), encoding='utf-8').read()
        for slot in ('SCENE_CSS', 'SCENE_HTML', 'SCENE_JS'):
            if slot not in html:
                add(False, 'T2 三个插槽齐全', '缺 ' + slot)
                return
        add(True, 'T2 三个插槽齐全', 'SCENE_CSS / SCENE_HTML / SCENE_JS')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------ T3 sync_brand
def t3_sync_brand():
    tmp = tempfile.mkdtemp(prefix='ttv_brand_')
    try:
        shutil.copy(os.path.join(ROOT, 'brand.example.json'),
                    os.path.join(tmp, 'brand.json'))
        rc, out = run(['engine/sync_brand.py', tmp])
        if rc != 0:
            add(False, 'T3 sync_brand 编品牌', '退出码 %d：%s' % (rc, out.strip()[:80]))
            return
        css_path = os.path.join(tmp, 'brand.css')
        ok = os.path.isfile(css_path)
        body = io.open(css_path, encoding='utf-8').read() if ok else ''
        has_var = '--' in body and ':' in body
        add(ok and has_var, 'T3 sync_brand 编品牌',
            'brand.css %d 字节，含 CSS 变量' % len(body) if ok and has_var
            else ('brand.css 缺失' if not ok else 'brand.css 里没有 CSS 变量'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -------------------------------------------------------------- T4 静态扫描
_BAD = [
    (re.compile(r'\bshell\s*=\s*True'), 'shell=True'),
    (re.compile(r'\bos\.system\s*\('), 'os.system()'),
    (re.compile(r'^\s*except\s*:', re.M), '裸 except:'),
    (re.compile(r"rm\s+-rf\s+/"), 'rm -rf /'),
]


def _walk(sub, exts):
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, sub)):
        dirnames[:] = [d for d in dirnames if d not in ('__pycache__', 'node_modules')]
        for f in filenames:
            # 本文件自己就写着这些坏模式的字面量，扫自己会永远红
            if f.endswith(exts) and f != 'smoke_test.py':
                yield os.path.join(dirpath, f)


def t4_static():
    hits = []
    for path in list(_walk('engine', ('.py', '.js'))) + list(_walk('scripts', ('.py', '.js'))):
        text = io.open(path, encoding='utf-8', errors='replace').read()
        for pat, label in _BAD:
            if pat.search(text):
                hits.append('%s: %s' % (os.path.relpath(path, ROOT), label))
    add(not hits, 'T4 无危险调用', '；'.join(hits) if hits else 'shell / system / 裸 except 均无')

    # 绝对路径不是一律禁止：找 ffmpeg / chrome 这类外部工具时，必须有一排
    # 跨平台兜底候选（shutil.which 找不到时的备胎，且都能用 MEV_* 环境变量覆盖）。
    # 但「候选列表」和「写死依赖」在文本上看不出区别，所以按文件判：
    # 一个有 cands 列表 + which/platform/环境变量的文件，算解析器，不查；
    # 剩下的文件里出现绝对路径，才是真的写死。
    abs_hits, resolvers = [], []
    win_abs = re.compile(r'["\'][A-Za-z]:[\\/]')
    posix_abs = re.compile(r'["\'](/Users/|/home/|/opt/|/usr/)')
    _searchy = re.compile(r'shutil\.which|process\.platform|MEV_|cands')
    for path in list(_walk('engine', ('.py', '.js'))) + list(_walk('scripts', ('.py', '.js'))):
        text = io.open(path, encoding='utf-8', errors='replace').read()
        is_resolver = bool(_searchy.search(text)) and 'cands' in text
        if is_resolver:
            resolvers.append(os.path.relpath(path, ROOT))
            continue
        for i, line in enumerate(text.splitlines(), 1):
            s = line.lstrip()
            if s.startswith('#') or s.startswith('//'):
                continue
            if win_abs.search(line) or posix_abs.search(line):
                abs_hits.append('%s:%d' % (os.path.relpath(path, ROOT), i))
    add(not abs_hits, 'T4 无写死绝对路径',
        '；'.join(abs_hits[:5]) if abs_hits
        else '%d 个路径解析器按候选列表处理' % len(resolvers))


# ------------------------------------------------------------ T5 文档引用
_DOC = ['SKILL.md', 'README.md']


def t5_doc_refs():
    missing = []
    link = re.compile(r'\]\((?!https?://|#)([^)#]+)\)')
    for doc in _DOC:
        text = io.open(os.path.join(ROOT, doc), encoding='utf-8').read()
        cands = set(link.findall(text))
        cands |= {m.group(1) for m in re.finditer(
            r'`((?:engine|scripts|references|structures|templates|extras)/[^`\s]+)`', text)}
        for c in cands:
            c = c.strip()
            if not c or any(ch in c for ch in '*<>$'):
                continue
            p = os.path.join(ROOT, c.replace('/', os.sep))
            if os.path.exists(p):
                continue
            # 文档里说的「把 xxx.example.json 复制成 xxx.json」不算死链：
            # 那个文件本来就该由用户复制出来，仓库里只有 example
            stem, ext = os.path.splitext(p)
            if ext and os.path.exists(stem + '.example' + ext):
                continue
            missing.append('%s → %s' % (doc, c))
    add(not missing, 'T5 文档里的路径都存在',
        '；'.join(sorted(set(missing))[:6]) if missing else 'SKILL.md / README.md 零死链')


def main():
    print('=' * 78)
    print('topic-to-video  自测（不依赖 ffmpeg / Chrome / TTS）')
    print('  仓库：%s' % ROOT)
    print('  解释器：%s' % PY)
    print('=' * 78)
    for fn in (t1_gate0, t2_init_ep, t3_sync_brand, t4_static, t5_doc_refs):
        try:
            fn()
        except Exception as e:
            add(False, fn.__name__, '%s: %s' % (type(e).__name__, e))

    bad = [r for r in _rows if not r[0]]
    print('-' * 78)
    print('%d 项检查，%d 通过，%d 失败' % (len(_rows), len(_rows) - len(bad), len(bad)))
    if bad:
        print('失败项：')
        for _, n, d in bad:
            print('  - %s  %s' % (n, d))
        return 1
    print('全部通过。这只说明零件没坏，出片能力还要看 engine/selfcheck.py。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
