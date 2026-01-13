import os
import json
from pathlib import Path
from video_to_subtitle import VideoToSubtitle


RECORD_FILE = "processing_records.json"


def load_records():
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_records(records):
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def batch_process(input_dir, output_dir=None):
    if output_dir is None:
        output_dir = input_dir

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    records = load_records()
    converter = VideoToSubtitle()

    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]

    video_files = []
    for ext in video_extensions:
        video_files.extend(Path(input_dir).glob(f"*{ext}"))

    print(f"Found {len(video_files)} video files")

    for video_file in sorted(video_files):
        video_key = str(video_file)

        if video_key in records and records[video_key].get("status") == "completed":
            print(f"Skipping {video_file.name} - already processed")
            continue

        try:
            output_srt = output_dir / video_file.with_suffix(".srt").name
            converter.process_video(str(video_file), str(output_srt))

            records[video_key] = {
                "status": "completed",
                "output_srt": str(output_srt),
                "processed_at": str(Path(video_file).stat().st_mtime),
            }
            save_records(records)

            print("-" * 50)
        except Exception as e:
            records[video_key] = {"status": "failed", "error": str(e)}
            save_records(records)
            print(f"Error processing {video_file}: {e}")


if __name__ == "__main__":
    input_dir = "bilibili_videos"
    output_dir = "subtitles"

    batch_process(input_dir, output_dir)
