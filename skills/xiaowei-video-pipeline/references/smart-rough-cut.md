# 智能粗剪与可交换编辑计划

这个分支把“自动剪辑”限制在可复核的粗剪建议上。它借鉴了转录到 EDL、场景分析、预览优先和 NLE 可交换输出的做法，但不把第三方项目的命令、默认风格或云服务依赖带进来。

## 何时启用

用户明确要求以下任一项时启用：去停顿、去口头禅、去重录、找高光、找多人/特定画面、生成粗剪、输出剪辑清单、为 Premiere/Resolve/Final Cut 准备可交换时间线。只要字幕、封面或导出规格时不要自动启用。

## 固定管线

```text
probe → transcript/scene index → edit-plan → preview/contact sheet
→ lint → user review or explicit no-preview → render → verify
```

每次决策必须落到 `edit-plan.json`。模型可以提出剪切建议，不能把自然语言判断直接变成不可追溯的 FFmpeg 命令。

## 三种模式

- `conservative`：只剪明显静音、重复废片和明确错误；保留完整语义单元。
- `balanced`：在保留语义完整的前提下处理长停顿、口头禅、明显重录和离题段落；默认模式。
- `aggressive`：适合短视频快剪，允许更密集剪切，但必须输出被删除的 cue、原因和人工复核点。

默认规则：不能跨不同说话人、不同 retake 或不连续语义拼接；无法判断时保留原片。静音检测、ASR 置信度、场景切换、重复相似度和目标时长只能作为证据，不能单独证明“应该删”。

## `edit-plan.json` 最小合同

```json
{
  "schema": 1,
  "mode": "balanced",
  "source": {
    "path": "/absolute/path/input.mp4",
    "sha256": "...",
    "durationSeconds": 183.2
  },
  "segments": [
    {
      "id": "seg-001",
      "action": "keep",
      "startSeconds": 0.0,
      "endSeconds": 12.4,
      "confidence": 0.98,
      "reasonCodes": ["opening"],
      "evidence": [{"type": "transcript", "cueIds": [0, 1, 2]}]
    },
    {
      "id": "seg-002",
      "action": "cut",
      "startSeconds": 12.4,
      "endSeconds": 15.1,
      "confidence": 0.91,
      "reasonCodes": ["long_pause"],
      "evidence": [{"type": "audio", "startSeconds": 12.4, "endSeconds": 15.1}]
    }
  ],
  "outputs": {"cutList": "cut-list.json", "preview": "preview.mp4"},
  "qa": {"manualChecks": ["语义连续", "切点无爆音", "开头中段结尾同步"]}
}
```

`segments` 必须按时间排序、不能重叠，至少有一个 `keep`。所有时间以秒保存，导出到 EDL/FCPXML/FFconcat 时再转换成目标格式。`reasonCodes` 使用稳定的短码，例如 `long_pause`、`filler`、`retake`、`off_topic`、`duplicate`、`scene_match`、`manual_keep`。每个 `cut` 和重要 `keep` 都要有 transcript、audio、frame、scene 或用户指令证据中的至少一种。

用随包脚本验证：

```bash
python3 scripts/validate_edit_plan.py /absolute/path/edit-plan.json
```

## 预览和导出

先输出低码率预览、contact sheet 和 `edit-report.md`。报告至少列出：删除时长、保留时长、每个 cut 的时间码、原因、证据、置信度、预期风险和人工检查项。

得到用户预览保存证据或明确的免预览授权后才渲染最终视频。需要跨剪辑器时优先输出时间码级 `cut-list.json`，再按目标工具生成 EDL、FCPXML 或 Resolve XML；不要把某个 NLE 的 XML 当作唯一真相。

## 音视频实现边界

- 能 stream copy 就优先无损切割；切点不在关键帧时明确说明需要重编码。
- FFmpeg 命令显式 `-map 0:v? -map 0:a?`，默认不使用 `-y` 覆盖已有文件。
- 目标体积压缩用两遍编码时，两遍必须共享同一个绝对 `passlogfile`，失败要清理临时日志并返回结构化错误；不要同时设置 CRF 和目标 bitrate。
- 硬件编码器必须先在当前机器的 encoder 列表中出现，再做短片 smoke test；macOS VideoToolbox、QSV、NVENC 和 VAAPI 不能凭平台名称互相替代。
- 缺少 `drawtext`、`subtitles` 或 `ass` 滤镜时，记录能力缺口，选择 ASS/PNG overlay 或纯字幕文件回退，不假装已经烧录。

## 人工闸门

以下情况直接暂停最终渲染：源文件指纹变化；粗剪会跨语义拼接；低置信度的专有名词或数字落在剪切边界；智能剪辑没有证据；预览与最终输出参数不一致；或输出路径会覆盖已有定稿。
