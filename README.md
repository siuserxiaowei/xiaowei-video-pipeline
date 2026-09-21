# Xiaowei Video Pipeline

`xiaowei-video-pipeline` 是一个面向 Codex、Claude Code 和通用 Agent 的视频后期 Skill 仓库。它把已录制或已剪辑的视频，整理成可复核、可恢复、可发布的成片交付包。

仓库中的 Skill 内部名称是 `xiaowei-video-pipeline`，这样可以和已有的 `字幕工作流`、`封面工作流`、`视觉工作流` 工作流保持兼容。

> Copyright © 2026 Xiaowei. All rights reserved. 本仓库保留全部权利，未授予复制、修改、再发布、商业使用或重新打包的许可。查看本仓库不等于获得授权。

## 它解决什么问题

普通的“给视频加字幕”通常只生成一个最终 MP4，难以回答这些问题：

- 字幕中的产品名、数字、命令和版本号是否真的听到了？
- 原视频变更后，旧字幕和封面是否还可以继续使用？
- 应该输出烧录字幕、可关闭字幕，还是单独的 SRT/VTT？
- YouTube、短视频平台和横竖屏版本是否用了正确的规格？
- 音频是否削波，字幕是否遮住人脸或界面文字？
- 音乐、B-roll、Logo 和字体的来源是否有记录？
- 渲染失败后能否从中断阶段恢复，而不是全部重做？

这个 Skill 用任务目录、源文件指纹、阶段状态、证据文件、质量闸门和交付清单回答这些问题。

## 功能总览

### 1. 任务路由

根据请求选择最小必要流程：

- 只要字幕：执行转录、校对、断句、SRT/ASS/烧录分支。
- 只要封面：执行当前视频帧筛选、多画幅封面和文字检查。
- 要字幕加封面：组合字幕和封面分支。
- 要完整成片：执行口播时间线、音频、B-roll/MG、音乐/配音、字幕、导出和平台交付。
- 要程序化视频：把字幕转换为结构化 Caption 数据，交给 Remotion 或其他渲染流程。

Skill 不会因为某个工具可用就自动启用全部处理类型。

### 2. 源文件锁定与可恢复任务

- 记录源视频绝对路径、文件大小、修改时间、时长、视频 SHA-256、视频轨道和音轨。
- 源文件指纹变化时创建新任务，不覆盖旧任务。
- 使用独立的 `<视频名>.oil-video-task/` 和 `exports/<id>/`。
- 阶段状态包括 `created`、`transcribing`、`awaiting_agent_review`、`awaiting_user_review`、`approved`、`exported` 和 `blocked`。
- 失败时从失败阶段恢复，不重复运行已经确认的 ASR 或覆盖定稿。

### 3. 能力预检

开始前记录本机能力快照：

- FFmpeg 和 ffprobe 是否可用；
- 视频和音频编码器是否可用；
- 字幕烧录能力和字体是否可用；
- OCR、转录 provider 和 TTS 是否可用；
- 视频轨道、音轨和可用磁盘空间是否满足任务；
- 能力状态是 `available`、`missing` 还是 `unknown`。

未知能力会被显式记录，不会静默假设工具存在。

### 4. 转录与字幕校对

- 优先复用同源且已审校的字幕，不重复跑 ASR。
- 保留原始 transcript、词级时间戳、置信度和审校稿。
- 低置信度、产品名、数字、命令、版本号、否定词和说话人变化必须抽样回听。
- 每处 Agent 改词都写入 `review-evidence.json`，记录音频时间段或匹配画面证据。
- 无法确认的词保留原文或疑点，不根据常识猜测。
- 只修改 `text`，不破坏时间码、token、置信度和条目顺序。
- 中文字幕支持中文、英文/数字边界空格、章节和安全区排版。

### 5. 三种字幕 profile

任务开始先声明字幕用途：

- `subtitle`：只承载对白，适合基础字幕文件。
- `captions`：除对白外，还表达关键音效、音乐、说话人和画外声音，适合无障碍场景。
- `social-burnin`：烧录到画面中，服从平台安全区、画面节奏和短视频可读性。

输出可以选择：

- 烧录字幕 MP4：字幕永久写入画面；
- 软字幕容器：字幕可以开关或切换语言；
- SRT/VTT：给剪辑器或平台上传；
- ASS：需要字体、位置、描边和样式时使用。

所有字幕文件使用 UTF-8。SRT 不承担完整样式和定位能力。

### 6. 口播、B-roll、MG、音乐和配音顺序

依赖顺序默认是：

```text
A-roll / 口播时间线
→ 音频平滑与混音
→ B-roll / MG 动画
→ 音乐 / 配音
→ 字幕
→ 导出与验证
```

时间线变化后，下游字幕、画面层和导出都要按新指纹复核。Skill 不会用 TTS 替换已经正确的原声，也不会在用户没有选择时擅自加入歌曲、音乐或配音。

### 7. 音频质量检查

启用音频 profile 时记录：

- 采样率；
- integrated loudness；
- loudness range；
- maximum true peak；
- 语音是否被音乐遮盖；
- 是否出现削波和明显失真。

可使用 FFmpeg `loudnorm` 做测量或双遍处理。广播型 EBU profile 可以使用 -23 LUFS；社交平台不能未经选择就套用这个目标。

