# siuserxiaowei-oil-video-pipeline

一个面向 Codex、Claude Code 和通用 Agent 的视频后期 Agent Skill。

它把已录制或已剪辑视频整理成可复核的字幕成片、字幕文件、封面和平台交付包，包含源文件指纹、转录证据、字幕校对、音频与平台质检、封面 sidecar、交付清单和人工发布闸门。

## 安装

```bash
git clone https://github.com/siuserxiaowei/siuserxiaowei-oil-video-pipeline.git
cp -R siuserxiaowei-oil-video-pipeline/skills/oil-video-pipeline ~/.codex/skills/
```

Claude Code 或通用 Agent 可复制到对应的 `~/.claude/skills/` 或 `~/.agents/skills/`。

## 使用

```text
使用 oil-video-pipeline，把 /absolute/path/video.mp4 做成中文烧录字幕成片，输出 SRT、ASS、3:4 封面，并检查 YouTube 发布规格。先预览，不要发布。
```

完整流程、质量闸门、交付清单、来源审计和案例见 [`skills/oil-video-pipeline/SKILL.md`](skills/oil-video-pipeline/SKILL.md)。

## 范围

Skill 本身不包含视频、个人素材、API Key 或第三方媒体。FFmpeg 等本地工具按本机环境使用；云端转录、TTS、图像生成和平台服务的费用由对应服务决定。

本仓库当前只发布 Skill 内容，没有替用户作额外的开源许可证承诺。
