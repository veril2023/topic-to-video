#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_audio.py — 配音 + 句级时间轴 + 三层混音

输入：<集目录>/script_lines.json
      [{"scene": 1, "sentences": ["第一句。", "第二句。"]}, ...]

输出：
      <集目录>/audio/scene_N.mp3      每幕一段配音（TTS 原始产物）
      <集目录>/audio/final_mix.mp3    三层混音后的成片音轨
      <集目录>/audio/subtitles.json   句级字幕（start/end）
      <集目录>/timeline.js            window.AUDIO_TIMELINE，engine.js 的唯一数据源

用法：
    python engine/build_audio.py <集目录>
    python engine/build_audio.py <集目录> --provider edge       # 免费，无需任何 key
    python engine/build_audio.py <集目录> --no-tts            # 复用已有 scene_*.mp3，只重算时间轴
    python engine/build_audio.py <集目录> --voice male-qn-jingying --speed 1.15

配音后端（brand.json 的 tts.provider，或 --provider 覆盖，默认 minimax）：
    minimax   需要 key，查找顺序：
              $MINIMAX_API_KEY → <集目录>/minimax_key.txt → <项目根>/minimax_key.txt
    edge      免费，不需要 key，需要先 `pip install edge-tts`。
              音色形如 zh-CN-YunxiNeural（男）/ zh-CN-XiaoxiaoNeural（女）
    none      不合成，等价于 --no-tts，要求 audio/scene_N.mp3 已经存在

为什么必须先有配音再画画面：
    时间轴由「真实语音的静音位置」反推，不是按字数估算。先画后配音，
    每一句的起止都会对不上，字幕和动画全部要返工。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request


# ----------------------------------------------------------------- 环境探测
def find_ffmpeg():
    """按候选顺序找 ffmpeg。都找不到就明确报错，不要静默失败。"""
    cands = [os.environ.get('MEV_FFMPEG')]
    w = shutil.which('ffmpeg')
    if w:
        cands.append(w)
    cands += [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        '/usr/local/bin/ffmpeg',
        '/opt/homebrew/bin/ffmpeg',
        '/usr/bin/ffmpeg',
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    print('找不到 ffmpeg。安装方式：\n'
          '  Windows: winget install Gyan.FFmpeg\n'
          '  macOS:   brew install ffmpeg\n'
          '  Linux:   sudo apt install ffmpeg\n'
          '或设置环境变量 MEV_FFMPEG=<绝对路径>')
    sys.exit(3)


FFMPEG = find_ffmpeg()


def run(cmd, timeout=900):
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout)


def duration_of(path):
    r = run([FFMPEG, '-i', str(path), '-f', 'null', '-'], timeout=120)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', r.stderr)
    if not m:
        raise RuntimeError('无法读取时长: %s' % path)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


# --------------------------------------------------------------------- TTS
def find_key(ep_dir):
    k = os.environ.get('MINIMAX_API_KEY')
    if k and k.strip():
        return k.strip()
    for p in (os.path.join(ep_dir, 'minimax_key.txt'),
              os.path.join(os.path.dirname(ep_dir), 'minimax_key.txt')):
        if os.path.isfile(p):
            v = io.open(p, encoding='utf-8').read().strip()
            if v:
                return v
    return None


def tts_one(out_path, text, key, model, voice, speed):
    payload = {
        'model': model, 'text': text, 'stream': False,
        'voice_setting': {'voice_id': voice, 'speed': speed, 'vol': 1.0, 'pitch': 0},
        'audio_setting': {'sample_rate': 32000, 'bitrate': 128000,
                          'format': 'mp3', 'channel': 1},
        'language_boost': 'Chinese',
    }
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.minimax.chat/v1/t2a_v2', data=body,
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                d = json.loads(resp.read().decode('utf-8'))
            code = d.get('base_resp', {}).get('status_code')
            audio = d.get('data', {}).get('audio')
            if code == 0 and audio:
                data = bytes.fromhex(audio)
                if len(data) > 1000:
                    io.open(out_path, 'wb').write(data)
                    return True
                last = '返回音频过短'
            else:
                last = 'api %s %s' % (code, d.get('base_resp', {}).get('status_msg'))
        except Exception as e:                      # noqa: BLE001
            last = str(e)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError('TTS 失败（%s）：%s' % (os.path.basename(out_path), last))


