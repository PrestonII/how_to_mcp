#!/usr/bin/env python3
"""
extract_frames.py - Extract video frames at specified timestamps for how-to documentation.

Usage:
    python3 extract_frames.py --video <path_to_mp4> --output <output_dir>
    python3 extract_frames.py --video BIMIT-Plan-Orientation_2026-02-18.mp4 --output images/
"""

import argparse
import os
import json
import sys
from pathlib import Path

try:
    import imageio
    import imageio.v3 as iio
except ImportError:
    print("Install imageio: pip install imageio[ffmpeg]")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Install Pillow: pip install pillow")
    sys.exit(1)


# Key timestamps from the BIMIT Plan Orientation meeting (Feb 18, 2026)
# Format: (timestamp_seconds, filename_slug, caption)
KEY_MOMENTS = [
    # Architecture Overview (~04:00-07:30)
    (240,  "01_architecture_overview",         "Figma diagram: server-plugin architecture overview"),
    (300,  "02_data_flow_modules",              "Data flow between Module 4, 5, and 6"),
    (360,  "03_api_call_sequence",              "API call sequence diagram"),
    (420,  "04_module_relationship",            "Module relationship and dependencies"),
    (450,  "05_architecture_summary",           "Architecture summary — Plugin triggers server flow"),

    # Code Structure (~08:00-09:30)
    (480,  "06_codebase_file_nav",              "File navigation: Module 6 directory structure"),
    (510,  "07_route_area_plan_create",         "Route definition: area_plan_create endpoint"),
    (540,  "08_module_organization",            "Module organization overview"),
    (570,  "09_code_entry_point",               "Code entry point for plan generation"),

    # Airtable Integration (~17:00-18:30)
    (1020, "10_airtable_project_runs",          "Airtable: Project Runs table structure"),
    (1050, "11_airtable_asset_storage",         "Airtable: Asset storage and S3 linking"),
    (1080, "12_airtable_status_tracking",       "Airtable: Status field values and tracking"),
    (1110, "13_airtable_linked_records",        "Airtable: Linked record relationships"),

    # Terminal / Development Setup (~27:00-40:00)
    (1620, "14_terminal_npm_run_test",          "Terminal: running npm run test"),
    (1680, "15_terminal_npm_run_dev",           "Terminal: running npm run dev (local server)"),
    (1740, "16_terminal_powershell_vs_gitbash", "Terminal: PowerShell vs Git Bash configuration"),
    (1800, "17_vscode_settings",                "VS Code: recommended settings and extensions"),
    (1860, "18_terminal_server_start",          "Terminal: successful server startup output"),

    # API Testing with Postman (~32:00-35:30)
    (1920, "19_postman_local_endpoint",         "Postman: local endpoint configuration"),
    (1980, "20_postman_request_body",           "Postman: request body / payload structure"),
    (2040, "21_postman_successful_response",    "Postman: successful API response"),
    (2100, "22_postman_error_debugging",        "Postman: error response and debugging steps"),

    # Environment Configuration (~36:00-37:30)
    (2160, "23_env_file_setup",                 ".env file: required environment variables"),
    (2220, "24_env_sample_vs_example",          "Comparison: .env.sample vs .env.example"),
    (2280, "25_env_aws_keys",                   ".env: AWS S3 configuration variables"),

    # Module 5 Code Structure (~50:00-51:00)
    (3000, "26_module5_structure",              "Module 5: well-maintained codebase example"),
    (3030, "27_module5_documentation",          "Module 5: inline documentation style"),
    (3060, "28_module5_modular_arch",           "Module 5: modular architecture pattern"),
]


def timestamp_to_seconds(ts_str: str) -> float:
    """Convert MM:SS or HH:MM:SS string to seconds."""
    parts = ts_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts_str)


def extract_frame(video_path: str, timestamp_sec: float, output_path: str, width: int = 1280):
    """Extract a single frame from video at the given timestamp."""
    try:
        # Read frame at specific time using imageio
        frame = iio.imread(video_path, index=None, plugin="pyav",
                           format_hint=".mp4",
                           kwargs={"ss": timestamp_sec})
        img = Image.fromarray(frame)

        # Resize maintaining aspect ratio
        orig_w, orig_h = img.size
        if orig_w > width:
            ratio = width / orig_w
            new_h = int(orig_h * ratio)
            img = img.resize((width, new_h), Image.LANCZOS)

        img.save(output_path, "PNG", optimize=True)
        return True
    except Exception as e:
        print(f"  [WARN] Could not extract frame at {timestamp_sec}s: {e}")
        return False


def extract_frames_subprocess(video_path: str, timestamp_sec: float, output_path: str):
    """Fallback: extract frame using imageio-ffmpeg directly."""
    import subprocess
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ts = str(timestamp_sec)
    cmd = [
        ffmpeg_exe,
        "-ss", ts,
        "-i", video_path,
        "-vframes", "1",
        "-vf", "scale=1280:-1",
        "-y",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def extract_all_frames(video_path: str, output_dir: str, moments: list = None, offset_sec: float = 1.5):
    """
    Extract all key frames from the video.

    Args:
        video_path: Path to the MP4 file
        output_dir: Directory to save extracted PNG frames
        moments: List of (seconds, slug, caption) tuples. Defaults to KEY_MOMENTS.
        offset_sec: Seconds to add after cue timestamp (allow screen to update)
    """
    if moments is None:
        moments = KEY_MOMENTS

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not Path(video_path).exists():
        print(f"ERROR: Video file not found: {video_path}")
        print("Please download the video from Fireflies and place it at the specified path.")
        return []

    results = []
    print(f"Extracting {len(moments)} frames from: {video_path}")
    print(f"Output directory: {output_dir}\n")

    for ts_sec, slug, caption in moments:
        adjusted_ts = ts_sec + offset_sec
        output_file = output_dir / f"{slug}.png"

        print(f"  [{slug}] @ {adjusted_ts:.1f}s — {caption}")

        # Try primary method, fall back to subprocess
        success = extract_frame(video_path, adjusted_ts, str(output_file))
        if not success:
            success = extract_frames_subprocess(video_path, adjusted_ts, str(output_file))

        results.append({
            "timestamp": ts_sec,
            "adjusted_timestamp": adjusted_ts,
            "slug": slug,
            "caption": caption,
            "output_file": str(output_file),
            "success": success,
        })

        if success:
            print(f"    -> Saved: {output_file}")
        else:
            print(f"    -> FAILED (placeholder will be used in document)")

    # Save manifest
    manifest_path = output_dir / "frames_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved: {manifest_path}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\nExtracted {success_count}/{len(results)} frames successfully.")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract video frames at key teaching moments for how-to documentation."
    )
    parser.add_argument(
        "--video", "-v",
        default="BIMIT-Plan-Orientation_2026-02-18.mp4",
        help="Path to the meeting video file"
    )
    parser.add_argument(
        "--output", "-o",
        default="images",
        help="Output directory for extracted frames"
    )
    parser.add_argument(
        "--offset", "-s",
        type=float,
        default=1.5,
        help="Seconds to add after timestamp to allow screen to update (default: 1.5)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all key moments without extracting"
    )
    args = parser.parse_args()

    if args.list:
        print("Key moments to be extracted:\n")
        for ts, slug, caption in KEY_MOMENTS:
            mins, secs = divmod(ts, 60)
            print(f"  {int(mins):02d}:{int(secs):02d}  {slug}")
            print(f"         {caption}\n")
        return

    extract_all_frames(args.video, args.output, offset_sec=args.offset)


if __name__ == "__main__":
    main()
