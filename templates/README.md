# templates/ · 新集开工模板

开一集新视频时，把这三个模板复制进集目录，改掉 `{NN}` `{标题}` 即可。
**不要从零建文件**——每集都要重新写 FACTS 的六节结构，是纯浪费。

## 一次性开工（复制 + 初始化）

```bash
EP=ep01_你的主题
mkdir -p "$EP"

cp templates/FACTS.template.md    "$EP/FACTS.md"
cp templates/脚本骨架.template.md "$EP/脚本.md"

python scripts/progress.py init "$EP" 01 "你的主题"
python scripts/progress.py show "$EP"
```

## 三个文件干什么

| 文件 | 作用 | 什么时候填完 |
|---|---|---|
| `FACTS.template.md` | 事实台账（QC-20）。分 T0/T1/T2/T3 四级，含"不能说的话"红线表 | **进分镜之前**（有「待补」就停） |
| `脚本骨架.template.md` | 七幕脚本骨架，已内建开场六句表、赌注句、钩子分布表、自检清单 | 第 6 步，写完跑 QC-27/28 |
| `PROGRESS.template.json` | 15 步进度 + 三个门的结果 | 全程维护，每次续做先 `show` |

## PROGRESS 怎么用（解决"跨会话不知道做到哪"）

```bash
python scripts/progress.py show  $EP              # 续做时第一件事
python scripts/progress.py done  $EP 7 "开场三件套过 QC-27/28"
python scripts/progress.py gate  $EP QC-29 PASS
python scripts/progress.py note  $EP "a4-16 入场改为 1.2s"
python scripts/progress.py html  $EP              # 生成 PROGRESS.html 看板
```

`show` 的输出里 `[x]` 已完成、`[~]` 进行中、`[ ]` 未开始、`[!]` 卡住。
**如果 `facts_pending` 非空，脚本会直接警告"按 QC-20 不许进分镜"**——
这是防止带病往下走的最后一道保险。

## 纪律

- 模板里的**空白表格要真的填**，不要留空交差。留空等于没做。
- `FACTS.md` 的「二、最大的真实性风险」至少写 2 条「不能说的话」；
  写不出说明检索不够深。
- `脚本骨架` 的第七节自检清单是**逐条打勾**，不是浏览一遍。
- 复制模板后立刻改集号与标题——**忘了改是最高频的低级事故**（QC-10）。
