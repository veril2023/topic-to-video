# -*- coding: utf-8 -*-
"""epcheck.py —— 竖屏知识短视频每集体检门（QC-29）

用途：抓"低级格式错误"，不判艺术质量。渲染完、合片后、归档前各跑一次。
用法：
    python scripts/epcheck.py ep01_你的主题
    python scripts/epcheck.py ep01_你的主题 --frames=12     # 抽样帧数（默认 9）
    python scripts/epcheck.py ep01_你的主题 --strict        # WARN 也算失败

退出码：0 全通过（可有 WARN）；1 有 FAIL；2 参数错误

设计原则：
  - 每项检查独立 try，一项炸不影响其它项
  - 所有数值实测，不推算
  - 程序判不了"画面对不对题"，CK-14 只输出待人工确认的抽样清单
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

def _find_bin(name):
    """按候选列表探测 ffmpeg/ffprobe；都找不到就返回裸命令名交给 PATH。
    这样脚本能在不同机器/不同项目目录下直接跑，不必改代码。

    优先级：环境变量 > 常见安装路径（跨平台） > 脚本同级目录 > 系统 PATH。
    """
    ext = '.exe' if os.name == 'nt' else ''
    cands = [
        os.environ.get('MEV_%s' % name.upper()),
        # 跨平台常见路径
        r"C:\ffmpeg\bin\%s%s" % (name, ext),
        r"C:\Program Files\ffmpeg\bin\%s%s" % (name, ext),
        r"/usr/bin/%s%s" % (name, ext),
        r"/usr/local/bin/%s%s" % (name, ext),
        r"/opt/homebrew/bin/%s%s" % (name, ext),
        r"/opt/ffmpeg/bin/%s%s" % (name, ext),
        # 脚本同级目录
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '%s%s' % (name, ext)),
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return name


FFMPEG = _find_bin('ffmpeg')
FFPROBE = _find_bin('ffprobe')

RESULTS = []   # (level, code, text)  level: PASS / WARN / FAIL / SKIP / INFO


def rec(level, code, text):
    RESULTS.append((level, code, text))
    print('[%s] %-6s %s' % (level, code, text))


def sh(args, timeout=120):
    return subprocess.run(args, capture_output=True, timeout=timeout)


def probe(path):
    r = sh([FFPROBE, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', path])
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode('utf-8', 'ignore'))


def parse_srt(path):
    raw = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
    blocks = re.split(r'\n\s*\n', raw.strip())
    cues = []
    for b in blocks:
        m = re.search(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*'
                      r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', b)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        st = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        en = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        txt = b[m.end():].strip()
        cues.append((st, en, txt))
    return cues


def audio_rms_db(path, t0, t1):
    """解出 [t0,t1] 区间单声道 22.05k PCM，返回 RMS dBFS。"""
    r = sh([FFMPEG, '-v', 'quiet', '-ss', '%.3f' % t0, '-i', path,
            '-t', '%.3f' % (t1 - t0), '-ac', '1', '-ar', '22050',
            '-f', 's16le', '-'], timeout=90)
    if r.returncode != 0 or not r.stdout:
        return None
    a = np.frombuffer(r.stdout, dtype='<i2').astype(np.float64) / 32768.0
    if a.size == 0:
        return None
    rms = float(np.sqrt(np.mean(a ** 2)))
    if rms <= 1e-9:
        return -120.0
    return 20.0 * np.log10(rms)


def find_one(pats):
    for p in pats:
        g = sorted(glob.glob(p))
        if g:
            return g[0]
    return None


def blur_var(img):
    g = img.convert('L')
    k = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1)
    return float(np.asarray(g.filter(k), dtype=np.float64).var())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    epdir = os.path.abspath(args[0])
    if not os.path.isdir(epdir):
        print('FAIL 目录不存在: %s' % epdir)
        return 2

    nframes = 9
    strict = '--strict' in sys.argv
    for a in sys.argv[1:]:
        if a.startswith('--frames='):
            nframes = int(a.split('=', 1)[1])

    epname = os.path.basename(epdir)
    m = re.search(r'ep(\d{2})', epname, re.I)
    N = m.group(1) if m else '??'

    print('=' * 68)
    print('epcheck 体检门 · %s' % epname)
    print('=' * 68)

    # ---------- 找文件 ----------
    mp4 = find_one([os.path.join(epdir, '第%s集-*.mp4' % N),
                    os.path.join(epdir, '*.mp4')])
    srt = find_one([os.path.join(epdir, '字幕_ep%s.srt' % N),
                    os.path.join(epdir, '*.srt')])
    aud = find_one([os.path.join(epdir, 'audio%s' % N, 'final_mix.mp3'),
                    os.path.join(epdir, 'audio%s' % N, 'final_mix.wav')])
    frame_dir = find_one([os.path.join(epdir, 'frames_ep%s' % N),
                          os.path.join(epdir, 'frames')])
    cover = find_one([os.path.join(epdir, '第%s集-*封面*.jpg' % N),
                      os.path.join(epdir, 'cover_34_ep%s.jpg' % N),
                      os.path.join(epdir, '*封面*.jpg')])

    print('成片 : %s' % (os.path.basename(mp4) if mp4 else '未找到'))
    print('字幕 : %s' % (os.path.basename(srt) if srt else '未找到'))
    print('音频 : %s' % (os.path.basename(aud) if aud else '未找到'))
    print('帧目录: %s' % (os.path.basename(frame_dir) if frame_dir else '未找到'))
    print('封面 : %s' % (os.path.basename(cover) if cover else '未找到'))
    print('-' * 68)

    vdur = adur = None
    vinfo = ainfo = None
    probes = {}

    # ---------- CK-10 编码合规 / CK-01 音画时长 ----------
    try:
        pj = probe(mp4) if mp4 else None
        if not pj:
            rec('FAIL', 'CK-10', '无法读取成片流信息')
        else:
            for s in pj.get('streams', []):
                if s.get('codec_type') == 'video':
                    vinfo = s
                elif s.get('codec_type') == 'audio':
                    ainfo = s
            if not vinfo:
                rec('FAIL', 'CK-10', '成片里没有视频流')
            else:
                w, h = int(vinfo.get('width', 0)), int(vinfo.get('height', 0))
                fps_s = vinfo.get('r_frame_rate', '0/1')
                try:
                    n1, n2 = fps_s.split('/')
                    fps = float(n1) / float(n2) if float(n2) else 0
                except Exception:
                    fps = 0
                pix = vinfo.get('pix_fmt', '')
                codec = vinfo.get('codec_name', '')
                badges = []
                if (w, h) != (1080, 1920):
                    badges.append('分辨率 %dx%d≠1080x1920' % (w, h))
                if abs(fps - 24) > 0.01:
                    badges.append('帧率 %.3f≠24' % fps)
                if pix != 'yuv420p':
                    if pix.startswith('yuvj'):
                        badges.append('pix_fmt=%s（JPEG full-range 遗留，部分播放器会偏亮→重编码加 -color_range tv）' % pix)
                    else:
                        badges.append('pix_fmt=%s' % pix)
                if codec != 'h264':
                    badges.append('codec=%s' % codec)
                if ainfo and ainfo.get('codec_name') != 'aac':
                    badges.append('音频=%s' % ainfo.get('codec_name'))
                if badges:
                    rec('FAIL', 'CK-10', '编码不合规：' + ' / '.join(badges))
                else:
                    rec('PASS', 'CK-10', '编码合规 %dx%d / %.0ffps / %s / %s / AAC'
                        % (w, h, fps, codec, pix))
                vdur = float(vinfo.get('duration') or 0) or None
    except Exception as e:
        rec('FAIL', 'CK-10', '异常: %s' % e)

    try:
        if aud:
            aj = probe(aud)
            if aj:
                adur = float(aj.get('format', {}).get('duration') or 0) or None
        if vdur is None and mp4:
            pj = probe(mp4)
            if pj:
                vdur = float(pj.get('format', {}).get('duration') or 0) or None
        if vdur and adur:
            diff = vdur - adur
            # v5 设计：视频应比音频长 1.3~3.8s（尾部静音定格，让观众读完结尾卡）。
            # 视频比音频长是设计，不是错误 —— 但超 5s 说明渲多了，为负说明被截了。
            if -0.5 <= diff <= 5.0:
                rec('PASS', 'CK-01', '音画时长 视频%.2fs / 音频%.2fs / 尾部定格%+.2fs（设计区间）'
                    % (vdur, adur, diff))
            elif diff < -0.5:
                rec('FAIL', 'CK-01', '视频比音频短 %.2fs —— 结尾被截断了' % (-diff))
            else:
                rec('FAIL', 'CK-01', '视频比音频长 %.2fs，超过 5s 上限（结尾拖太久或帧数多了）' % diff)
            if diff >= 1.3:
                rec('PASS', 'CK-12', '结尾卡停留 %.2fs（≥1.3s）' % diff)
            else:
                rec('FAIL', 'CK-12', '结尾卡停留仅 %.2fs，不足 1.3s（观众读不完结尾卡）' % diff)
        else:
            rec('SKIP', 'CK-01', '缺视频或音频时长，无法比对')
    except Exception as e:
        rec('FAIL', 'CK-01', '异常: %s' % e)

    # ---------- CK-02 / 03 / 05 字幕 ----------
    cues = []
    try:
        if not srt:
            rec('SKIP', 'CK-02', '未找到 srt')
        else:
            cues = parse_srt(srt)
            if not cues:
                rec('FAIL', 'CK-02', 'srt 解析出 0 条 cue（格式可能损坏）')
            else:
                last_end = max(c[1] for c in cues)
                if adur:
                    if last_end <= adur + 0.3:
                        rec('PASS', 'CK-02', '字幕末条 %.2fs ≤ 音频 %.2fs +0.3s（共 %d 条）'
                            % (last_end, adur, len(cues)))
                    else:
                        rec('FAIL', 'CK-02', '字幕末条 %.2fs 超出音频 %.2fs（多 %.2fs，最后一条会被截）'
                            % (last_end, adur, last_end - adur))
                else:
                    rec('SKIP', 'CK-02', '缺音频时长')

                overlaps = []
                for i in range(1, len(cues)):
                    if cues[i][0] < cues[i - 1][1] - 0.001:
                        overlaps.append((i, cues[i - 1][1] - cues[i][0]))
                if overlaps:
                    rec('FAIL', 'CK-03', '字幕条重叠 %d 处（最严重 %.2fs @第%d条）'
                        % (len(overlaps), max(o[1] for o in overlaps), overlaps[0][0]))
                else:
                    rec('PASS', 'CK-03', '字幕条无重叠')

                gaps = []
                for i in range(1, len(cues)):
                    g = cues[i][0] - cues[i - 1][1]
                    if g > 1.5:
                        gaps.append((i, g))
                if gaps:
                    rec('WARN', 'CK-05', '字幕空洞 %d 处 >1.5s（最长 %.1fs @第%d条）→ 这段没有台词'
                        % (len(gaps), max(g[1] for g in gaps), gaps[0][0]))
                else:
                    rec('PASS', 'CK-05', '字幕无明显空洞')
    except Exception as e:
        rec('FAIL', 'CK-03', '异常: %s' % e)

    # ---------- CK-04 片头 BGM ----------
    try:
        if not aud:
            rec('SKIP', 'CK-04', '未找到 final_mix 音频')
        else:
            a1 = audio_rms_db(aud, 0.0, 1.0)
            a2 = audio_rms_db(aud, 2.0, 3.0)
            if a1 is None or a2 is None:
                rec('SKIP', 'CK-04', '音频解码失败')
            else:
                d = a1 - a2
                if d >= 6.0:
                    rec('PASS', 'CK-04', '片头BGM 0-1s=%.1fdB / 2-3s=%.1fdB / 高 %.1fdB（≥6dB，v6 达标）'
                        % (a1, a2, d))
                else:
                    rec('FAIL', 'CK-04', '片头BGM 0-1s=%.1fdB / 2-3s=%.1fdB / 仅高 %.1fdB（需≥6dB）→ v6 要求片头 1 秒有明显 BGM 抓耳'
                        % (a1, a2, d))
    except Exception as e:
        rec('FAIL', 'CK-04', '异常: %s' % e)

    # ---------- CK-09 帧序 ----------
    frames = []
    try:
        if not frame_dir:
            rec('SKIP', 'CK-09', '未找到帧目录（可能已清理）')
        else:
            frames = sorted(glob.glob(os.path.join(frame_dir, 'frame_*.jpg')))
            if not frames:
                rec('SKIP', 'CK-09', '帧目录为空')
            else:
                nums = []
                for f in frames:
                    mm = re.search(r'frame_(\d+)\.jpg$', f)
                    if mm:
                        nums.append(int(mm.group(1)))
                nums.sort()
                # 帧号从 0 开始（frame_000000.jpg），不是从 1
                lo, hi = nums[0], nums[-1]
                have = set(nums)
                missing = [n for n in range(lo, hi + 1) if n not in have]
                dup = len(nums) - len(have)
                if missing:
                    rec('FAIL', 'CK-09', '帧序号缺失 %d 个（首个 %s）' % (len(missing), missing[0]))
                elif dup:
                    rec('FAIL', 'CK-09', '帧重复 %d 个' % dup)
                else:
                    rec('PASS', 'CK-09', '帧序完整 %d 帧（%d–%d 连续）' % (len(nums), lo, hi))
    except Exception as e:
        rec('FAIL', 'CK-09', '异常: %s' % e)

    # ---------- CK-06 / 07 / 08 抽样帧 ----------
    try:
        if not frames:
            rec('SKIP', 'CK-06', '无帧可抽')
        else:
            n = min(nframes, len(frames))
            idx = [int(round(i * (len(frames) - 1) / (n - 1))) for i in range(n)] if n > 1 else [0]
            dark, blurry, textonly = [], [], []
            for i in idx:
                im = Image.open(frames[i]).convert('RGB')
                arr = np.asarray(im)
                g = np.asarray(im.convert('L'), dtype=np.float64)
                std = float(g.std())
                fname = os.path.basename(frames[i])
                if std < 3.0:
                    dark.append((fname, std))
                if frames[i] == frames[idx[0]]:
                    continue
                bv = blur_var(im)
                if bv < 80:
                    blurry.append((fname, bv))
                # 主画面区（y 300-1330，避开角标与字幕带）
                band = g[300:1330, :]
                ink = float((band > 60).mean()) * 100
                if ink < 0.05:
                    textonly.append((fname, ink))
            if dark:
                rec('FAIL', 'CK-06', '纯色/黑帧 %d 张（如 %s std=%.2f）' % (len(dark), dark[0][0], dark[0][1]))
            else:
                rec('PASS', 'CK-06', '抽样 %d 帧无纯色/黑帧' % len(idx))
            if blurry:
                rec('WARN', 'CK-07', '可能模糊 %d 张（最低 %s 拉普拉斯方差=%.0f，阈值80）'
                    % (len(blurry), blurry[0][0], blurry[0][1]))
            else:
                rec('PASS', 'CK-07', '抽样帧清晰度正常')
            if textonly:
                rec('WARN', 'CK-08', '疑似纯文字帧 %d 张（主画面区墨迹 <0.05%%，如 %s）'
                    % (len(textonly), textonly[0][0]))
            else:
                rec('PASS', 'CK-08', '抽样帧主画面区都有图形')
            print('         抽样帧: ' + ', '.join(os.path.basename(frames[i]) for i in idx))
    except Exception as e:
        rec('FAIL', 'CK-06', '异常: %s' % e)

    # ---------- CK-11 封面 ----------
    try:
        if not cover:
            rec('WARN', 'CK-11', '未找到封面文件')
        else:
            im = Image.open(cover)
            w, h = im.size
            if (w, h) == (1200, 1600):
                rec('PASS', 'CK-11', '封面 %dx%d（3:4 合规）' % (w, h))
            else:
                rec('FAIL', 'CK-11', '封面 %dx%d ≠ 1200x1600' % (w, h))
    except Exception as e:
        rec('WARN', 'CK-11', '异常: %s' % e)

    # ---------- CK-13 体积 ----------
    try:
        if mp4:
            mb = os.path.getsize(mp4) / 1048576.0
            if 8 <= mb <= 60:
                rec('PASS', 'CK-13', '成片 %.2f MB（v5 矢量底正常区间）' % mb)
            else:
                rec('WARN', 'CK-13', '成片 %.2f MB 超出 8–60MB（过小=渲错，过大=可能混进照片）' % mb)
    except Exception as e:
        rec('WARN', 'CK-13', '异常: %s' % e)

    # ---------- CK-14 人工项 ----------
    print('-' * 68)
    print('[INFO] CK-14 图形语义匹配 —— 必须人工，程序不判')
    if frames:
        n = 6
        step = max(1, len(frames) // n)
        picks = [frames[min(i * step, len(frames) - 1)] for i in range(n)]
        print('         请逐张打开，对台词问一句「这张图画的是这句话吗」：')
        for p in picks:
            print('           %s' % p)
    print('         判据：图形表达的含义必须与当拍台词一致；装饰性图形不算')

    # ---------- 汇总 ----------
    print('=' * 68)
    fails = [r for r in RESULTS if r[0] == 'FAIL']
    warns = [r for r in RESULTS if r[0] == 'WARN']
    print('汇总：PASS %d / WARN %d / FAIL %d / SKIP %d'
          % (sum(1 for r in RESULTS if r[0] == 'PASS'), len(warns), len(fails),
             sum(1 for r in RESULTS if r[0] == 'SKIP')))
    if fails:
        print('不通过项：' + ' / '.join('%s(%s)' % (r[1], r[2][:24]) for r in fails))
        print('结果：FAIL —— 修好再归档')
        return 1
    if warns and strict:
        print('结果：FAIL（--strict 模式下 WARN 也算失败）')
        return 1
    print('结果：PASS' + ('（有 WARN，请人工确认）' if warns else ''))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
