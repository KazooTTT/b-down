# Video to Subtitle Converter

使用 sensevoice-small 模型将视频中的语音转为字幕。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 单个视频转字幕

```bash
python video_to_subtitle.py "bilibili_videos/视频文件.mp4"
```

指定输出文件：

```bash
python video_to_subtitle.py "bilibili_videos/视频文件.mp4" -o "subtitles/输出文件.srt"
```

### 批量处理

处理 bilibili_videos 目录中的所有视频：

```bash
python batch_process.py
```

字幕文件将保存在 `subtitles` 目录中。

## 依赖项

- funasr: 用于加载 sensevoice-small 模型
- torch: PyTorch 框架
- torchaudio: 音频处理
- ffmpeg-python: 音频提取
- pysrt: SRT 字幕文件生成

## 注意事项

- 首次运行时会自动下载 sensevoice-small 模型（约 100MB）
- 需要 ffmpeg 安装在系统中
- 如果有 GPU，会自动使用 CUDA 加速
