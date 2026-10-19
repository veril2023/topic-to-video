#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfcheck.py — 环境自检

在开工前跑一次。它回答唯一一个问题：**这台机器能不能真的产出 mp4。**

为什么必须做这一步：
    本技能不是纯文档包，它要调用 ffmpeg、headless Chrome、Node。
    如果执行环境不具备这些能力（比如只有网页版对话、没有本地文件系统），
    那么无论写得多好的脚本都产不出视频。此时正确做法是**立刻告知用户换工具**，
    而不是花几十分钟生成一份"看起来完整"的脚本然后卡在渲染。

用法：
    python engine/selfcheck.py [项目根]

退出码：0 全部通过（可能有无害警告）；1 有致命项缺失
"""
import io
import json
import os
import shutil
import subprocess
import sys

OK, WARN, FAIL = '  OK  ', ' WARN ', ' FAIL '
rows = []


def add(level, name, detail=''):
    rows.append((level, name, detail))


def which_any(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def find_chrome():
    cands = [os.environ.get('MEV_CHROME')]
    home = os.path.expanduser('~')
    roots = [os.path.join(home, '.cache', 'ms-playwright'),
             os.path.join(home, '.cache', 'hyperframes', 'chrome'),
             os.path.join(home, 'AppData', 'Local', 'ms-playwright')]
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            for d in os.listdir(root):
                for rel in (('chrome-win64', 'chrome.exe'),
                            ('chrome-linux', 'chrome'),
                            ('chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'),
                            ('chrome-headless-shell-win64', 'chrome-headless-shell.exe'),
                            ('chrome-headless-shell-linux64', 'chrome-headless-shell')):
                    cands.append(os.path.join(root, d, *rel))
        except OSError:
            pass
    sysd = {
        'win32': [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                  r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                  r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                  r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'],
        'darwin': ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                   '/Applications/Chromium.app/Contents/MacOS/Chromium'],
    }.get(sys.platform, ['/usr/bin/google-chrome', '/usr/bin/chromium',
                         '/usr/bin/chromium-browser'])
    cands += sysd
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()

    # ---- 1. Python ----
    v = sys.version_info
    add(OK if v >= (3, 8) else FAIL, 'Python',
        '%d.%d.%d  %s' % (v.major, v.minor, v.micro, sys.executable))

    # ---- 2. Node ----
    node = which_any(['node'])
    if node:
        try:
            out = subprocess.run([node, '-v'], capture_output=True, text=True, timeout=20)
            add(OK, 'Node.js', out.stdout.strip() + '  ' + node)
        except Exception as e:                          # noqa: BLE001
            add(WARN, 'Node.js', '存在但无法执行：%s' % e)
    else:
        add(FAIL, 'Node.js', '未安装 —— 渲染需要它。装：https://nodejs.org')

    # ---- 3. puppeteer-core ----
    if node:
        probe = ("try{require.resolve('puppeteer-core');console.log('yes')}"
                 "catch(e){console.log('no')}")
        found = False
        for cwd in (root, os.path.join(root, 'engine'), os.getcwd()):
            try:
                r = subprocess.run([node, '-e', probe], capture_output=True,
                                   text=True, timeout=30, cwd=cwd,
                                   env=dict(os.environ, NODE_PATH=os.environ.get('NODE_PATH', '')))
                if r.stdout.strip() == 'yes':
                    found = True
                    break
            except Exception:                           # noqa: BLE001
                pass
        add(OK if found else FAIL, 'puppeteer-core',
            '已安装' if found else '未安装 —— 在项目根执行：npm i puppeteer-core')

    # ---- 4. ffmpeg / ffprobe ----
    for name in ('ffmpeg', 'ffprobe'):
        p = os.environ.get('MEV_' + name.upper()) or which_any([name]) \
            or (r'C:\ffmpeg\bin\%s.exe' % name if os.path.isfile(r'C:\ffmpeg\bin\%s.exe' % name) else None)
        if p and os.path.isfile(p):
            try:
                out = subprocess.run([p, '-version'], capture_output=True, text=True, timeout=20)
                add(OK, name, out.stdout.splitlines()[0][:70])
            except Exception as e:                      # noqa: BLE001
                add(WARN, name, '存在但无法执行：%s' % e)
        else:
            add(FAIL, name, '未安装 —— 装：winget install Gyan.FFmpeg / brew install ffmpeg')

    # ---- 5. Chrome ----
    ch = find_chrome()
    add(OK if ch else FAIL, 'Chrome/Chromium',
        ch if ch else '未找到 —— npx playwright install chromium 或装 Google Chrome')

    # ---- 6. 字体（中文渲染的前提）----
    sysname = sys.platform
    if sysname == 'win32':
        add(OK, '中文字体', 'Windows 自带微软雅黑/宋体')
    elif sysname == 'darwin':
        add(OK, '中文字体', 'macOS 自带苹方/宋体')
    else:
        has = subprocess.run(['fc-list', ':lang=zh'], capture_output=True, text=True) \
            if which_any(['fc-list']) else None
        n = len([l for l in (has.stdout or '').splitlines() if l.strip()]) if has else 0
        add(OK if n else WARN, '中文字体',
            '%d 个中文字体' % n if n else '未检测到中文字体，画面里的中文会变成方框。装：sudo apt install fonts-noto-cjk')

    # ---- 7. 配音后端（两条路，有一条通就能出片）----
    key = os.environ.get('MINIMAX_API_KEY')
    src = '环境变量 MINIMAX_API_KEY'
    if not key:
        for p in (os.path.join(root, 'minimax_key.txt'),):
            if os.path.isfile(p):
                key = io.open(p, encoding='utf-8').read().strip()
                src = p
                break

    edge_ok = False
    try:
        import importlib.util
        edge_ok = importlib.util.find_spec('edge_tts') is not None
    except Exception:                               # noqa: BLE001
        edge_ok = False

    if key and edge_ok:
        add(OK, '配音后端', 'MiniMax 已配置（%s）+ Edge TTS 免费可用，任选其一' % src)
    elif key:
        add(OK, '配音后端', 'MiniMax 已配置（%s）。想要免费方案：pip install edge-tts 后加 --provider edge' % src)
    elif edge_ok:
        add(OK, '配音后端', 'Edge TTS 免费可用（无需 key），用 --provider edge 或把 brand.json 的 tts.provider 设为 edge')
    else:
        add(WARN, '配音后端',
            '两条路都没通：没有 MINIMAX_API_KEY，也没装 edge-tts。'
            '装免费的：pip install edge-tts，然后 --provider edge；'
            '或者自己生成 audio/scene_N.mp3 后用 --no-tts')

    # ---- 8. 项目结构 ----
    need = ['brand.json', 'engine/engine.js', 'engine/render.js',
            'engine/build_audio.py', 'engine/mux.py', 'engine/gen_srt.py']
    miss = [n for n in need if not os.path.isfile(os.path.join(root, n))]
    add(OK if not miss else WARN, '项目结构',
        '完整' if not miss else '缺少：' + ', '.join(miss)
        + ('（brand.json 可由 brand.example.json 复制）' if 'brand.json' in miss else ''))

    # ---- 9. 写权限 ----
    try:
        t = os.path.join(root, '.selfcheck.tmp')
        io.open(t, 'w', encoding='utf-8').write('x')
        os.remove(t)
        add(OK, '写权限', root)
    except Exception as e:                              # noqa: BLE001
        add(FAIL, '写权限', '无法写入 %s：%s' % (root, e))

    # ---- 输出 ----
    print('=' * 78)
    print('环境自检  ' + root)
    print('=' * 78)
    for lv, n, d in rows:
        print('%s %-18s %s' % (lv, n, d))
    print('-' * 78)

    fatal = [r for r in rows if r[0] == FAIL]
    warns = [r for r in rows if r[0] == WARN]
    if fatal:
        print('结论：无法出片。有 %d 项致命缺失：' % len(fatal))
        for _, n, _ in fatal:
            print('  - ' + n)
        print('\n请先补齐上述项目，或换一台具备完整命令行环境（可写文件 + 可跑 node/python）的机器。')
        print('如果当前只能用网页版对话（不能写文件、不能跑命令），本技能无法产出 mp4，')
        print('它最多只能交付脚本与分镜，请改用 Claude Code / Codex / Qoder / Trae 等本地工具。')
        return 1
    print('结论：可以出片。%s' % ('（%d 项警告，见上）' % len(warns) if warns else '全部通过。'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