def tts_edge(out_path, text, voice, speed):
    """微软 Edge 的在线语音合成：免费，不需要任何 API key。

    依赖第三方包 edge-tts（`pip install edge-tts`），所以延迟导入——
    没装的人跑 minimax 后端时不受影响。
    产物是 24kHz 单声道 mp3，后续 ffmpeg 统一重采样，和 32kHz 的 MiniMax 产物等价。
    """
    try:
        import asyncio
        import edge_tts
    except ImportError:
        raise RuntimeError(
            'Edge TTS 需要先装依赖：pip install edge-tts\n'
            '（免费、不需要 key。音色举例：zh-CN-YunxiNeural 男 / zh-CN-XiaoxiaoNeural 女）')

    rate = '%+d%%' % int(round((float(speed) - 1.0) * 100))
    last = None
    for attempt in range(4):
        try:
            async def _go():
                await edge_tts.Communicate(text, voice, rate=rate).save(out_path)
            asyncio.run(_go())
            if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
                return True
            last = '返回音频过短'
        except Exception as e:                      # noqa: BLE001
            last = str(e)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError('Edge TTS 失败（%s）：%s' % (os.path.basename(out_path), last))


# ------------------------------------------------------- 从静音位置反推句级节拍
def silences_of(path):
    r = run([FFMPEG, '-i', str(path), '-af', 'silencedetect=noise=-38dB:d=0.12',
             '-f', 'null', '-'], timeout=180)
    out, cur = [], None
    for line in r.stderr.splitlines():
        m = re.search(r'silence_start: ([\d.]+)', line)
        if m:
            cur = float(m.group(1))
        m = re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', line)
        if m and cur is not None:
            out.append((cur, float(m.group(1))))
            cur = None
    return out


def detect_beats(path, char_counts, cand_pen=3.0):
    """一幕之内每句的起始秒（相对幕起点）。

    做法：把「真实检测到的静音结束点」和「按字数等比的估计点」合成候选池，
    再用动态规划选出一条单调递增的切分路径，代价 = 与字数估计的偏差² +
    非真实静音点的惩罚。

    为什么不用简单的按字数切：
      中文句长和实际语速不线性 —— 数字、专有名词、停顿都会破坏比例，
      实测误差可达 0.5s 以上，字幕会明显早于或晚于声音。
    为什么用 DP 而不是就近匹配：
      就近匹配会让两个切点抢同一个静音点，造成某句时长为 0。
    """
    n = len(char_counts)
    dur = duration_of(path)
    first = 0.10
    if n <= 1:
        return [first]

    sil = silences_of(path)
    real_ends = {round(e, 3) for _, e in sil if e > 0.05}
    total = float(sum(char_counts))
    est, cum = [], 0.0
    for c in char_counts[:-1]:
        cum += c
        est.append(round(first + (cum / total) * (dur - first), 3))

    pool = sorted({p for p in (real_ends | set(est)) if p > first + 0.05})
    if len(pool) < n - 1:
        pool = sorted(set(pool) | {round(first + (i + 1) * (dur - first) / n, 3)
                                   for i in range(n - 1)})

    K, m = n - 1, len(pool)
    INF = float('inf')
    dp = [[INF] * m for _ in range(K)]
    pv = [[-1] * m for _ in range(K)]
    for j, t in enumerate(pool):
        dp[0][j] = (t - est[0]) ** 2 + (0.0 if t in real_ends else cand_pen)
    for k in range(1, K):
        for j, t in enumerate(pool):
            best, bi = INF, -1
            for i in range(j):
                if dp[k - 1][i] < best:
                    best, bi = dp[k - 1][i], i
            if best < INF:
                dp[k][j] = best + (t - est[k]) ** 2 + (0.0 if t in real_ends else cand_pen)
                pv[k][j] = bi
    bestj, bestc = -1, INF
    for j in range(m):
        if dp[K - 1][j] < bestc:
            bestc, bestj = dp[K - 1][j], j
    idxs, j = [], bestj
    for k in range(K - 1, -1, -1):
        idxs.append(j)
        j = pv[k][j]
    idxs.reverse()
    return [first] + [pool[x] for x in idxs]


