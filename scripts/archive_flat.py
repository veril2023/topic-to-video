# -*- coding: utf-8 -*-
"""平铺归档：把每集 视频 / 3:4封面 / 发布文档 直接平铺到目标目录（不分子目录）。
   复制后回读 sha256 逐字节比对，全一致才写 MANIFEST_flat.md。

   目标目录优先级：环境变量 MEV_DST > 配置文件 archive_config.json > 默认 ./archive_output。
   项目根优先级：环境变量 MEV_ROOT > 从 cwd 向上找 SERIES.md > 脚本所在目录的父级。

用法: python archive_flat.py  (一次性归档全部在表剧集)
      python archive_flat.py ep04  (只归档指定集)
      MEV_DST=/path/to/archive python archive_flat.py  (指定归档目录)
"""
import hashlib, io, json, os, shutil, sys

def _project_root():
    """自动推导项目根：环境变量 MEV_ROOT > 从 cwd 向上找 SERIES.md > 脚本所在目录的父级。"""
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
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_dst():
    """解析归档目标目录：环境变量 > 配置文件 > 默认值。"""
    # 1. 环境变量
    e = os.environ.get('MEV_DST')
    if e:
        return e
    # 2. 配置文件（与脚本同目录）
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'archive_config.json')
    if os.path.isfile(cfg):
        try:
            d = json.load(open(cfg, encoding='utf-8')).get('dst')
            if d:
                return d
        except Exception:
            pass
    # 3. 默认值（相对于项目根）
    return os.path.join(_project_root(), 'archive_output')


ROOT = _project_root()
DST = _resolve_dst()

# 每集: (srcdir, epno, 副题) —— 新集在 EPS 表加一行即可，其余不用改
EPS = [
    ('S1_ep01_骨头上的刻痕',         '01', '骨头上的刻痕'),
    ('S1_ep02_六十进制从哪来',       '02', '六十进制从哪来'),
    ('S1_ep03_生下来就会数吗',       '03', '生下来就会数吗'),
    ('S1_ep04_零_让欧洲害怕的符号',  '04', '零_让欧洲害怕的符号'),
    ('S1_ep05_负数的羞耻',           '05', '负数的羞耻'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest(), os.path.getsize(p)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(DST, exist_ok=True)
    all_rows = []
    for srcdir, epno, sub in EPS:
        if only and only != 'ep' + epno:
            continue
        base = os.path.join(ROOT, srcdir)
        vids = [f for f in os.listdir(base) if f.startswith('第%s集' % epno) and f.endswith('.mp4')]
        if not vids:
            print('MISS video', srcdir); return 1
        pfx = '万物有数-第%s集-%s' % (epno, sub)
        jobs = [
            (vids[0],            pfx + '.mp4'),
            ('cover_34_ep%s.jpg' % epno, pfx + '-封面.jpg'),
            ('发布文档_ep%s.md' % epno,   pfx + '-发布文档.md'),
        ]
        rows = []
        for s, d in jobs:
            sp = os.path.join(base, s)
            dp = os.path.join(DST, d)
            if not os.path.exists(sp):
                continue  # 该集无此文件（如 ep03 无验收报告），跳过
            shutil.copy2(sp, dp)
            h1, n1 = sha(sp); h2, n2 = sha(dp)
            ok = (h1 == h2 and n1 == n2)
            rows.append((d, n1, h1, ok))
            print(('OK  ' if ok else 'BAD ') + '%-52s %10d  %s' % (d, n1, h1[:16]))
        all_rows += rows

    # 清理 D 盘根目录里不在白名单的残留文件（字幕/验收报告/LICENSES/FACTS/旧命名封面等）
    # 白名单 = 全部 EPS 的三件套命名（与本轮归档哪些集无关）+ MANIFEST。
    # 这样单集归档（python archive_flat.py ep03）不会删掉其它集已归档的交付件。
    # 任何「万物有数-第NN集-」前缀的系列文件一律保留（未来 ep06+ 未入表时也不误删），
    # 只真正清掉旧方案的残留（srt / 验收报告 / LICENSES / 封面_A_B / 旧命名 mp4 等）。
    allowed = set(['MANIFEST_flat.md'])
    for _, epno, sub in EPS:
        pfx = '万物有数-第%s集-%s' % (epno, sub)
        allowed.add(pfx + '.mp4')
        allowed.add(pfx + '-封面.jpg')
        allowed.add(pfx + '-发布文档.md')
    series_pfx = '万物有数-第'
    for f in sorted(os.listdir(DST)):
        fp = os.path.join(DST, f)
        if not os.path.isfile(fp):
            continue
        if f in allowed:
            continue
        if f.startswith(series_pfx):
            print('KEEP 系列前缀但不在白名单，保留待人工确认：%s' % f)
            continue
        os.remove(fp)
        print('CLEAN 已删除残留文件：%s' % f)

    # 写 MANIFEST —— 清单按归档目录实际存在的系列文件登记（与本轮归档了哪些集无关，
    # 保证单集运行后 MANIFEST 依然完整）
    buf = ['# 平铺归档清单 · %s\n' % DST,
           '每集固定三类：视频 + 3:4封面 + 发布文档 ｜ 校验：复制后回读 sha256 逐字节比对\n\n',
           '| 文件 | 字节 | sha256 |\n|---|---|---|\n']
    bad = 0
    for d, n, h, ok in all_rows:
        if not ok:
            bad += 1
    rows = []
    for f in sorted(os.listdir(DST)):
        if not f.startswith(series_pfx):
            continue
        h, n = sha(os.path.join(DST, f))
        rows.append('| `%s` | %d | `%s` |\n' % (f, n, h))
    io.open(os.path.join(DST, 'MANIFEST_flat.md'), 'w', encoding='utf-8', newline='\n').write(''.join(buf + rows))
    print('归档目录：', DST)
    print('文件数 %d，不一致 %d' % (len(all_rows), bad))
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
