"""Thao tác video/audio bằng ffmpeg + ffprobe."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class FFmpegError(RuntimeError):
    pass


def _run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise FFmpegError(
            "Không tìm thấy ffmpeg/ffprobe. Cài đặt: https://ffmpeg.org/download.html"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise FFmpegError(exc.stderr.strip() or str(exc)) from exc


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise FFmpegError("Cần ffmpeg và ffprobe trong PATH trước khi chạy pipeline.")


def probe(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    result = _run(cmd)
    return json.loads(result.stdout)


def duration_seconds(path: Path) -> float:
    info = probe(path)
    raw = info.get("format", {}).get("duration")
    if raw is None:
        return 0.0
    return float(raw)


def extract_audio(video_path: Path, wav_path: Path, sample_rate: int = 16000) -> Path:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = wav_path.with_suffix(".tmp.wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(tmp),
    ]
    _run(cmd)
    tmp.replace(wav_path)
    return wav_path


def mux_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    original_mix: float = 0.0,
    srt_path: Path | None = None,
) -> Path:
    """Ghép video gốc với audio mới. original_mix=0.12 giữ ~12% tiếng gốc."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(output_path.stem + ".tmp" + output_path.suffix)
    mix = max(0.0, min(1.0, float(original_mix or 0.0)))
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path)]
    if srt_path is not None:
        cmd += ["-i", str(srt_path)]
    if mix > 0:
        cmd += [
            "-filter_complex",
            f"[0:a]volume={mix}[a0];[1:a]volume=1.0[a1];"
            "[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
        ]
    else:
        cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    if srt_path is not None:
        cmd += ["-map", "2:s:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=vie"]
    cmd += [
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(tmp),
    ]
    _run(cmd)
    tmp.replace(output_path)
    return output_path


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    font_name: str = "Arial",
    font_size: int = 22,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(output_path.stem + ".tmp" + output_path.suffix)
    srt_escaped = (
        str(srt_path.resolve())
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", r"\'")
    )
    style = (
        f"FontName={font_name},FontSize={font_size},"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0,MarginV=28"
    )
    vf = f"subtitles='{srt_escaped}':force_style='{style}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        str(tmp),
    ]
    _run(cmd)
    tmp.replace(output_path)
    return output_path


def soft_subs(video_path: Path, srt_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(output_path.stem + ".tmp" + output_path.suffix)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(srt_path),
        "-c",
        "copy",
        "-c:s",
        "mov_text",
        "-metadata:s:s:0",
        "language=vie",
        "-movflags",
        "+faststart",
        str(tmp),
    ]
    _run(cmd)
    tmp.replace(output_path)
    return output_path


def change_tempo(audio_path: Path, output_path: Path, tempo: float) -> Path:
    if abs(tempo - 1.0) < 0.02:
        if audio_path.resolve() != output_path.resolve():
            shutil.copy2(audio_path, output_path)
        return output_path

    filters: list[str] = []
    remaining = tempo
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.4f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp" + output_path.suffix)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-filter:a",
        ",".join(filters),
        str(tmp),
    ]
    _run(cmd)
    tmp.replace(output_path)
    return output_path
