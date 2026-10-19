#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tts_custom.py — 自定义配音接入点（想用别的 TTS 时，只改这一个文件）

`build_audio.py --provider custom` 会调用本文件的 synthesize()。
你想接任何 TTS —— 本地模型、别的云服务、公司内部接口 —— **只改这一个函数**，
主流程代码一行都不用动。

约定
----
输入  text      这一幕的全部台词（多句已经拼在一起，请整段合成，不要自己切句）
      out_path  要写出的音频路径（文件名已按 audio/scene_N.mp3 定好）
      voice     brand.json 里 tts.voice 的值，原样传给你，怎么解释由你决定
      speed     brand.json 里 tts.speed 的值（1.15 = 1.15 倍速）
输出  在 out_path 写出一个能正常播放的音频（mp3 最稳；写 wav/m4a 也可以，
      后续 ffmpeg 能读，但你要自己保证扩展名和实际格式一致）
返回  True = 成功；抛异常 = 失败，build_audio.py 会打印原因并停在那一步

为什么是「每幕一个文件」而不是「每句一个」
----------------------------------------
句子的起止时间是从这段音频的**静音位置**反推出来的（silencedetect + DP 选最优切分），
所以只要音频是正常朗读、句与句之间有自然停顿就行，**不需要你提供任何时间戳**。
这也是为什么换哪家 TTS 都不影响画面对齐。

自测
----
改完之后跑一次：
    python engine/build_audio.py 01_你的主题 --provider custom
"""
import os
import subprocess


def synthesize(text, out_path, voice='', speed=1.0):
    """把 text 合成到 out_path。改这里就行。"""

    # ------------------------------------------------------------------
    # 示例 A · 调命令行工具（把 cmd 换成你的 TTS 命令）
    # ------------------------------------------------------------------
    # 只要你的工具能「给一段文字 + 输出一个音频文件」，就能这样接。
    # 下面以 edge-tts 的命令行版本为例（pip install edge-tts 后可直接用）：
    #
    # rate = '%+d%%' % round((float(speed) - 1) * 100)
    # cmd = ['edge-tts',
    #        '--voice', voice or 'zh-CN-YunxiNeural',
    #        '--rate', rate,
    #        '--text', text,
    #        '--write-media', out_path]
    # subprocess.run(cmd, check=True)
    # return True

    # ------------------------------------------------------------------
    # 示例 B · 调 HTTP 接口（以 OpenAI 兼容的 /v1/audio/speech 为例）
    # ------------------------------------------------------------------
    # 硅基流动、火山、DeepInfra 等很多家都兼容这个形状，改 base_url 和 model 即可。
    #
    # import json, urllib.request
    # payload = {'model': 'tts-1', 'input': text,
    #            'voice': voice or 'alloy', 'response_format': 'mp3'}
    # req = urllib.request.Request(
    #     'https://api.openai.com/v1/audio/speech',
    #     data=json.dumps(payload).encode('utf-8'),
    #     headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
    #              'Content-Type': 'application/json'})
    # with urllib.request.urlopen(req, timeout=180) as r:
    #     data = r.read()
    # with open(out_path, 'wb') as f:
    #     f.write(data)
    # return True

    # ------------------------------------------------------------------
    # 示例 C · 调本地模型（命令行方式，比如 CosyVoice / GPT-SoVITS 的推理脚本）
    # ------------------------------------------------------------------
    # python 环境里如果能 import 到模型，也可以直接在这里跑推理，
    # 只要最后把音频写到 out_path 即可。

    raise NotImplementedError(
        'engine/tts_custom.py 还没填。\n'
        '  打开这个文件，把 synthesize() 里任意一个示例取消注释、改成你的服务，再重跑。\n'
        '  不想写代码的话有现成两条路：\n'
        '    --provider edge     免费，pip install edge-tts\n'
        '    --provider minimax  需要 MINIMAX_API_KEY\n'
        '  或者自己把音频做成 audio/scene_N.mp3，然后跑 --no-tts。'
    )
