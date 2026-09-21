"""Pipeline chính: video → audio → transcript → dịch → phụ đề / lồng tiếng."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Literal

from . import media
from .config import OUTPUT_DIR, TEMP_DIR
from .subtitles import write_bilingual_srt, write_srt
from .transcribe import Segment, Transcriber
from .translate import Translator
from .tts import build_dub_track

ProgressFn = Callable[[str, float], None]
Mode = Literal["srt", "soft", "hard", "dub"]


@dataclass
class JobResult:
    job_id: str
    source_video: str
    output_video: str | None
    srt_translated: str
    srt_original: str
    srt_bilingual: str
    transcript_json: str
    detected_language: str
    segment_count: int
    mode: str


class VideoTranslatePipeline:
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "auto",
        work_root: Path | None = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.work_root = Path(work_root) if work_root else OUTPUT_DIR

    def run(
        self,
        video_path: str | Path,
        target_lang: str = "vi",
        source_lang: str = "auto",
        mode: Mode = "soft",
        bilingual: bool = True,
        voice: str | None = None,
        fit_timing: bool = True,
        resolve_overlap: bool = True,
        max_overlap_tempo: float = 1.85,
        progress: ProgressFn | None = None,
    ) -> JobResult:
        media.require_ffmpeg()
        video_path = Path(video_path).expanduser().resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Không thấy file: {video_path}")

        job_id = uuid.uuid4().hex[:10]
        job_dir = self.work_root / job_id
        tmp_dir = TEMP_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        def report(msg: str, pct: float) -> None:
            if progress:
                progress(msg, max(0.0, min(1.0, pct)))

        report("Đang phân tích video…", 0.04)
        wav_path = tmp_dir / "audio_16k.wav"
        media.extract_audio(video_path, wav_path)
        total_dur = media.duration_seconds(video_path)

        report("Bắt đầu nhận dạng giọng nói…", 0.12)
        transcriber = Transcriber(model_size=self.model_size, device=self.device)
        segments, detected = transcriber.run(wav_path, source_lang=source_lang, progress=report)
        if not segments:
            raise RuntimeError("Không nhận được lời thoại nào. Kiểm tra video có tiếng nói rõ không.")

        src_for_mt = source_lang if source_lang != "auto" else detected
        if src_for_mt == "zh":
            src_for_mt = "zh-CN"

        translator = Translator(target_lang=target_lang, source_lang=src_for_mt)
        segments = translator.translate_segments(segments, progress=report)

        srt_vi = write_srt(segments, job_dir / "translated.srt", use_translated=True)
        srt_src = write_srt(segments, job_dir / "original.srt", use_translated=False)
        srt_bi = write_bilingual_srt(segments, job_dir / "bilingual.srt")

        transcript_path = job_dir / "transcript.json"
        transcript_path.write_text(
            json.dumps(
                {
                    "detected_language": detected,
                    "target_language": target_lang,
                    "segments": [asdict(s) for s in segments],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        output_video: Path | None = None
        stem = video_path.stem
        ext = video_path.suffix or ".mp4"

        if mode == "srt":
            report("Đã xuất phụ đề SRT.", 1.0)
        elif mode == "soft":
            report("Đang nhúng phụ đề mềm…", 0.86)
            srt_use = srt_bi if bilingual else srt_vi
            output_video = media.soft_subs(video_path, srt_use, job_dir / f"{stem}.soft{ext}")
            report("Xong nhúng phụ đề mềm.", 1.0)
        elif mode == "hard":
            report("Đang ghi phụ đề cứng (re-encode)…", 0.86)
            srt_use = srt_bi if bilingual else srt_vi
            output_video = media.burn_subtitles(video_path, srt_use, job_dir / f"{stem}.sub{ext}")
            report("Xong phụ đề cứng.", 1.0)
        elif mode == "dub":
            report("Đang tổng hợp giọng đọc…", 0.78)
            dub_wav = tmp_dir / "dub.wav"
            build_dub_track(
                segments=segments,
                total_duration=total_dur,
                work_dir=tmp_dir / "tts",
                output_wav=dub_wav,
                target_lang=target_lang,
                voice=voice,
                fit_timing=fit_timing,
                progress=report,
                resolve_overlap=resolve_overlap,
                max_overlap_tempo=max_overlap_tempo,
            )
            report("Đang ghép audio mới vào video…", 0.96)
            output_video = media.mux_audio(
                video_path,
                dub_wav,
                job_dir / f"{stem}.dub{ext}",
                original_mix=0.12,
                srt_path=srt_vi,
            )
            report("Xong lồng tiếng.", 1.0)
        else:
            raise ValueError(f"Mode không hỗ trợ: {mode}")

        shutil.rmtree(tmp_dir, ignore_errors=True)

        return JobResult(
            job_id=job_id,
            source_video=str(video_path),
            output_video=str(output_video) if output_video else None,
            srt_translated=str(srt_vi),
            srt_original=str(srt_src),
            srt_bilingual=str(srt_bi),
            transcript_json=str(transcript_path),
            detected_language=detected,
            segment_count=len(segments),
            mode=mode,
        )
