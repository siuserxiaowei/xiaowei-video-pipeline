# 使用案例与失败恢复

## 正向案例：讲话视频粗剪与字幕成片

准备：本地 MP4、用户选择 `balanced`、中文、输出 SRT/ASS/烧录 MP4，未授权时保留预览。

处理：运行 `media_doctor.py`，锁定源文件并生成 `source.json`；复用或生成 transcript；根据静音、重复和场景证据写 `edit-plan.json`；生成 preview/contact sheet；通过 `validate_edit_plan.py` 后等待用户保存预览；再按新的 `timelineHash` 生成字幕、烧录视频和封面。

验收：`edit-plan.json` 结构通过；每个 cut 有证据；`verification.json` 包含 ffprobe、开头/中段/结尾抽样、音频测量和实际编码器；`delivery.json` 的源、时间线、字幕和输出 hash 一致。

## 边界案例：当前 FFmpeg 没有字幕滤镜

准备：`capabilities.json` 中 `subtitles`、`ass` 或 `drawtext` 为 `missing`，用户要求烧录字幕。

处理：停止假装烧录成功，给出三个可验证路径：换用已安装的 FFmpeg 构建、输出 ASS/SRT 软字幕、或使用 PNG overlay 重新生成预览。把选择和能力缺口写进 `quality.json`，不覆盖旧 MP4。

验收：最终文件的字幕形态与交付清单一致；如果没有烧录，不能把它写成“字幕已写入画面”。

## 失败恢复：两遍压缩第二遍失败

准备：目标大小压缩的第一遍已生成日志，但第二遍找不到统计文件或输出为 0 字节。

处理：把 stage 标为 `failed`，保留错误码和命令摘要；检查两遍是否使用同一个绝对 `passlogfile`，清理属于本次 operation 的临时日志，修复后从压缩阶段恢复，不重跑 ASR、校对或封面。

验收：第二遍退出码为 0 只是必要条件；还要检查输出存在、可播放、时长在容差内、大小达到目标、音视频轨道正确，并把实际结果写入 `verification.json`。
