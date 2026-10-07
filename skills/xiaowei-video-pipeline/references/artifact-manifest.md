# 交付清单

delivery.json 用来让下一次发布或修订复用已经验证的产物。它记录身份和证据，不保存密钥，也不把编辑历史写成 changelog。

## 最小结构

{
  "schema": 1,
  "taskId": "video-stem-2026-09-21",
  "source": {
    "path": "/absolute/path/video.mp4",
    "sha256": "...",
    "durationSeconds": 183.2,
    "videoTracks": 1,
    "audioTracks": 1
  },
  "captions": {
    "language": "zh-CN",
    "captionProfile": "social-burnin",
    "encoding": "UTF-8",
    "reviewed": true,
    "userApproved": true,
    "burnedVideo": {"path": "/absolute/path/video_subtitled.mp4", "sha256": "..."},
    "srt": {"path": "/absolute/path/video_subtitled.srt", "sha256": "..."},
    "ass": {"path": "/absolute/path/video_subtitled.ass", "sha256": "..."}
  },
  "capabilities": {
    "ffmpeg": {"status": "available", "version": "..."},
    "ocr": {"status": "unknown"},
    "transcription": {"status": "available", "provider": "..."}
  },
  "evidenceBundle": {
    "path": "/absolute/path/evidence/",
    "timelineSha256": "...",
    "keyframes": ["00:00:12.400", "00:01:08.100"]
  },
  "audio": {
    "sampleRateHz": 48000,
    "integratedLufs": -23.1,
    "loudnessRangeLu": 7.2,
    "truePeakDbtp": -1.0,
    "profile": "ebu-r128"
  },
  "covers": [
    {"aspect": "3:4", "path": "/absolute/path/video_3x4.png", "sha256": "..."},
    {"aspect": "4:3", "path": "/absolute/path/video_4x3.png", "sha256": "..."},
    {"aspect": "16:9", "path": "/absolute/path/video_16x9.png", "sha256": "..."}
  ],
  "platforms": {
    "xiaohongshu": {"status": "ready", "draftId": "...", "coverAspect": "3:4"},
    "bilibili": {"status": "ready", "draftId": "...", "coverAspect": "4:3"}
  },
  "quality": {
    "status": "pass_with_warnings",
    "report": "/absolute/path/quality.json",
    "manualChecks": ["开头同步", "中段同步", "结尾同步", "字幕不遮脸"]
  },
  "platformProfiles": {
    "youtube": {"version": "2026-09", "checkedAt": "2026-09-21", "source": "official"}
  },
  "assets": [
    {"path": "/absolute/path/music.wav", "kind": "music", "source": "...", "rightsNotes": "..."}
  ],
  "editReport": "/absolute/path/edit-report.md",
  "publish": {"finalButtonClicked": false, "userActionRequired": true}
}

## 记录规则

- status 只能使用 ready、blocked、not_requested 或 needs_user_review；平台没有运行时用 not_requested，不要猜测“已准备好”。
- 文件路径必须是绝对路径，且在写入清单前再次确认存在。SHA-256 只记录实际文件，不记录 URL 的猜测值。
- userApproved=true 必须来自当前任务的预览保存或用户本轮明确免预览授权，并保留对应的 preview-save.json 或授权原话摘要。
- pass_with_warnings 必须列出警告；没有人工抽样证据时不能写 pass。
- 平台草稿状态只代表字段和 receipt 已独立核对，不代表已经公开发布。
- 修订成片时创建新的 exports/<id>/ 和新的清单；不要在旧清单里追加编辑历史。

## 粗剪与工具链字段

启用智能粗剪或多次导出时，在 `delivery.json` 中补充这些字段；它们用于断点恢复和判断旧产物是否还能复用：

```json
{
  "timeline": {
    "schema": 1,
    "sourceSha256": "...",
    "timelineHash": "...",
    "editPlan": "/absolute/path/edit-plan.json",
    "segments": 12,
    "durationSeconds": 148.6
  },
  "toolchain": {
    "ffmpegVersion": "...",
    "ffprobeVersion": "...",
    "encoder": "libx264",
    "capabilitiesRef": "/absolute/path/capabilities.json"
  },
  "operations": [
    {
      "operationId": "op-20261007-001",
      "stage": "render",
      "status": "succeeded",
      "commandDigest": "...",
      "inputHash": "...",
      "outputHash": "...",
      "failure": null
    }
  ]
}
```

`timelineHash` 必须由源文件 hash、按时间排序的 segment、决策、字幕时间轴和相关 profile 共同计算。只改输出文件名不创建新 timeline；改变任一时间线输入就不能复用旧的字幕烧录、封面或验证结论。`operations[].status` 只能使用 `planned`、`running`、`succeeded`、`failed`、`blocked` 或 `needs_user_review`；失败要保留可读的 `failure.code`、阶段和是否可重试。
