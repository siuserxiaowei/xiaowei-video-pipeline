# 媒体能力快照与回退合同

能力探测的目标是记录“当前机器能做什么”，不是自动安装依赖或保证所有功能成功。执行任务开始时运行：

```bash
python3 scripts/media_doctor.py --root /absolute/path/task-dir --output /absolute/path/task-dir/capabilities.json
```

把结果的 `schema`、生成时间、工具版本、FFmpeg filters/encoders、可用磁盘和缺失项写入 `task.json.capabilities`。没有这个快照时，不把字幕烧录、GPU 编码、Whisper、OCR、下载或 TTS 写成已可用。

## 路由规则

1. `ffprobe` 可用时先探测容器、轨道、时长、帧率、分辨率、色彩和音频；不可用时停止媒体处理，不用文件扩展名猜格式。
2. 需要远程媒体时才调用 `yt-dlp` 或已授权的媒体入口。记录 URL、下载命令版本、下载时间、最终文件 SHA-256 和失败原因；不把 Cookie、token 或完整私有 URL 写入公开清单。
3. 需要字幕烧录时检查 `subtitles`/`ass`/`drawtext`；缺失就切换到软字幕、ASS 文件或 PNG overlay，并在 `quality.json` 标成 warning/error。
4. 需要转录时先复用同源已审校 transcript；没有就选择已配置的本地/远程 provider，记录语言、模型、版本和实际状态。
5. 需要硬件编码时从当前 `ffmpeg -encoders` 结果选编码器并做短片 smoke test；失败回退到 `libx264` 或明确阻塞。不要把“检测到 GPU”直接当成“编码可用”。
6. 需要目标体积时计算目标视频 bitrate、保留音频预算和最小可接受画质，使用结构化两遍编码日志；不要只依据 FFmpeg 的退出码，必须检查输出文件、时长、大小和可播放性。

## 证据状态

每项能力只能使用 `available`、`missing`、`unknown` 或 `error`。`available` 只表示探测或 smoke test 成功；它不替代最终文件验证。能力变化、源文件变化或导出机器变化后重新运行 doctor。