# ------------------------------------------------------------------- 音效生成
def gen_pad(path, total):
    """底噪垫：四个低频正弦叠加 + 慢速颤音 + 低通。
    不用素材文件，现场合成 —— 保证任何机器都能跑，且不引入版权问题。"""
    run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
         '-f', 'lavfi', '-i', 'sine=frequency=55:duration=%.3f' % total,
         '-f', 'lavfi', '-i', 'sine=frequency=82.5:duration=%.3f' % total,
         '-f', 'lavfi', '-i', 'sine=frequency=110:duration=%.3f' % total,
         '-f', 'lavfi', '-i', 'sine=frequency=164.81:duration=%.3f' % total,
         '-filter_complex',
         '[0][1][2][3]amix=inputs=4:normalize=0,tremolo=f=0.26:d=0.45,'
         'lowpass=f=520,volume=0.9[a]',
         '-map', '[a]', '-c:a', 'libmp3lame', '-b:a', '128k', str(path)])


SFX_SPECS = {
    'thud': 'anoisesrc=d=0.20:c=brown:a=0.9,lowpass=f=320,'
            'afade=t=in:st=0:d=0.01,afade=t=out:st=0.06:d=0.14,volume=1.6',
    'hum': 'sine=frequency=68:duration=1.0,afade=t=in:st=0:d=0.06,'
           'afade=t=out:st=0.25:d=0.75,volume=1.5',
    'ding': 'sine=frequency=1320:duration=0.9,afade=t=in:st=0:d=0.01,'
            'afade=t=out:st=0.20:d=0.70,volume=0.7',
    'whoosh': 'anoisesrc=d=0.60:c=pink:a=0.5,highpass=f=300,lowpass=f=3200,'
              'afade=t=in:st=0:d=0.12,afade=t=out:st=0.22:d=0.36,volume=1.0',
}


def gen_sfx(dirpath):
    out = {}
    for k, af in SFX_SPECS.items():
        p = os.path.join(dirpath, 'sfx_%s.mp3' % k)
        r = run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
                 '-f', 'lavfi', '-i', af, '-c:a', 'libmp3lame', '-b:a', '128k', p], 120)
        if r.returncode == 0:
            out[k] = p
    return out


