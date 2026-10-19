#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate0.py — 主题闸门（开工前第一个动作）

用法：
    python scripts/gate0.py "帮我按《数学之美》做一系列视频"
    python scripts/gate0.py "讲讲量子力学"
    python scripts/gate0.py "为什么井盖是圆的"

为什么要有这个脚本：
    文档里的"先判断再开工"是软要求，模型经常跳过它直接产出大纲。
    但模型对"跑一条命令并贴出结果"的服从度，远高于"遵守一段文字规则"——
    因为跑命令有明确动作和输出，跳过它会被用户看出来。

    所以把判断做成一个可执行动作：脚本先做机器能做的粗筛，
    再输出一张必须填的空表。填不了这张表，就不该开工。

这不是自动判定，脚本只做三件事：
    1. 关键词初筛（D 级合规风险 / C 级抽象风险 / 时效性风险）
    2. 颗粒度检查（主题太粗 → 提示降到一个具体事件）
    3. 输出三问 + 七项契约的填空表，默认值已预填
"""
import io
import re
import sys

# ---------------------------------------------------------------- 关键词初筛
D_RISK = [
    (r'揭秘|真相|内幕|隐瞒|封杀|不敢说|删前', '事实难以双源核实，且有误导风险'),
    (r'养生|食疗|排毒|治(病|疗|愈)|吃什么(好|能)|偏方|抗癌', '医疗健康建议，合规风险'),
    (r'荐股|股票|基金|买入|涨(停|跌)|抄底|收益率', '投资建议，合规风险'),
    (r'政治|领导人|体制|意识形态', '政治敏感'),
]
C_RISK = [
    (r'励志|鸡汤|正能量|感动|治愈|温暖|人生感悟', '情感共鸣类，本技能调性是理性+具体物，做出来会说教'),
    (r'今天|昨日|最新|突发|刚刚|本周', '时效性极强，竖屏短视频寿命只有几天'),
    (r'教程|怎么(用|操作|安装|设置)|步骤|入门到', '操作教程，3 分钟竖屏装不下，应横屏长视频'),
]
ABSTRACT_HINT = [
    r'^什么是', r'原理$', r'概论$', r'导论', r'哲学$', r'思想$', r'体系$',
]
A_HINT = [
    r'为什么.{2,}', r'(谁|怎么|如何)(发明|发现|造出|做出)', r'诞生', r'身世',
    r'那(一|个)(天|年|次)', r'失败|崩(盘|溃)|被推翻|错在',
]


def classify(topic):
    """返回 (级别, 原因列表)。级别只是初筛，不等于结论。"""
    reasons = []
    level = 'B'

    for pat, why in D_RISK:
        if re.search(pat, topic):
            reasons.append('D 级风险：' + why)
            level = 'D'
    for pat, why in C_RISK:
        if re.search(pat, topic):
            reasons.append('C 级风险：' + why)
            if level != 'D':
                level = 'C'
    for pat in ABSTRACT_HINT:
        if re.search(pat, topic):
            reasons.append('抽象信号：主题像"一个领域"而不是"一件事"')
            if level == 'B':
                level = 'C'
    for pat in A_HINT:
        if re.search(pat, topic):
            reasons.append('具体信号：已含具体事件/人物/反差，接近 A 级')
            if level == 'B':
                level = 'A'
    return level, reasons


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    topic = ' '.join(sys.argv[1:]).strip()
    n = len(topic)

    level, reasons = classify(topic)

    print('=' * 70)
    print('主题闸门  ' + topic)
    print('=' * 70)

    # ---- 颗粒度 ----
    print('\n[1] 颗粒度')
    if n <= 6:
        print('  ⚠ 只有 %d 个字，太粗。这通常是"一个领域"，不是"一件事"。' % n)
        print('    改写方向：降到一个人 / 一个物 / 一次争论 / 一次失败。')
        print('    例：量子力学 → 爱因斯坦和玻尔争了三十年，到底在争什么')
    elif n <= 15:
        print('  · 偏短，可能仍然是一个话题而不是一件事，请在三问里确认。')
    else:
        print('  ✓ 长度够，像是一个具体命题。')

    # ---- 关键词初筛 ----
    print('\n[2] 关键词初筛（机器能做的只有这些）')
    if reasons:
        for r in reasons:
            print('  · ' + r)
    else:
        print('  · 没有命中任何风险词。注意：没命中不等于没问题。')
    print('  初筛级别：%s（仅供参考，最终以三问为准，见 R10）' % level)

    # ---- 三问填空表 ----
    print('\n[3] 三问（必须逐条填，填不了就不该开工）')
    print('  ' + '-' * 66)
    print('  | # | 问题 | 判断 | 一句理由 |')
    print('  |---|------|------|----------|')
    print('  | 1 | 能画出来吗？（核心那件事有不看字幕也能看懂的物/场景/动作） | ⬜ | |')
    print('  | 2 | 能一句话说清它在争什么吗？（二分问题或将被验证的断言） | ⬜ | |')
    print('  | 3 | 事实查得到吗？（≥2 个独立来源） | ⬜ | |')
    print('  ' + '-' * 66)
    print('  三过 → 接；一不过 → 换角度（R10 §6）；两不过 → 拒。')

    # ---- 七项契约 ----
    print('\n[4] 输入契约（默认值已预填，用户只需改他关心的）')
    print('  ' + '-' * 66)
    print('  | # | 项 | 我的预填 |')
    print('  |---|----|----------|')
    print('  | 1 | 一句话主题 | （由三问改写到"一件事"的粒度） |')
    print('  | 2 | 目标观众 | 泛知识受众，高中以上学历 |')
    print('  | 3 | 发布平台 | 抖音 + 视频号双投 |')
    print('  | 4 | 时长档 | 3–4.5 分钟 |')
    print('  | 5 | 结构 | seven-act（说不出来就按 R9/structures 换） |')
    print('  | 6 | 系列身份 | 单条视频，不做系列 |')
    print('  | 7 | 品牌配置 | brand.json 默认值 |')
    print('  | 8 | 配音方案 | edge（免费，需 pip install edge-tts）；有自己的 TTS 就说，改 engine/tts_custom.py |')
    print('  ' + '-' * 66)

    # ---- 结论 ----
    print('\n[5] 下一步')
    too_coarse = n <= 6
    if level == 'D':
        print('  ⛔ 命中 D 级风险。不要开工。按 R10 §5 的拒绝话术回复，并给出替代方向。')
    elif too_coarse:
        print('  ⚠ 主题太粗，现在发契约表没有意义——他自己也不知道第 1 项该填什么。')
        print('    先给用户 2–3 个降颗粒度的改写方案（一个人 / 一个物 / 一次争论 / 一次失败），')
        print('    让他挑一个。挑定后拿那句新主题再跑一次本脚本，那时才发 [3][4] 两张表。')
    elif level == 'C':
        print('  ⚠ 命中 C 级风险。不要直接开工，先向用户说明这个题材的代价，')
        print('    并给出一个降颗粒度的改写方案，让用户选。')
    else:
        print('  ✓ 把上面 [3] 和 [4] 两张表原样发给用户，等他确认后再开工。')
        print('  ⛔ 在用户回复之前，不要输出脚本、分集表或画面代码。')
    print('')
    print('本脚本只做初筛，不替代判断。完整标准见 references/R10-适用边界.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
