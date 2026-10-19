# -*- coding: utf-8 -*-
"""progress.py —— 15 步进度跟踪，解决"跨会话继续做不知道跑到哪了"。

用法：
    python progress.py init <集目录> <集号> <标题>     # 从模板生成本集 PROGRESS.json
    python progress.py show <集目录>                   # 打印进度表（每次续做先跑这个）
    python progress.py done <集目录> <步骤号> [备注]    # 标记某步完成
    python progress.py gate <集目录> <门名> PASS|FAIL   # 记录门禁结果
    python progress.py note <集目录> <文字>             # 追加一条全局备注
    python progress.py html <集目录> [输出路径]         # 生成可视化看板 PROGRESS.html

门名可用：QC-27 / QC-28 / QC-29（对应 gates 里的键，也可写完整键名）
"""
import json
import os
import shutil
import sys
from datetime import date

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'templates', 'PROGRESS.template.json')
FNAME = 'PROGRESS.json'

GATE_ALIAS = {
    'QC-27': 'QC-27_hooks',
    'QC-28': 'QC-28_subpacing',
    'QC-29': 'QC-29_epcheck',
}


def pj(d):
    return os.path.join(d, FNAME)


def load(d):
    p = pj(d)
    if not os.path.isfile(p):
        print('FAIL 找不到 %s，先跑 init' % p)
        sys.exit(1)
    return json.load(open(p, encoding='utf-8'))