# ---------------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    ep_dir = os.path.abspath(args[0])
    no_tts = '--no-tts' in sys.argv

    def opt(name, dflt):
        if '--' + name in sys.argv:
            return sys.argv[sys.argv.index('--' + name) + 1]
        return dflt

    root = os.path.dirname(ep_dir)
    brand = {}
    bj = os.path.join(root, 'brand.json')
    if os.path.isfile(bj):
        brand = json.load(io.open(bj, encoding='utf-8'))
    tts_cfg = brand.get('tts') or {}

    PROVIDER = opt('provider', tts_cfg.get('provider', 'minimax')).strip().lower()
    if PROVIDER not in ('minimax', 'edge', 'none'):
        print('未知的 tts.provider：%s（只支持 minimax / edge / none）' % PROVIDER)
        return 2

    # 音色的默认值取决于后端：两家的 voice id 体系完全不同，不能混用
    _voice_default = 'zh-CN-YunxiNeural' if PROVIDER == 'edge' else 'male-qn-jingying'
    MODEL = opt('model', tts_cfg.get('model', 'speech-2.8-hd'))
    VOICE = opt('voice', tts_cfg.get('voice') or _voice_default)
    SPEED = float(opt('speed', tts_cfg.get('speed', 1.15)))
    INTRO = float(tts_cfg.get('intro', 1.5))
    GAP = float(tts_cfg.get('gap', 0.55))
    GAP_BEFORE_LAST = float(tts_cfg.get('gap_before_last', 1.6))
    TAIL_PAD = float(tts_cfg.get('tail_pad', 1.3))
    VOICE_GAIN = tts_cfg.get('voice_gain', '2dB')
    SFX_VOL = float(tts_cfg.get('sfx_volume', 0.16))
    PAD_VOL = float(tts_cfg.get('pad_volume', 0.16))

    sl_path = os.path.join(ep_dir, 'script_lines.json')
    if not os.path.isfile(sl_path):
        print('找不到 %s\n格式：[{"scene":1,"sentences":["第一句。","第二句。"]}, ...]' % sl_path)
        return 2
    SCENES = json.load(io.open(sl_path, encoding='utf-8'))
    SCENES.sort(key=lambda s: s['scene'])

    audio = os.path.join(ep_dir, 'audio')
    os.makedirs(audio, exist_ok=True)

    # ---- 1. TTS ----
    if no_tts or PROVIDER == 'none':
        print('跳过合成（%s）：复用已有配音' % ('--no-tts' if no_tts else 'tts.provider=none'))
    elif PROVIDER == 'edge':
        print('配音后端：Edge TTS（免费）  音色 %s  语速 %.2f' % (VOICE, SPEED))
        for sc in SCENES:
            p = os.path.join(audio, 'scene_%d.mp3' % sc['scene'])
            print('  第 %d 幕（%d 句）...' % (sc['scene'], len(sc['sentences'])))
            tts_edge(p, ''.join(sc['sentences']), VOICE, SPEED)
            time.sleep(0.8)
    else:
        key = find_key(ep_dir)
        if not key:
            print('找不到 MiniMax API key。四种方式：\n'
                  '  1) 环境变量 MINIMAX_API_KEY\n'
                  '  2) <项目根>/minimax_key.txt\n'
                  '  3) --provider edge（免费，需 pip install edge-tts）\n'
                  '  4) --no-tts（复用已有 scene_*.mp3，只重算时间轴）\n')
            return 3
        for sc in SCENES:
            p = os.path.join(audio, 'scene_%d.mp3' % sc['scene'])
            print('TTS 第 %d 幕（%d 句）...' % (sc['scene'], len(sc['sentences'])))
            tts_one(p, ''.join(sc['sentences']), key, MODEL, VOICE, SPEED)
            time.sleep(0.8)

    # ---- 2. 幕级时间轴 ----
    timeline, t = [], INTRO
    for i, sc in enumerate(SCENES):
        p = os.path.join(audio, 'scene_%d.mp3' % sc['scene'])
        if not os.path.isfile(p):
            print('缺少配音 %s（用 --no-tts 时必须已有该文件）' % p)
            return 3
        d = duration_of(p)
        gap_after = 0.0 if i == len(SCENES) - 1 else GAP
        # 最后一幕前的长静默：给「升维/落点」留呼吸，也让结尾卡有时间站住
        if i == len(SCENES) - 2:
            gap_after = GAP_BEFORE_LAST
        timeline.append({'scene': sc['scene'], 'start': round(t, 3),
                         'duration': round(d, 3), 'gap_after': gap_after})
        print('  幕%d  start=%7.2fs  dur=%6.2fs  gap=%.2f' % (sc['scene'], t, d, gap_after))
        t += d + gap_after
    total = round(t, 3)
    print('配音总长 %.2fs' % total)

    # ---- 3. 句级节拍 ----
    subs = []
    for sc, tl in zip(SCENES, timeline):
        counts = [len(s) for s in sc['sentences']]
        beats = detect_beats(os.path.join(audio, 'scene_%d.mp3' % sc['scene']), counts)
        for i, s in enumerate(sc['sentences']):
            st = tl['start'] + beats[i]
            en = tl['start'] + (beats[i + 1] if i + 1 < len(beats) else tl['duration'])
            subs.append({'scene': sc['scene'], 'idx': i, 'text': s,
                         'start': round(st, 3), 'end': round(en, 3)})
        print('  幕%d 句界: %s' % (sc['scene'], [round(b, 2) for b in beats]))

    io.open(os.path.join(audio, 'subtitles.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(subs, ensure_ascii=False, indent=1))

    # ---- 4. 垫底 + 音效 ----
    pad = os.path.join(audio, 'pad.mp3')
    gen_pad(pad, total)
    sfx = gen_sfx(audio)

    # ---- 5. 事件表（音效落点） ----
    events = []
    if 'whoosh' in sfx:
        events.append((sfx['whoosh'], 0.12, 0.50))                    # 片头入场
    if 'thud' in sfx:
        events.append((sfx['thud'], max(0.0, timeline[0]['start'] - 0.20), 0.16))
    for s in timeline[1:]:
        if 'whoosh' in sfx:
            events.append((sfx['whoosh'], max(0.0, s['start'] - 0.45), SFX_VOL * 0.7))
    # 幕 2 内的三连击 + 低鸣：给「被逼到墙角」提供听觉压强。
    # 位置按幕内比例算，不写死绝对秒数 —— 幕长随文案变化，写死必然错位。
    if len(timeline) > 1:
        a2 = timeline[1]
        if 'thud' in sfx:
            for k in range(3):
                events.append((sfx['thud'], a2['start'] + 0.40 * a2['duration'] + k * 0.22, 0.22))
        if 'hum' in sfx:
            events.append((sfx['hum'], a2['start'] + 0.86 * a2['duration'], 0.20))
    if len(timeline) > 3 and 'thud' in sfx:
        a4 = timeline[3]
        events.append((sfx['thud'], a4['start'] + 0.22 * a4['duration'], 0.22))
    if len(timeline) > 5 and 'ding' in sfx:
        a6 = timeline[5]
        events.append((sfx['ding'], a6['start'] + max(0.0, a6['duration'] - 1.2), 0.26))

    # ---- 6. 三层混音 ----
    inputs, labels = [], []
    for i, s in enumerate(timeline):
        inputs += ['-i', os.path.join(audio, 'scene_%d.mp3' % s['scene'])]
        ms = int(s['start'] * 1000)
        labels.append('[%d:a]adelay=%d|%d,volume=%s[v%d]' % (i, ms, ms, VOICE_GAIN, i))
    for k, (p, at, vol) in enumerate(events):
        inputs += ['-i', p]
        src = len(inputs) // 2 - 1
        ms = max(0, int(at * 1000))
        labels.append('[%d:a]adelay=%d|%d,volume=%.3f[s%d]' % (src, ms, ms, vol, k))
    inputs += ['-i', pad]
    pad_src = len(inputs) // 2 - 1
    labels.append('[%d:a]volume=%.3f,afade=t=in:st=0:d=3.0,'
                  'afade=t=out:st=%.3f:d=3.0[pd]'
                  % (pad_src, PAD_VOL, max(0.0, total - 3.2)))
    mix_in = (''.join('[v%d]' % i for i in range(len(timeline)))
              + ''.join('[s%d]' % i for i in range(len(events))) + '[pd]')
    labels.append('%samix=inputs=%d:normalize=0:dropout_transition=0,'
                  'alimiter=limit=0.95[aout]' % (mix_in, len(timeline) + len(events) + 1))

    out_mix = os.path.join(audio, 'final_mix.mp3')
    r = run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error']
            + inputs + ['-filter_complex', ';'.join(labels),
                        '-map', '[aout]', '-c:a', 'libmp3lame', '-b:a', '192k', out_mix])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        print('混音失败')
        return 1
    print('混音完成 %.2fs（目标 %.2fs）' % (duration_of(out_mix), total))

    # ---- 7. 输出时间轴 ----
    io.open(os.path.join(ep_dir, 'timeline.js'), 'w', encoding='utf-8', newline='\n').write(
        'window.AUDIO_TIMELINE = ' + json.dumps({
            'starts': [s['start'] for s in timeline],
            'durations': [s['duration'] for s in timeline],
            'gaps': [s['gap_after'] for s in timeline],
            'intro': INTRO, 'gap': GAP, 'total': total, 'tail_pad': TAIL_PAD,
            'voice': '%s/%s' % (PROVIDER, VOICE), 'speed': SPEED,
            'subtitles': subs}, ensure_ascii=False) + ';\n')
    io.open(os.path.join(ep_dir, 'audio', 'timeline.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'total': total, 'intro': INTRO, 'gap': GAP,
                    'scenes': timeline, 'tail_pad': TAIL_PAD},
                   ensure_ascii=False, indent=2))
    print('timeline.js 已写入（%d 幕 / %d 句）' % (len(timeline), len(subs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
