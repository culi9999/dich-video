"""Dịch từng đoạn thoại."""

from __future__ import annotations

from typing import Callable

from .transcribe import Segment

ProgressFn = Callable[[str, float], None]


class Translator:
    def __init__(self, target_lang: str = "vi", source_lang: str = "auto") -> None:
        self.target_lang = target_lang
        self.source_lang = source_lang

    def _translate_one(self, text: str) -> str:
        from deep_translator import GoogleTranslator

        src = self.source_lang if self.source_lang and self.source_lang != "auto" else "auto"
        translator = GoogleTranslator(source=src, target=self.target_lang)
        return translator.translate(text) or text

    def translate_segments(
        self,
        segments: list[Segment],
        progress: ProgressFn | None = None,
    ) -> list[Segment]:
        if self.target_lang == self.source_lang:
            for seg in segments:
                seg.translated = seg.text
            return segments

        n = max(1, len(segments))
        batch: list[str] = []
        idxs: list[int] = []
        for i, seg in enumerate(segments):
            text = (seg.text or "").strip()
            if not text:
                seg.translated = ""
                continue
            batch.append(text)
            idxs.append(i)
            if len(batch) >= 25 or i == len(segments) - 1:
                try:
                    from deep_translator import GoogleTranslator

                    src = self.source_lang if self.source_lang != "auto" else "auto"
                    translator = GoogleTranslator(source=src, target=self.target_lang)
                    translated = translator.translate_batch(batch)
                    if not isinstance(translated, list) or len(translated) != len(batch):
                        raise ValueError("batch lệch")
                    for j, dst in zip(idxs, translated):
                        segments[j].translated = (dst or segments[j].text).strip()
                except Exception:
                    for j, src_text in zip(idxs, batch):
                        try:
                            segments[j].translated = self._translate_one(src_text).strip()
                        except Exception:
                            segments[j].translated = segments[j].text
                batch, idxs = [], []
                if progress:
                    progress(f"Đã dịch {i + 1}/{n} đoạn…", 0.58 + 0.16 * (i + 1) / n)
        return segments
