import os
import subprocess
import torch
import numpy as np
import pysrt
from funasr import AutoModel
from pathlib import Path


class VideoToSubtitle:
    def __init__(self):
        print("Loading sensevoice-small model...")
        self.model = AutoModel(
            model="iic/SenseVoiceSmall",
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 30000},
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        print("Model loaded successfully!")

    def extract_audio(self, video_path, audio_path=None):
        if audio_path is None:
            audio_path = str(Path(video_path).with_suffix(".wav"))

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            audio_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return audio_path

    def transcribe(self, audio_path):
        res = self.model.generate(
            input=audio_path, cache={}, language="auto", use_itn=True, batch_size_s=300
        )
        return res

    def create_srt(self, transcription_result, output_path):
        subs = pysrt.SubRipFile()

        for result in transcription_result:
            if "sentence_info" not in result:
                continue

            for seg in result["sentence_info"]:
                start_time = seg["start"] / 1000
                end_time = seg["end"] / 1000

                sub = pysrt.SubRipItem(
                    index=len(subs) + 1,
                    start=pysrt.SubRipTime(seconds=start_time),
                    end=pysrt.SubRipTime(seconds=end_time),
                    text=seg["text"],
                )
                subs.append(sub)

        subs.save(output_path, encoding="utf-8")

    def process_video(self, video_path, output_srt=None):
        if output_srt is None:
            output_srt = str(Path(video_path).with_suffix(".srt"))

        print(f"Processing: {video_path}")

        audio_path = self.extract_audio(video_path)
        print(f"Audio extracted to: {audio_path}")

        transcription = self.transcribe(audio_path)
        print(f"Transcription completed")

        self.create_srt(transcription, output_srt)
        print(f"Subtitle saved to: {output_srt}")

        return output_srt


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert video speech to subtitles using sensevoice-small"
    )
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("-o", "--output", help="Output SRT file path", default=None)

    args = parser.parse_args()

    converter = VideoToSubtitle()
    converter.process_video(args.video_path, args.output)


if __name__ == "__main__":
    main()
