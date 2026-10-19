#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""init_ep.py — 建一集的目录骨架

用法：
    python engine/init_ep.py <项目根> <集号> <标题>
    例：python engine/init_ep.py . 03 "为什么井盖是圆的"

产出 <集号>_<标题>/ 目录：
    standalone.html     从 engine/standalone.template.html 复制，只有三个插槽要填
    script_lines.json   台词结构（build_audio.py 的输入）
    ../../../brand.css  不复制，用相对路径 ../brand.css 引用

设计约束：本脚本只做搬运，不生成任何内容。缺什么就留空插槽，
         让 agent 明确知道要填什么，而不是给他一段「看起来像成品」的假内容。
"""
import io
import json
import os
import re
import shutil
import sys


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    root = os.path.abspath(sys.argv[1])
    ep_no = sys.argv[2].zfill(2)
    title = sys.argv[3].strip()

    bj = os.path.join(root, 'brand.json')
    brand = {}
    if os.path.isfile(bj):
        brand = json.load(io.open(bj, encoding='utf-8'))
    series = brand.get('series_name') or '你的系列名'

    mark_path = os.path.join(root, 'brand_mark.html')
    mark = io.open(mark_path, encoding='utf-8').read().strip() if os.path.isfile(mark_path) \
        else '<svg viewBox="0 0 240 240" width="100%" height="100%"><circle cx="120" cy="120" r="104" fill="none" stroke="var(--accent)" stroke-width="10"/></svg>'

    safe = re.sub(r'[\\/:*?"<>|]', '_', title)
    ep_dir = os.path.join(root, '%s_%s' % (ep_no, safe))
    os.makedirs(ep_dir, exist_ok=True)

    tpl_path = os.path.join(root, 'engine', 'standalone.template.html')
    tpl = io.open(tpl_path, encoding='utf-8').read()
    html = (tpl.replace('{{SERIES_NAME}}', series)
               .replace('{{EP_NO}}', ep_no)
               .replace('<!--<<BUG_SVG>>-->', mark)
               # 资源路径统一指到项目根，避免每集复制一份 engine/brand.css 造成多副本漂移
               .replace('href="brand.css"', 'href="../brand.css"')
               .replace('src="engine.js"', 'src="../engine/engine.js"'))
    io.open(os.path.join(ep_dir, 'standalone.html'), 'w', encoding='utf-8', newline='\n').write(html)

    # 台词结构模板：scene / sentences 是 build_audio.py 的唯一输入。
    # 按默认结构（七幕升维）铺 7 幕占位 —— 只给 1 幕的话，粗心的人会真的只写一幕，
    # 出来一个 30 秒的"视频"，然后才发现结构不对。换个结构就自己增删这段。
    _acts = ['奇景', '困局', '动手', '造物', '穿透', '升维', '追问']
    lines = [{"scene": i + 1,
              "sentences": ["（第 %d 幕「%s」的句子，一句一个元素，写完脚本再填）" % (i + 1, name)]}
             for i, name in enumerate(_acts)]
    io.open(os.path.join(ep_dir, 'script_lines.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(lines, ensure_ascii=False, indent=2) + '\n')

    print('OK  集目录：%s' % ep_dir)
    print('     standalone.html   ← 三个插槽：SCENE_CSS / SCENE_HTML / SCENE_JS')
    print('     script_lines.json ← 每幕的句子数组（写完脚本再填）')
    print('')
    print('下一步：')
    print('  1. 写 脚本.md（幕表 + 逐句台词），字数按 5.5 字/秒估算')
    print('  2. 把每幕句子填进 script_lines.json')
    print('  3. python engine/build_audio.py "%s"   # 生成配音 + 句级时间轴' % ep_dir)
    print('  4. 填 standalone.html 的三个插槽（画面）')
    print('  5. node engine/render.js "%s" probe 5 30 60   # 抽帧看图' % ep_dir)
    print('  6. node engine/render.js "%s" full' % ep_dir)
    print('  7. python engine/gen_srt.py "%s" && python engine/mux.py "%s"' % (ep_dir, ep_dir))
    return 0


if __name__ == '__main__':
    sys.exit(main())
