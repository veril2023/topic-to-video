# 《万物有数》竖屏数学短视频生产技能 · v6 · 通用版

> **一句话**：把"一个人被什么麻烦逼到墙角，然后造出了一个原本不存在的东西"做成 67 集竖屏短视频的完整生产技能。去平台依赖，任何 AI Agent 都能用。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 目录

- [这是什么](#这是什么)
- [三种使用方式](#三种使用方式)
- [环境准备](#环境准备)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [脚本参考](#脚本参考)
- [常见问题](#常见问题)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 这是什么

这是一个**数学史 / 数学本质科普短视频系列**的完整生产技能包，原名为《万物有数》，共 8 季 67 集，适配视频号 / 抖音 / 快手 / 小红书。

**核心叙事框架**：每集讲"一个人被什么麻烦逼到墙角，然后造出了一个原本不存在的东西"，用七幕升维结构（奇景 → 困局 → 动手 → 造物 → 穿透 → 升维 → 追问）。

**本版本是通用版**：从 WorkBuddy 技能包移植而来，去除了平台特定依赖。你可以：

1. 把 `SKILL.md` 当**提示词**喂给任何 AI Agent（DeepSeek、豆包工作、千问工作、GPT、Claude 等）
2. **Clone 这个仓库**，按命令行操作
3. 按需查阅 `references/` 下的某个章节

---

## 三种使用方式

### 方式 A：把 SKILL.md 当提示词（最简单）

直接把 `SKILL.md` 的内容复制给任何 AI Agent，它会按照里面的红线和 15 步流程帮你生产视频。

```
示例用法：
"读一下这份技能文件，帮我做一集关于'零的历史'的《万物有数》短视频"
"按照 SKILL.md 的 QC-27 钩子密度门检查我的脚本"
```

### 方式 B：Clone 仓库，命令行操作（最完整）

```bash
# 1. 克隆
git clone <repo-url>
cd math-essence-video-generic

# 2. 安装 Python 依赖
pip install numpy pillow

# 3. 开新集（示例：ep06）
EP=S1_ep06_万物皆数与第一次危机
mkdir -p "$EP"
cp templates/FACTS.template.md   "$EP/FACTS.md"
cp templates/脚本骨架.template.md "$EP/脚本_ep06.md"
python scripts/progress.py init "$EP" 06 万物皆数与第一次危机

# 4. 查看当前进度
python scripts/progress.py show "$EP"

# 5. 渲染完成后跑体检
python scripts/epcheck.py "$EP"
```

### 方式 C：按需查阅 references/（最灵活）

| 遇到什么问题 | 读哪个文件 |
|---|---|
| 不知道这一集该讲什么 | `references/R1-选题与叙事.md` §2 逐季分集表 |
| 不知道怎么写开场钩子 | `references/R1-选题与叙事.md` §3.4 |
| 不知道怎么做分镜 | `references/R2-视觉系统.md` |
| 不知道怎么配声音 | `references/R3-声音与语气.md` |
| 质检报错了 | `references/R4-质检门.md` |
| 不知道完整的 15 步流程 | `references/R5-生产流程.md` |
| 遇到奇怪的 bug | `references/R6-经验库.md`（搜关键词） |
| 想做小红书九图 | `references/R7-小红书图文.md` |
| 想改这个技能本身 | `references/R8-技能维护指南.md` |

---

## 环境准备

| 依赖 | 版本要求 | 用途 | 是否必须 |
|---|---|---|---|
| Python | 3.8+ | 跑 `scripts/*.py`（需要 numpy + PIL） | 必须 |
| Node.js | 18+ | 跑 `scripts/*.js`（Chrome 渲染） | 必须 |
| Chrome / Chromium | 最新版 | 渲染 HTML 动画帧 | 必须 |
| ffmpeg / ffprobe | 最新版 | 音频处理、视频编码、体检门 | 必须 |
| MiniMax API Key | — | TTS 语音合成 | 可选 |
| Agnes API Key | — | AI 图生图 | 可选 |

### 安装依赖

```bash
# Python 依赖
pip install numpy pillow

# Node 依赖（渲染用）
npm install puppeteer playwright
```

### 脚本路径说明

所有脚本已内置自适应路径解析，无需手动配置：

- **ffmpeg/ffprobe**：自动探测 `MEV_FFMPEG` / `MEV_FFPROBE` 环境变量 → 常见安装路径 → 系统 PATH
- **Chrome/Chromium**：由渲染脚本自动探测
- **Python**：使用系统 Python 即可

如需指定自定义路径：
```bash
export MEV_FFMPEG=/path/to/ffmpeg
export MEV_FFPROBE=/path/to/ffprobe
```

---

## 快速开始

### 1. 开新集

```bash
EP=S1_ep06_万物皆数与第一次危机
mkdir -p "$EP"
cp templates/FACTS.template.md   "$EP/FACTS.md"
cp templates/脚本骨架.template.md "$EP/脚本_ep06.md"
python scripts/progress.py init "$EP" 06 万物皆数与第一次危机
python scripts/progress.py show "$EP"
```

### 2. 查看进度看板

```bash
python scripts/progress.py html "$EP"   # 生成 PROGRESS.html 可视化看板
```

### 3. 跑体检门

```bash
python scripts/epcheck.py "$EP"         # 14 项自动检查
python scripts/epcheck.py "$EP" --strict  # WARN 也算失败
```

### 4. 跑钩子密度门

```bash
python scripts/qc27_hooks.py "$EP/timeline.js"
```

### 5. 跑字幕节奏门

```bash
python scripts/qc28_subpacing.py "$EP/timeline.js"
```

### 6. 归档

```bash
# 指定归档目录
MEV_DST=/path/to/archive python scripts/archive_flat.py

# 或只归档指定集
python scripts/archive_flat.py ep04
```

---

## 目录结构

```
math-essence-video-generic/
├── SKILL.md                 # 技能入口（可当提示词用）
├── README.md                # 本文件
├── LICENSE                  # MIT 许可证
├── .gitignore               # Git 忽略规则
├── references/              # R1~R8 方法论文档
│   ├── R1-选题与叙事.md      # 季结构 / 七幕 / 变体 / 钩子范式
│   ├── R2-视觉系统.md        # 资产四级 / 动画分级 / 分镜层
│   ├── R3-声音与语气.md      # 三层声轨 / BGM / 声线
│   ├── R4-质检门.md          # QC-0~QC-29 全表
│   ├── R5-生产流程.md        # 15 步完整流程
│   ├── R6-经验库.md          # 100 条经验
│   ├── R7-小红书图文.md      # 9 图 + 文案规范
│   └── R8-技能维护指南.md    # 改 skill 前的必读
├── scripts/                 # 可直接运行的脚本
│   ├── epcheck.py           # 体检门 QC-29（14 项）
│   ├── qc27_hooks.py        # 钩子密度门
│   ├── qc28_subpacing.py    # 字幕节奏门
│   ├── qc26_overlap.js      # 重叠压字门
│   ├── audit_motion_template.py  # 运动审计模板
│   ├── progress.py          # 15 步进度跟踪
│   └── archive_flat.py      # 平铺归档 + sha256 校验
├── templates/               # 新集开工模板
│   ├── FACTS.template.md     # 事实台账
│   ├── 脚本骨架.template.md  # 七幕脚本骨架
│   ├── PROGRESS.template.json # �度进度模板
│   └── README.md            # 模板使用说明
└── assets/
    └── render_xhs_palette.js # 小红书九图生产母版
```

---

## 脚本参考

### `scripts/epcheck.py` — 体检门（QC-29）

14 项自动检查，抓低级格式错误：

| 检查 | 内容 |
|---|---|
| CK-01 | 音画时长差 |
| CK-02 | 字幕末条越界 |
| CK-03 | 字幕条重叠 |
| CK-04 | 片头 BGM |
| CK-05 | 字幕空洞 |
| CK-06 | 纯色/黑帧 |
| CK-07 | 画面模糊 |
| CK-08 | 纯文字帧 |
| CK-09 | 帧序完整 |
| CK-10 | 编码合规 |
| CK-11 | 封面尺寸 |
| CK-12 | 结尾卡停留 |
| CK-13 | 文件体积 |
| CK-14 | 图形语义匹配（人工） |

### `scripts/progress.py` — 进度跟踪

```bash
python scripts/progress.py init  <集目录> <集号> <标题>   # 初始化
python scripts/progress.py show  <集目录>                 # 查看进度
python scripts/progress.py done  <集目录> <步骤号> [备注]  # 标记完成
python scripts/progress.py gate  <集目录> <门名> PASS|FAIL # 记录门禁结果
python scripts/progress.py note  <集目录> <文字>           # 追加备注
python scripts/progress.py html  <集目录> [输出路径]       # 生成看板
```

### `scripts/qc27_hooks.py` — 钩子密度门

判定：最长无钩子间隔 ≤ 25s、前 30s 内 ≥ 1 次提问、片头后 3s 内出现母题赌注句。

### `scripts/qc28_subpacing.py` — 字幕节奏门

判定：单条字数 ≤ 22、单条停留 ≤ 4.5s、阅读速度 3.5-9.0 字/秒。

### `scripts/archive_flat.py` — 平铺归档

复制视频/封面/发布文档到目标目录，回读 sha256 逐字节校验，生成 MANIFEST。

---

## 常见问题

### Q：这个技能包和原版有什么区别？

A：原版是 WorkBuddy 技能包，依赖 WorkBuddy 平台。通用版去除了所有平台特定依赖（`agent_created` 元数据、WorkBuddy 工具引用、硬编码 Windows 路径），保留了全部核心方法论和可运行脚本。详见 [SKILL.md §0b](SKILL.md)。

### Q：我可以用它做什么？

A：你可以用它生产《万物有数》系列的任意一集——从选题分析、脚本写作、分镜设计、动画渲染到质检归档，全流程覆盖。也可以只取其中某个环节的方法论（比如只学七幕结构用在其他创作中）。

### Q：脚本能在 macOS / Linux 上跑吗？

A：可以。所有 Python 脚本已做跨平台适配（路径探测、路径拼接均使用 `os.path`）。Node 脚本同理。

### Q：我没有 MiniMax / Agnes API Key？

A：可以。TTS 可以用任何其他语音合成替代（ ElevenLabs、微软 Azure、甚至系统自带 TTS）。图生图同理，可以用任何 AI 图生图工具。脚本本身不绑定特定 API。

### Q：怎么贡献？

A：见下方「贡献」章节。

---

## 贡献

### 报告问题

在 GitHub 上开 Issue，包含：
- 问题描述
- 环境信息（OS / Python 版本 / Node 版本）
- 复现步骤
- 期望行为 vs 实际行为

### 修改技能

修改前**必读** `references/R8-技能维护指南.md`，里面写了四种常见的改坏方式和 8 项自检清单。

### 提交 PR

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/my-change`）
3. 提交更改（`git commit -m "描述"`）
4. 推送到分支（`git push origin feature/my-change`）
5. 在 GitHub 上开 Pull Request

---

## 许可证

MIT — 见 [LICENSE](LICENSE)。可自由使用、修改、分发，保留原作者署名。