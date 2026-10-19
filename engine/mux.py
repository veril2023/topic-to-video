#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mux.py — 逐帧图 + 混音音轨 → 交付 MP4

用法：
    python engine/mux.py <集目录>
    python engine/mux.py <集目录> --cover 7.0        # 顺便在指定秒抽一张封面候选

编码参数（这些值不是随便定的）：
    -crf 18            视觉无损区间；再高（数字更大）在深色渐变背景上会出色带
    -pix_fmt yuv420p   平台兼容性必需。yuv444/420p10 在某些安卓机上是黑屏
    -profile:v high -level 4.2   1080×1920@24fps 的通用档位
    -movflags +faststart        把索引放文件头，微信里能边下边播
    -colorspace/range  显式标 bt709 + tv range，否则播放器按自身猜测解释，
                       深色画面会「发灰」或「死黑」

⚠ 绝对不要加 `-shortest`：
    音频比画面短（画面多出 tail_pad 那 1.3s 的定格留白）。加了 -shortest 会按
    音频时长截断，把结尾的静音定格整段切掉 —— 实测成片从 19.42s 变成 18.08s，
    最后一句话刚讲完画面就断。结尾留白是设计，不是冗余。
"""
import json
import os
import re
import shutil
import subprocess
import sys


def find_ffmpeg(name='ffmpeg'):
    cands = [os.environ.get('MEV_' + name.upper())]
    w = shutil.which(name)
    if w:
        cands.append(w)
    cands += [r'C:\ffmpeg\bin\%s.exe' % name, '/usr/local/bin/%s' % name,
              '/opt/homebrew/bin/%s' % name, '/usr/bin/%s' % name]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    print('找不到 %s。见 build_audio.py 开头的安装提示。' % name)
    sys.exit(3)


FFMPEG = find_ffmpeg('ffmpeg')
FFPROBE = find_ffmpeg('ffprobe')


def run(cmd, timeout=1800):
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    ep_dir = os.path.abspath(args[0])
    name = os.path.basename(ep_dir)
    m = re.match(r'(\d+)_(.*)', name)
    ep_no = m.group(1) if m else '00'
    title = m.group(2) if m else name

    frames = os.path.join(ep_dir, 'frames_ep%s' % ep_no)
    if not os.path.isdir(frames):
        print('找不到帧目录 %s（先跑 render.js full）' % frames)
        return 2
    audio = os.path.join(ep_dir, 'audio', 'final_mix.mp3')
    if not os.path.isfile(audio):
        print('找不到 %s（先跑 build_audio.py）' % audio)
        return 2

    nfr = len([f for f in os.listdir(frames) if f.startswith('frame_')])
    # 帧数校验：少了 1 帧就是音画不同步，必须拦住，不能"渲了就行"
    tl = os.path.join(ep_dir, 'timeline.js')
    expect = 0
    if os.path.isfile(tl):
        s = open(tl, encoding='utf-8-sig').read()
        d = json.loads(s[s.find('{'):s.rfind('}') + 1])
        expect = int(-(-(d['total'] + d.get('tail_pad', 1.3)) * 24 // 1))
    print('帧数 %d / 期望约 %d' % (nfr, expect))
    if nfr < 200:
        print('帧数过少，先完成渲染')
        return 1
    if expect and abs(nfr - expect) > 2:
        print('⚠ 帧数与时间轴不匹配（差 %d 帧）——音画会错位，建议重渲：'
              '先删掉多余帧再 full' % (nfr - expect))

    # 输出文件名：系列名-第NN集-标题.mp4（与归档脚本的命名规则一致）
    series = '成片'
    bj = os.path.join(os.path.dirname(ep_dir), 'brand.json')
    if os.path.isfile(bj):
        series = json.load(open(bj, encoding='utf-8')).get('series_name') or series
    out = os.path.join(ep_dir, '%s-第%s集-%s.mp4' % (series, ep_no, title))

    r = run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
             '-framerate', '24', '-i', os.path.join(frames, 'frame_%06d.jpg'),
             '-i', audio,
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
             '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
             '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
             '-color_range', 'tv', '-tune', 'stillimage',
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-movflags', '+faststart', out])
    if r.returncode != 0:
        print('FFMPEG 失败\n' + r.stderr[-2000:])
        return 1
    print('OK  %s  %.1f MB' % (out, os.path.getsize(out) / 1048576))

    p = run([FFPROBE, '-v', 'error', '-show_entries',
             'format=duration,size,bit_rate',
             '-show_entries', 'stream=codec_name,width,height,r_frame_rate,duration',
             '-of', 'json', out])
    try:
        info = json.loads(p.stdout)
        print(json.dumps(info, ensure_ascii=False, indent=1))
    except Exception:                                   # noqa: BLE001
        print(p.stdout)

    if '--cover' in sys.argv:
        t = float(sys.argv[sys.argv.index('--cover') + 1])
        # 优先用 render.js cover 出的无字幕原图：带字幕的帧裁成 3:4 会把字幕切掉下半截。
        raw = os.path.join(ep_dir, 'cover_raw.jpg')
        fi = int(t * 24)
        src = raw if os.path.isfile(raw) else os.path.join(frames, 'frame_%06d.jpg' % fi)
        dst = os.path.join(ep_dir, '封面候选.jpg')
        if os.path.isfile(src):
            # 3:4 封面（1200×1600）。从 9:16 裁必须**顶部对齐**：
            # 居中裁会把左上角品牌角标切掉一半（实测），而角标是封面识别度的主要来源。
            r2 = run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
                      '-i', src,
                      '-vf', 'crop=1080:1440:0:0,scale=1200:1600:flags=lanczos',
                      '-q:v', '2', dst])
            print('封面候选 -> %s%s' % (dst, '' if os.path.isfile(raw) else '（用了带字幕的帧，建议先跑 render.js cover）'))
        else:
            print('第 %d 帧不存在，无法抽封面' % fi)
    return 0


if __name__ == '__main__':
    sys.exit(main())
