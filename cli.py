#!/usr/bin/env python3
"""CLI: python cli.py video.mp4 --to vi --mode soft"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import LANGUAGES, WHISPER_MODELS
from src.pipeline import VideoTranslatePipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dich-video",
        description="Dịch video: nhận dạng giọng nói → dịch → phụ đề hoặc lồng tiếng.",
    )
    p.add_argument("video", help="Đường dẫn file video hoặc audio")
    p.add_argument("--to", dest="target", default="vi", choices=sorted(k for k in LANGUAGES if k != "auto"))
    p.add_argument("--from", dest="source", default="auto", choices=sorted(LANGUAGES.keys()))
    p.add_argument(
        "--mode",
        default="soft",
        choices=["srt", "soft", "hard", "dub"],
        help="srt=chỉ xuất chữ | soft=nhúng phụ đề | hard=ghi chữ lên hình | dub=lồng tiếng",
    )
    p.add_argument("--model", default="medium", choices=sorted(WHISPER_MODELS.keys()))
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument(
        "--voice",
        default=None,
        help="Giọng VieNeu-TTS (vd. 'Đức Trí', 'Anh Khôi') hoặc Edge TTS (vd. vi-VN-HoaiMyNeural)",
    )
    p.add_argument("--no-bilingual", action="store_true", help="Phụ đề chỉ ngôn ngữ đích")
    p.add_argument("--no-fit-timing", action="store_true", help="Không kéo/nén tốc độ TTS theo khung gốc")
    p.add_argument(
        "--no-resolve-overlap",
        action="store_true",
        help="Tắt phương án A: không tăng tốc câu trước khi chồng câu sau",
    )
    p.add_argument(
        "--max-overlap-tempo",
        type=float,
        default=1.85,
        help="Trần tăng tốc khi phát hiện chồng câu (mặc định 1.85)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipe = VideoTranslatePipeline(model_size=args.model, device=args.device)

    def progress(msg: str, pct: float) -> None:
        bar = int(pct * 24)
        print(f"\r[{'█' * bar}{'░' * (24 - bar)}] {pct:5.0%}  {msg:<48}", end="", flush=True)

    print(f"Nguồn : {args.video}")
    print(f"Dịch  : {args.source} → {args.target} | mode={args.mode} | model={args.model}")
    try:
        result = pipe.run(
            video_path=args.video,
            target_lang=args.target,
            source_lang=args.source,
            mode=args.mode,
            bilingual=not args.no_bilingual,
            voice=args.voice,
            fit_timing=not args.no_fit_timing,
            resolve_overlap=not args.no_resolve_overlap,
            max_overlap_tempo=args.max_overlap_tempo,
            progress=progress,
        )
    except Exception as exc:
        print(f"\nLỗi: {exc}", file=sys.stderr)
        return 1

    print("\n--- Kết quả ---")
    print(f"Job           : {result.job_id}")
    print(f"Ngôn ngữ gốc  : {result.detected_language}")
    print(f"Số đoạn thoại : {result.segment_count}")
    print(f"SRT dịch      : {result.srt_translated}")
    print(f"SRT gốc       : {result.srt_original}")
    print(f"SRT song ngữ  : {result.srt_bilingual}")
    print(f"JSON          : {result.transcript_json}")
    if result.output_video:
        print(f"Video ra      : {result.output_video}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
