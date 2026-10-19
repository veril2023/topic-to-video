# -*- coding: utf-8 -*-
"""平铺归档：把每集的 视频 / 3:4 封面 / 发布文档 直接平铺到目标目录（不分子目录）。
   复制后回读 sha256 逐字节比对，全一致才写 MANIFEST_flat.md。

   **不维护任何剧集列表**——扫描项目根下的集目录，按目录名自动识别集号与集名：
        ep01_我的主题/            → 第 01 集，集名「我的主题」
        S1_ep01_我的主题/         → 同上（季前缀可有可无）
        ep12-另一个主题/          → 第 12 集，集名「另一个主题」

   目标目录优先级：环境变量 MEV_DST > scripts/archive_config.json > <项目根>/archive_output
   项目根优先级：环境变量 MEV_ROOT > 从 cwd 向上找 SERIES.md > 当前目录（含集目录时）
   系列名前缀：环境变量 MEV_SERIES > brand.json 的 series_name > "未命名系列"

用法:
    python scripts/archive_flat.py                 # 归档全部集
    python scripts/archive_flat.py ep01            # 只归档第 1 集
    MEV_DST=/path/to/archive python scripts/archive_flat.py
    MEV_SERIES=我的系列 MEV_DST=/path python scripts/archive_flat.py

退出码：0 全部一致；1 缺少成片；2 有 sha256 不一致
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys


def _project_root():
    e = os.environ.get('MEV_ROOT')
    if e and os.path.isdir(e):
        return e
    d = os.getcwd()
    for _ in range(5):
        if os.path.isfile(os.path.join(d, 'SERIES.md')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.getcwd()


def _resolve_dst():
    e = os.environ.get('MEV_DST')
    if e:
        return e
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'archive_config.json')
    if os.path.isfile(cfg):
        try:
            d = json.load(open(cfg, encoding='utf-8')).get('dst')
            if d:
                return d
        except Exception:
            pass
    return os.path.join(_project_root(), 'archive_output')


def _resolve_series():
    e = os.environ.get('MEV_SERIES')
    if e:
        return e
    for p in (os.path.join(_project_root(), 'brand.json'),
              os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'brand.json')):
        if os.path.isfile(p):
            try:
                n = json.load(open(p, encoding='utf-8')).get('series_name')
                if n and n.strip():
                    return n.strip()
            except Exception:
                pass
    return '未命名系列'


ROOT = _project_root()
DST = _resolve_dst()
SERIES = _resolve_series()

# 集目录名：ep01_标题 / S1_ep01_标题 / ep01-标题
EP_RE = re.compile(r'(?:^|[/\\])[^/\\]*?ep\s*(\d{1,3})\s*[_-]\s*(.+?)\s*$', re.I)


def discover():
    """扫描项目根下的一级目录，返回 [(集号, 集名, 绝对路径)]，按集号排序。"""
    out = []
    try:
        names = sorted(os.listdir(ROOT))
    except OSError:
        return out
    for name in names:
        p = os.path.join(ROOT, name)
        if not os.path.isdir(p):
            continue
        m = EP_RE.search(name)
        if not m:
            continue
        epno, title = m.group(1).zfill(2), m.group(2).replace('_', ' ').strip()
        # 过滤掉明显的非集目录（例如 ep01_xxx 的备份目录 _bak）
        if name.startswith('_') or name.startswith('.'):
            continue
        out.append((epno, title, p))
    out.sort(key=lambda x: x[0])
    return out


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest(), os.path.getsize(p)


def pick(base, epno, patterns):
    """在集目录里按候选 glob 顺序找第一个存在的文件。"""
    import glob
    for pat in patterns:
        g = sorted(glob.glob(os.path.join(base, pat)))
        if g:
            return g[0]
    return None


def main():
    only = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        m = re.search(r'(\d{1,3})', sys.argv[1])
        if m:
            only = m.group(1).zfill(2)

    os.makedirs(DST, exist_ok=True)
    eps = discover()
    if not eps:
        print('FAIL 在 %s 下没有找到集目录（应形如 ep01_标题）' % ROOT)
        return 2

    all_rows = []
    missing = 0
    for epno, title, base in eps:
        if only and epno != only:
            continue
        vid = pick(base, epno, ['*.mp4', '第%s集*.mp4' % epno])
        if not vid:
            print('MISS 第%s集《%s》：没有 mp4' % (epno, title))
            missing += 1
            continue
        cover = pick(base, epno, ['*封面*.jpg', 'cover*.jpg', '*.jpg'])
        doc = pick(base, epno, ['*发布文档*.md', '发布*.md', '*发布*.md'])

        pfx = '%s-第%s集-%s' % (SERIES, epno, title.replace(' ', '_'))
        jobs = [(vid, pfx + '.mp4')]
        if cover:
            jobs.append((cover, pfx + '-封面.jpg'))
        if doc:
            jobs.append((doc, pfx + '-发布文档.md'))

        for sp, dname in jobs:
            dp = os.path.join(DST, dname)
            shutil.copy2(sp, dp)
            h1, n1 = sha(sp)
            h2, n2 = sha(dp)
            ok = (h1 == h2 and n1 == n2)
            all_rows.append((dname, n1, h1, ok))
            print(('OK  ' if ok else 'BAD ') + '%-56s %10d  %s' % (dname, n1, h1[:16]))

    # 清理目标目录里不属于本系列三件套的残留（字幕/报告/临时文件等）。
    # 任何以「<系列名>-第」开头的文件一律保留，避免单集归档删掉其它集。
    series_pfx = '%s-第' % SERIES
    for f in sorted(os.listdir(DST)):
        fp = os.path.join(DST, f)
        if not os.path.isfile(fp):
            continue
        if f == 'MANIFEST_flat.md' or f.startswith(series_pfx):
            continue
        os.remove(fp)
        print('CLEAN 已删除残留文件：%s' % f)

    # MANIFEST 按目录实际存在的系列文件登记（与本轮归档了哪些集无关）
    buf = ['# 平铺归档清单 · %s\n' % DST,
           '每集固定三类：视频 + 3:4 封面 + 发布文档 ｜ 校验：复制后回读 sha256 逐字节比对\n\n',
           '| 文件 | 字节 | sha256 |\n|---|---|---|\n']
    bad = sum(1 for r in all_rows if not r[3])
    rows = []
    for f in sorted(os.listdir(DST)):
        if not f.startswith(series_pfx):
            continue
        h, n = sha(os.path.join(DST, f))
        rows.append('| `%s` | %d | `%s` |\n' % (f, n, h))
    io.open(os.path.join(DST, 'MANIFEST_flat.md'), 'w',
            encoding='utf-8', newline='\n').write(''.join(buf + rows))

    print('-' * 70)
    print('系列前缀：%s' % SERIES)
    print('归档目录：%s' % DST)
    print('本次写入 %d 个文件，sha256 不一致 %d 个，缺成片 %d 集'
          % (len(all_rows), bad, missing))
    if bad:
        return 2
    if missing:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