def save(d, data):
    data['updated'] = date.today().isoformat()
    json.dump(data, open(pj(d), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def cmd_init(d, ep, title):
    if os.path.isfile(pj(d)):
        print('已存在 %s，未覆盖' % pj(d))
        return
    tpl = json.load(open(TEMPLATE, encoding='utf-8'))
    tpl['ep'] = ep
    tpl['title'] = title
    tpl['started'] = date.today().isoformat()
    json.dump(tpl, open(pj(d), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('已创建 %s' % pj(d))


def cmd_show(d):
    t = load(d)
    print('=' * 64)
    print('ep%s《%s》  结构 %s  变体 %s  升维 %s  开始 %s'
          % (t['ep'], t['title'], t.get('structure', 'seven-act'),
             t.get('variant', '?'), t.get('dimension', '?'), t.get('started', '?')))
    print('比分 %s → %s' % (t.get('score_before') or '?', t.get('score_after') or '（未结算）'))
    print('-' * 64)
    for s in t['steps']:
        mark = {'done': '[x]', 'in_progress': '[~]', 'pending': '[ ]', 'blocked': '[!]'}.get(
            s.get('status', 'pending'), '[ ]')
        gate = ('  <%s>' % s['gate']) if s.get('gate') else ''
        note = ('  ' + s['note']) if s.get('note') else ''
        print('%s %2d %-24s%s%s' % (mark, s['n'], s['name'], gate, note))
    print('-' * 64)
    g = t.get('gates') or {}
    if g:
        print('门禁：' + '  '.join('%s=%s' % (k, v if v is not None else '—') for k, v in g.items()))
    if t.get('facts_pending'):
        print('FACTS 待补：' + '; '.join(t['facts_pending']))
        print('  ⚠️ 有未清事实 → 按 QC-20 不许进分镜')
    if t.get('notes'):
        print('备注：' + t['notes'])
    done = sum(1 for s in t['steps'] if s.get('status') == 'done')
    print('=' * 64)
    print('进度 %d/15' % done)


def cmd_done(d, n, note):
    t = load(d)
    for s in t['steps']:
        if str(s['n']) == str(n):
            s['status'] = 'done'
            if note:
                s['note'] = note
            t['current_step'] = int(n) + 1
            save(d, t)
            print('第 %s 步标记完成，当前应做第 %d 步' % (n, t['current_step']))
            return
    print('FAIL 没有第 %s 步' % n)


def cmd_gate(d, name, result):
    t = load(d)
    key = GATE_ALIAS.get(name, name)
    t.setdefault('gates', {})[key] = result.upper()
    save(d, t)
    print('%s = %s' % (key, result.upper()))


def cmd_note(d, text):
    t = load(d)
    t['notes'] = (t.get('notes') or '') + (' | ' if t.get('notes') else '') + text
    save(d, t)
    print('已追加备注')


TPL = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:linear-gradient(180deg,#0D1118,#1A2130);color:#F5F0E6;
 font-family:"Microsoft YaHei",system-ui,sans-serif;min-height:100vh;padding:40px 32px}
.wrap{max-width:860px;margin:0 auto}
h1{font-size:28px;font-weight:600;letter-spacing:.02em}
h1 em{font-style:normal;color:#E8A33D}
.meta{margin-top:10px;color:rgba(245,240,230,.55);font-size:14px;line-height:1.9}
.meta b{color:#E8A33D;font-weight:500}
.bar{margin:26px 0 8px;height:10px;background:rgba(245,240,230,.10);border-radius:5px;overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#E8A33D,#F2B75E);border-radius:5px}
.pct{font-size:13px;color:rgba(245,240,230,.55)}
ul{list-style:none;margin-top:26px}
li{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:8px;
 border:1px solid rgba(245,240,230,.08);margin-bottom:7px;font-size:15px;background:rgba(20,24,36,.55)}
li i{font-style:normal;width:16px;text-align:center;color:rgba(245,240,230,.35)}
li b{font-weight:500;color:rgba(245,240,230,.45);width:22px;font-size:13px}
li .t{flex:1}
li .g{font-size:11px;color:#E8A33D;border:1px solid rgba(232,163,61,.4);
 border-radius:20px;padding:2px 9px;white-space:nowrap}
li .n{font-size:12px;color:rgba(245,240,230,.45);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
li.done{border-color:rgba(232,163,61,.45);background:rgba(232,163,61,.10)}
li.done i{color:#E8A33D}
li.done .t{color:rgba(245,240,230,.65)}
li.in_progress{border-color:rgba(63,169,140,.5);background:rgba(63,169,140,.10)}
li.in_progress i{color:#3FA98C}
li.blocked{border-color:rgba(226,75,74,.5);background:rgba(226,75,74,.10)}
li.blocked i{color:#E24B4A}
.gates{margin-top:26px;display:flex;gap:10px;flex-wrap:wrap}
.badge{font-size:13px;padding:6px 14px;border-radius:20px;border:1px solid rgba(245,240,230,.16);color:rgba(245,240,230,.6)}
.badge.ok{color:#3FA98C;border-color:rgba(63,169,140,.55);background:rgba(63,169,140,.10)}
.badge.bad{color:#E24B4A;border-color:rgba(226,75,74,.55);background:rgba(226,75,74,.10)}
.foot{margin-top:34px;font-size:12px;color:rgba(245,240,230,.35);line-height:1.9}
.warn{margin-top:20px;padding:12px 16px;border-left:3px solid #E8A33D;
 background:rgba(232,163,61,.08);font-size:14px;color:#F2B75E;border-radius:0 6px 6px 0}
</style></head><body><div class="wrap">
<h1>__EP__ <em>《__NAME__》</em></h1>
<div class="meta">结构 <b>__ST__</b> ｜ 变体 <b>__VARIANT__</b> ｜ 升维 <b>__DIM__</b> ｜ 开始 __START__ ｜ 更新 __UPD__<br>
母题比分 <b>__S1__</b> → <b>__S2__</b></div>
<div class="bar"><i style="width:__PCT__%"></i></div>
<div class="pct">进度 __DONE__ / __TOTAL__（__PCT__%）</div>
__WARN__
<ul>__ROWS__</ul>
<div class="gates">__GATES__</div>
<div class="foot">本页是快照，更新进度后重跑 <code>python progress.py html &lt;集目录&gt;</code> 刷新。<br>
数据来源：__SRC__</div>
</div></body></html>"""


def cmd_html(d, out):
    t = load(d)
    total = len(t['steps'])
    done = sum(1 for s in t['steps'] if s.get('status') == 'done')
    pct = int(round(done * 100.0 / total)) if total else 0

    rows = []
    for s in t['steps']:
        st = s.get('status', 'pending')
        icon = {'done': '●', 'in_progress': '◐', 'pending': '○', 'blocked': '▲'}.get(st, '○')
        gate = ('<span class="g">%s</span>' % s['gate']) if s.get('gate') else ''
        note = ('<span class="n">%s</span>' % s['note']) if s.get('note') else ''
        rows.append('<li class="%s"><i>%s</i><b>%02d</b><span class="t">%s</span>%s%s</li>'
                    % (st, icon, s['n'], s['name'], gate, note))

    g = t.get('gates') or {}
    gates = ''.join('<span class="badge %s">%s %s</span>'
                    % ('ok' if v == 'PASS' else 'bad' if v == 'FAIL' else 'idle',
                       k, v if v else '未跑')
                    for k, v in g.items())

    warn = ''
    if t.get('facts_pending'):
        warn = ('<div class="warn">FACTS 还有 %d 条待补：%s<br>'
                '按 QC-20，未清的事实不许进分镜。</div>'
                % (len(t['facts_pending']), '; '.join(t['facts_pending'])))

    html = (TPL.replace('__TITLE__', 'ep%s %s' % (t['ep'], t['title']))
               .replace('__EP__', 'ep%s' % t['ep'])
               .replace('__NAME__', t['title'])
               .replace('__ST__', str(t.get('structure') or 'seven-act'))
               .replace('__VARIANT__', str(t.get('variant') or '—'))
               .replace('__DIM__', str(t.get('dimension') or '—'))
               .replace('__START__', str(t.get('started') or '—'))
               .replace('__UPD__', str(t.get('updated') or '—'))
               .replace('__S1__', str(t.get('score_before') or '—'))
               .replace('__S2__', str(t.get('score_after') or '未结算'))
               .replace('__PCT__', str(pct))
               .replace('__DONE__', str(done))
               .replace('__TOTAL__', str(total))
               .replace('__WARN__', warn)
               .replace('__ROWS__', ''.join(rows))
               .replace('__GATES__', gates)
               .replace('__SRC__', pj(d)))

    out = out or os.path.join(d, 'PROGRESS.html')
    open(out, 'w', encoding='utf-8').write(html)
    print('已生成看板 %s' % out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    act, d = sys.argv[1], os.path.abspath(sys.argv[2])
    if not os.path.isdir(d):
        print('FAIL 目录不存在: %s' % d)
        return 2
    if act == 'init':
        if len(sys.argv) < 5:
            print('用法: init <集目录> <集号> <标题>')
            return 2
        cmd_init(d, sys.argv[3], sys.argv[4])
    elif act == 'show':
        cmd_show(d)
    elif act == 'done':
        cmd_done(d, sys.argv[3], ' '.join(sys.argv[4:]))
    elif act == 'gate':
        cmd_gate(d, sys.argv[3], sys.argv[4])
    elif act == 'note':
        cmd_note(d, ' '.join(sys.argv[3:]))
    elif act == 'html':
        cmd_html(d, sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