### 8. 多画幅封面

默认可以准备：

- 小红书：3:4；
- B 站或通用横版：4:3；
- B 站个人空间或横版用途：16:9。

每个封面保留：

- 当前视频参考帧；
- 主标题和副标题来源；
- prompt；
- 分析结果；
- 生成响应；
- 最终图片 sidecar；
- Logo、人物和素材来源。

封面文字逐字检查，不允许模型自行添加当前素材之外的品牌、人物、数字或文案。

### 9. 平台 profile

平台规格保存为带版本和日期的 profile，不把一次搜索结果当成永久规则。

YouTube profile 至少检查：

- MP4 和 fast start；
- H.264 视频；
- AAC/Opus 音频；
- 48 kHz；
- 逐行扫描；
- 与录制源一致的帧率；
- BT.709 色彩信息。

短视频 profile 至少检查：

- 9:16 画幅；
- 关键内容安全区；
- 清晰度；
- 人声可懂度；
- 音乐授权；
- 当前平台的时长和文件大小限制。

Skill 只准备和核对平台草稿，不点击最终公开发布按钮。

### 10. 验证与交付文件

常见任务目录：

```text
视频名.oil-video-task/
├── task.json
├── source.json
├── transcript.json
├── reviewed-transcript.json
├── review-evidence.json
├── captions.json
├── preview-save.json
├── quality.json
├── verification.json
├── evidence/
├── cover/
├── exports/<id>/
└── delivery.json
```

最终交付可以包含：

- 字幕成片 MP4；
- 中文 SRT；
- ASS 或 VTT；
- 英文 SRT；
- 3:4、4:3、16:9 封面；
- `quality.json`；
- `verification.json`；
- `delivery.json`；
- `edit-report.md`；
- evidence bundle。

交付前至少检查开头、中段和结尾的音画同步、字幕遮挡、文件可播放性、时长、音轨、抽帧画面和任务指纹。

## 安装

### Codex

```bash
git clone https://github.com/siuserxiaowei/xiaowei-video-pipeline.git
cp -R xiaowei-video-pipeline/skills/xiaowei-video-pipeline ~/.codex/skills/
```

安装后重新打开 Codex 或开启新任务，让它重新发现 Skill。

### Claude Code

```bash
cp -R xiaowei-video-pipeline/skills/xiaowei-video-pipeline ~/.claude/skills/
```

### 通用 Agent

复制到对应的 Agent Skill 目录：

```bash
cp -R xiaowei-video-pipeline/skills/xiaowei-video-pipeline ~/.agents/skills/
```

## 使用示例

### 完整成片

```text
使用 xiaowei-video-pipeline，把 /absolute/path/demo.mp4 做成中文视频成片。
要求：烧录字幕、输出中文 SRT 和 ASS、生成 3:4/4:3/16:9 封面，目标平台是 YouTube 和小红书。
先预览和质检，不要点击发布。
```

### 只做字幕

```text
使用 xiaowei-video-pipeline，只处理 /absolute/path/demo.mp4 的中文字幕。
输出 SRT、ASS 和烧录 MP4，不生成封面，不做平台上传。
```

### 屏幕录制校对

```text
使用 xiaowei-video-pipeline，校对这个屏幕录制里的产品名、命令和版本号。
所有改词必须保留音频或同时间画面证据，不确定的地方标记出来。
```

### 只准备平台交付包

```text
使用 xiaowei-video-pipeline，检查这个已经剪好的 MP4 是否符合 YouTube 和竖屏短视频 profile，
生成 delivery.json、quality.json 和需要修复的问题，不要重新剪辑和发布。
```

## 不做什么

- 不替用户点击最终发布按钮；
- 不凭常识补写听不清的产品名、数字、命令或版本；
- 不覆盖用户已有视频、字幕、封面或定稿；
- 不把原始用户视频、个人素材、API Key 或账号登录态打包进仓库；
- 不把某个平台某一天的规格当成所有平台的永久规则；
- 不保证模型自动完成精确节拍剪辑、口型同步或审美判断；
- 不自动决定付费转录、TTS、图片生成或第三方云服务。

## 费用与依赖

Skill 本身是说明文件，不单独收费，也不需要充值。使用时会消耗 Codex 或其他 Agent 的正常模型上下文和使用额度；任务越长、视频证据越多、校对越细，正常模型用量通常越高。

本地 FFmpeg、文件校验和字幕整理通常只消耗本机 CPU、磁盘和时间。云端转录、TTS、图片生成、ChatCut 或平台 API 是否收费，由对应服务的账户和套餐决定。

## 仓库结构

```text
README.md
skills/
└── xiaowei-video-pipeline/
    ├── SKILL.md
    └── references/
        ├── artifact-manifest.md
        ├── examples.md
        ├── quality-gates.md
        └── skill-lineage.md
```

详细规则和案例入口：

- [Skill 主说明](skills/xiaowei-video-pipeline/SKILL.md)
- [质量闸门](skills/xiaowei-video-pipeline/references/quality-gates.md)
- [交付清单格式](skills/xiaowei-video-pipeline/references/artifact-manifest.md)
- [使用案例](skills/xiaowei-video-pipeline/references/examples.md)
- [来源审计](skills/xiaowei-video-pipeline/references/skill-lineage.md)
