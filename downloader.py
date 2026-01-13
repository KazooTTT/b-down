import json
import subprocess
import os
import re
from pathlib import Path


def get_bvid_from_url(url):
    """从B站视频URL提取BV ID"""
    match = re.search(r"/video/(BV\w+)", url)
    return match.group(1) if match else None


def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # 移除控制字符
    filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()


def load_downloaded_videos(tracking_file="downloaded_videos.json"):
    """加载已下载视频的记录"""
    if Path(tracking_file).exists():
        with open(tracking_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_downloaded_videos(downloaded, tracking_file="downloaded_videos.json"):
    """保存已下载视频的记录"""
    with open(tracking_file, "w", encoding="utf-8") as f:
        json.dump(downloaded, f, ensure_ascii=False, indent=2)


def is_video_downloaded(bvid, output_dir):
    """检查视频是否已经下载"""
    if not bvid:
        return False

    output_path = Path(output_dir)
    if not output_path.exists():
        return False

    # 检查是否存在包含BV ID的文件
    for file in output_path.iterdir():
        if file.is_file() and bvid in file.name:
            return True

    return False


def download_videos(
    json_file="bilibili_videos.json",
    output_dir="bilibili_videos",
    tracking_file="downloaded_videos.json",
    force=False,
):
    """从JSON文件读取视频URL并下载"""

    # 读取视频列表
    with open(json_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    # 加载已下载视频记录
    downloaded_bvids = load_downloaded_videos(tracking_file)

    print(f"准备下载 {len(videos)} 个视频到 {output_dir}/")
    print(f"已记录 {len(downloaded_bvids)} 个已下载视频")

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, video in enumerate(videos, 1):
        title = video.get("title", "N/A")
        url = video.get("url", "")

        if not url:
            continue

        # 获取BV ID
        bvid = get_bvid_from_url(url)

        if not bvid:
            print(f"\n[{idx}/{len(videos)}] 跳过: 无法从URL提取BV ID")
            print(f"URL: {url}")
            continue

        # 检查是否已下载
        if not force and bvid in downloaded_bvids:
            # 进一步检查文件是否存在
            if is_video_downloaded(bvid, output_dir):
                print(f"\n[{idx}/{len(videos)}] 跳过: 已下载 - {title}")
                skipped_count += 1
                continue

        print(f"\n[{idx}/{len(videos)}] 下载: {title}")
        print(f"URL: {url}")
        print(f"BV ID: {bvid}")

        # 清理标题作为文件名，添加BV ID以便识别
        safe_title = sanitize_filename(title)

        # 构建yt-dlp命令
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--progress",
            "-o",
            f"{output_dir}/{safe_title} [{bvid}].%(ext)s",
            url,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
            )

            if result.returncode == 0:
                print(f"✓ 下载成功: {safe_title}")
                downloaded_count += 1

                # 记录已下载的BV ID
                if bvid not in downloaded_bvids:
                    downloaded_bvids.append(bvid)
                    save_downloaded_videos(downloaded_bvids, tracking_file)
            else:
                print(f"✗ 下载失败: {safe_title}")
                print(f"错误: {result.stderr}")
                failed_count += 1

        except subprocess.TimeoutExpired:
            print(f"✗ 下载超时: {safe_title}")
            failed_count += 1
        except Exception as e:
            print(f"✗ 下载出错: {safe_title} - {str(e)}")
            failed_count += 1

    print(f"\n{'=' * 50}")
    print(f"下载完成!")
    print(f"成功: {downloaded_count}")
    print(f"跳过: {skipped_count}")
    print(f"失败: {failed_count}")
    print(f"总计: {len(videos)}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    import sys

    json_file = sys.argv[1] if len(sys.argv) > 1 else "bilibili_videos.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "bilibili_videos"
    tracking_file = sys.argv[3] if len(sys.argv) > 3 else "downloaded_videos.json"
    force = "--force" in sys.argv or "-f" in sys.argv

    download_videos(json_file, output_dir, tracking_file, force)
