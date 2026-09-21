"""Xuất / đọc phụ đề SRT."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import srt

from .transcribe import Segment


def _td(seconds: float) -> timedelta:
    safe = max(0.0, float(seconds))
    return timedelta(seconds=safe)


def segments_to_srt(segments: list[Segment], use_translated: bool = True) -> str:
    items = []
    for i, seg in enumerate(segments, start=1):
        content = (seg.translated if use_translated else seg.text) or seg.text
        items.append(
            srt.Subtitle(
                index=i,
                start=_td(seg.start),
                end=_td(max(seg.end, seg.start + 0.4)),
                content=content.strip(),
            )
        )
    return srt.compose(items)


def write_srt(segments: list[Segment], path: Path, use_translated: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(segments_to_srt(segments, use_translated), encoding="utf-8")
    return path


def write_bilingual_srt(segments: list[Segment], path: Path) -> Path:
    items = []
    for i, seg in enumerate(segments, start=1):
        src = (seg.text or "").strip()
        dst = (seg.translated or src).strip()
        content = dst if dst == src else f"{dst}\n{src}"
        items.append(
            srt.Subtitle(
                index=i,
                start=_td(seg.start),
                end=_td(max(seg.end, seg.start + 0.4)),
                content=content,
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(srt.compose(items), encoding="utf-8")
    return path
