# 竖屏知识科普短视频生产技能

> **输入一个主题，输出一条能留住人的竖屏知识短片。**
> 这套技能不含任何现成选题或素材——它给的是一条能复现同等质量的流水线：七幕结构、分镜语言、句级动画、三层声轨、29 道质检门。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 目录

- [这是什么 / 不是什么](#这是什么--不是什么)
- [核心方法：七幕升维（默认结构）](#核心方法七幕升维默认结构可替换)
- [三种使用方式](#三种使用方式)
- [环境准备](#环境准备)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [脚本参考](#脚本参考)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 这是什么 / 不是什么

**是什么**：一套竖屏（1080×1920）知识讲解短视频的**生产方法与工具集**。适用于科普、历史、经济、心理、技术原理等任何"讲清一个概念 / 一场变革 / 一个人的发现"的题材。

**不是什么**：不是一个选题库，不是一套现成素材，不是某个系列的内容备份。仓库里**没有任何一集的具体内容**——没有集名清单、没有台词、没有画面素材。

**它解决的问题**：把"讲一个知识点"改造成"看一个人怎么被一个麻烦逼出一件原本不存在的东西"。

| 普通科普写法 | 这套写法 |
|---|---|
| "今天我们来讲勾股定理" | "一块地，边长为 1 的正方形，对角线多长？" |
| 先给定义，再举例子 | 先给困境，再给造物 |
| 讲完就走 | 升维成一个可迁移的思维动作 + 留一个没答案的问题 |
| 靠信息量留人 | 靠悬念密度留人（钩子间隔 ≤25s） |

---

## 核心方法：七幕升维（默认结构，可替换）

每集 = **一个人被什么麻烦逼到墙角，然后造出了一个原本不存在的东西**。

| 幕 | 名称 | 时长 | 硬要求 |
|---|---|---|---|
| 0 | 片头 | ≤1.0s | 品牌元素齐全 + 同起片头 BGM |
| 1 | 奇景 | 12–20s | 片头后 3s 亮赌注；一个可看见的物 + 数量；首句 ≤15 字 |
| 2 | 困局 | 30–45s | 4–8 个镜头；必须出分镜板 |
| 3 | 动手 | 22–32s | "跟着我算一步"，10 秒内算得完 |
| 4 | 造物 | 45–70s | 全集最重要动画段；≥1 个"画面自解释"演示 |
| 5 | 穿透 | 35–50s | 领域跨越链条，具体到人物与年份 |
| 6 | 升维 | 25–40s | 收束为单一意象；末尾留白 1.5s 全静音 |
| 7 | 追问 | 12–18s | 赌注对账 + 关键词铭牌（做系列时加下集预告） |

合计 182–276s。四变体（七幕升维 / 双线对撞 / 思想实验 / 物的传记）+ 七种升维型（尺度 / 视角 / 时间 / 概念 / 身份 / 反身 / 文明），详见 [`structures/seven-act.md`](structures/seven-act.md)。

### 结构是可插拔的

上表是**默认结构**，不是唯一答案。选题里如果**说不出"造出来的那个东西"长什么样**（制度怎么烂掉、两派吵了一百年、一座城怎么被放弃），
硬套七幕会逼出空洞的幕（第 4 幕只能堆知识点）。

```
structures/
├── README.md        # 路由规则：什么题材换什么结构 + 8 条不变量 + 结构文件 6 个槽
├── seven-act.md     # 默认：七幕升维（已生产验证）
└── _template.md     # 自建结构模板（含一个未验证的 collapse 填法示例）
```

**换结构的代价**：改三处（选结构 → 抄它的幕表进脚本骨架 → 按映射表读其它文档的幕名）。
`references/` 与 `scripts/` **一行都不用改**——脚本不依赖幕数或幕名。

**不能换的 8 条**：片头 ≤1.0s / 开场 8 秒零前置知识 / 片头后 3 秒亮赌注 / 钩子间隔 ≤25s /
**兑现幕必须最长** / **落点幕不能是本集总结** / 字幕 ≤22 字且 ≤4.5s / 不承接上一集。
清单见 [`structures/README.md`](structures/README.md) §4。

---

## 三种使用方式

### 方式 A：当提示词用（最简单）

把 `SKILL.md` 的内容丢给任何 AI（DeepSeek、豆包、千问、GPT、Claude、本地模型都行），然后给主题：

```
读一下这份技能文件。我要做一集关于「为什么地图上格陵兰岛那么大」的竖屏科普视频，
目标观众是高中生，发抖音，3 分钟。按里面的流程一步步来，每步做完先给我看。
```

> 只要模型能读长文 + 能写代码，就能跑。脚本可选（它是给会用命令行的人加速用的）。

### 方式 B：Clone 仓库跑流水线（最完整）

```bash
git clone <repo-url>
cd vertical-explainer-video

pip install numpy pillow
npm install puppeteer-core

# 开新集
EP=ep01_你的主题
mkdir -p "$EP"
cp templates/FACTS.template.md    "$EP/FACTS.md"
cp templates/脚本骨架.template.md "$EP/脚本.md"
python scripts/progress.py init "$EP" 01 "你的主题"

# 随时看进度
python scripts/progress.py show "$EP"
python scripts/progress.py html "$EP"     # 生成可视化看板
```

### 方式 C：按需查方法论（最灵活）

| 你卡在哪 | 读哪个 |
|---|---|
| 不知道这个选题能不能做 | R1 §2 选题体检 9 问 |
| 不知道怎么开场 | R1 §6 钩子六句范式 |
| 不知道怎么设计镜头 | R2 §4.3 六镜型 |
| 不知道怎么配音/配乐 | R3 三层声轨 + 片头 BGM |
| 质检报错了 | R4 对应的 QC 条目 |
| 遇到奇怪的 bug | R6 经验库（Ctrl+F 搜现象） |

---

## 环境准备

| 依赖 | 版本 | 用途 | 必须 |
|---|---|---|---|
| Python | 3.8+ | `scripts/*.py`（numpy + pillow） | ✅ |
| Node.js | 18+ | `scripts/*.js`（Chrome 渲染） | ✅ |
| Chrome / Chromium | 最新 | 渲染逐帧画面 | ✅ |
| ffmpeg / ffprobe | 最新 | 音频处理、编码、体检 | ✅ |
| TTS 服务 | — | 旁白合成 | 可选 |
| 图生图服务 | — | AI 卡片素材 | 可选 |

```bash
pip install numpy pillow
npm install puppeteer-core
```

**路径全部自适应**，不写死任何绝对路径：

```bash
# 需要覆盖时
export MEV_FFMPEG=/usr/local/bin/ffmpeg
export MEV_FFPROBE=/usr/local/bin/ffprobe
export MEV_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

---

## 快速开始

### 1. 确认输入契约（SKILL.md §0）

主题 / 观众 / 平台 / 时长 / 系列身份 / 品牌配置 —— 6 项。

### 2. 过选题体检（QC-0）

```bash
# R1 §2 的 9 个问题，第 1/2/4/5 条必须过，否则换题
```

### 3. 写脚本前先跑两个门

```bash
python scripts/qc27_hooks.py    "$EP/timeline.js"      # 钩子密度 ≤25s
python scripts/qc28_subpacing.py "$EP/timeline.js"      # 字幕 ≤22 字 / ≤4.5s
```

> 这两个门**必须在写 HTML 之前跑**。此时改字零成本；渲染后发现要重录重渲。

### 4. 渲染完跑体检

```bash
python scripts/epcheck.py "$EP"
python scripts/epcheck.py "$EP" --strict
```

### 5. 归档

```bash
MEV_DST=/your/archive python scripts/archive_flat.py
```

---

## 目录结构

```
vertical-explainer-video/
├── SKILL.md                      # 技能入口（可当提示词）
├── README.md                     # 本文件
├── LICENSE
├── .gitignore
├── brand.example.json            # 品牌配置示例
├── structures/                   # ★ 结构插槽（幕怎么排）
│   ├── README.md                 #   路由规则 + 8 条不变量 + 结构 6 槽
│   ├── seven-act.md              #   默认：七幕升维（已生产验证）
│   └── _template.md              #   自建结构模板（含未验证示例）
├── references/
│   ├── R1-叙事结构.md             # 选题体检 / 钩子 / 赌注 / 查重 / 台账
│   ├── R2-视觉系统.md             # 资产四级 / 动画分级 / 六镜型 / 安全区 / 字幕
│   ├── R3-声音与语气.md           # 三层声轨 / BGM / 幽默 / 通俗化 / 真实性
│   ├── R4-质检门.md               # QC-0~QC-29
│   ├── R5-生产流程.md             # 15 步 / 渲染 / 引擎契约
│   ├── R6-经验库.md               # 现象 → 根因 → 规则
│   ├── R7-小红书图文.md           # 9 图规范
│   └── R8-技能维护指南.md         # 改技能前必读
├── scripts/
│   ├── epcheck.py                # 体检门（14 项）
│   ├── qc27_hooks.py             # 钩子密度
│   ├── qc28_subpacing.py         # 字幕节奏
│   ├── qc26_overlap.js           # 重叠压字
│   ├── audit_motion_template.py  # 运动审计模板
│   ├── progress.py               # 进度跟踪 + 看板
│   └── archive_flat.py           # 归档 + sha256
├── templates/
│   ├── FACTS.template.md         # 事实台账
│   ├── 脚本骨架.template.md      # 脚本骨架（幕表按选定结构）
│   ├── PROGRESS.template.json    # 进度模板
│   └── README.md
└── assets/
    ├── qc_xhs.js                 # 九图版式质检
    └── xhs_center.py             # 九图重心测量
```

---

## 脚本参考

| 脚本 | 干什么 | 典型用法 |
|---|---|---|
| `epcheck.py` | 14 项格式体检（音画时长/字幕/BGM/黑帧/编码/封面…） | `python scripts/epcheck.py ep01_xxx` |
| `progress.py` | 15 步进度 + 门禁 + HTML 看板 | `python scripts/progress.py show ep01_xxx` |
| `qc27_hooks.py` | 钩子密度（最长空窗 ≤25s、前 30s ≥1 问、3s 内赌注句） | `python scripts/qc27_hooks.py timeline.js` |
| `qc28_subpacing.py` | 字幕节奏（≤22 字 / ≤4.5s / 3.5–9 字每秒） | `python scripts/qc28_subpacing.py timeline.js` |
| `qc26_overlap.js` | 图形 × 文本重叠 + 残影文本 | `node scripts/qc26_overlap.js page.html 9431 8891 out.json` |
| `audit_motion_template.py` | 运动审计模板（复制后按集改） | 见文件头注释 |
| `archive_flat.py` | 平铺归档 + sha256 回读 + MANIFEST | `MEV_DST=/path python scripts/archive_flat.py` |

---

## 常见问题

**Q：这个仓库里有具体的视频内容吗？**
A：没有。只有方法、判据、脚本、模板。选题由你给。

**Q：我不写代码，能用吗？**
A：能。把 `SKILL.md` 当提示词喂给 AI 就行；脚本是加速器，不是必需品。

**Q：一定要用 MiniMax / Agnes 这些服务吗？**
A：不。它们是原作者的默认选择。TTS 换成任何服务都行，图生图换成任何服务都行，脚本不绑定。

**Q：macOS / Linux 能跑吗？**
A：能。所有脚本用 `os.path` 拼路径，Chrome 与 ffmpeg 都是跨平台探测。

**Q：做系列可以吗？**
A：可以。`SKILL.md §0` 有系列身份追问清单（系列名 / 口号 / 核心诘问 / 集数），`brand.example.json` 是配置模板。

**Q：怎么保证视频"同一个水平"？**
A：靠三样东西：① 七幕结构固定 ② 29 道质检门有明确判据 ③ 脚本把格式类错误自动化。质量的下限由门守住，上限靠选题和文案。

---

## 贡献

- **报 bug**：开 Issue，附 OS / Python / Node 版本 + 复现步骤 + 期望 vs 实际。
- **改技能**：改之前**必读** `references/R8-技能维护指南.md`（四种改坏方式 + 8 项自检）。
- **提 PR**：fork → 分支 → 提交 → PR。

---

## 许可证

MIT，见 [LICENSE](LICENSE)。