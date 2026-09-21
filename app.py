#!/usr/bin/env python3
"""Giao diện Streamlit — chạy: streamlit run app.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.config import (
    EDGE_VOICE_ALTERNATES,
    EDGE_VOICE_MAP,
    LANGUAGES,
    OUTPUT_DIR,
    VIENEU_VOICES,
    WHISPER_MODELS,
)
from src.pipeline import VideoTranslatePipeline

st.set_page_config(
    page_title="Dịch Video",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: "Be Vietnam Pro", sans-serif; }
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0ea5e9 160%);
    color: #f8fafc;
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    margin-bottom: 1.2rem;
}
.hero h1 { font-size: 2rem; margin: 0 0 .35rem 0; letter-spacing: -.02em; }
.hero p { margin: 0; opacity: .88; }
.stProgress > div > div > div { background: linear-gradient(90deg, #38bdf8, #22c55e); }
div[data-testid="stMetric"] {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: .4rem .8rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
<div class="hero">
  <h1>🎬 Dịch Video</h1>
  <p>Nhận dạng lời thoại → dịch ngôn ngữ → xuất phụ đề hoặc lồng tiếng VieNeu-TTS. Chạy trên máy bạn.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Cấu hình")
    lang_items = [(k, v) for k, v in LANGUAGES.items()]
    src_keys = [k for k, _ in lang_items]
    tgt_keys = [k for k in src_keys if k != "auto"]

    source_lang = st.selectbox(
        "Ngôn ngữ gốc",
        options=src_keys,
        format_func=lambda k: LANGUAGES[k],
        index=0,
    )
    target_lang = st.selectbox(
        "Ngôn ngữ đích",
        options=tgt_keys,
        format_func=lambda k: LANGUAGES[k],
        index=tgt_keys.index("vi") if "vi" in tgt_keys else 0,
    )

    mode_labels = {
        "soft": "Nhúng phụ đề mềm (bật/tắt trong player)",
        "hard": "Ghi phụ đề cứng lên hình",
        "srt": "Chỉ xuất file SRT + bản dịch",
        "dub": "Lồng tiếng (VieNeu-TTS / Edge) + giữ hình gốc",
    }
    mode = st.selectbox("Chế độ xuất", options=list(mode_labels), format_func=lambda k: mode_labels[k])
    bilingual = st.checkbox("Phụ đề song ngữ (đích + gốc)", value=True, disabled=mode == "dub")

    st.divider()
    model_size = st.selectbox(
        "Model Whisper",
        options=list(WHISPER_MODELS),
        index=list(WHISPER_MODELS).index("medium"),
        format_func=lambda k: f"{k} — {WHISPER_MODELS[k]}",
    )
    device = st.selectbox("Thiết bị", options=["auto", "cpu", "cuda"], index=0)

    if target_lang == "vi":
        voices = list(VIENEU_VOICES) + list(EDGE_VOICE_ALTERNATES.get("vi", []))
    else:
        voices = EDGE_VOICE_ALTERNATES.get(target_lang) or [
            EDGE_VOICE_MAP.get(target_lang, "en-US-JennyNeural")
        ]
    voice = st.selectbox("Giọng lồng tiếng (VieNeu-TTS / Edge)", options=voices, disabled=mode != "dub")
    fit_timing = st.checkbox("Khớp nhịp thoại gốc (kéo/nén TTS)", value=True, disabled=mode != "dub")
    resolve_overlap = st.checkbox(
        "Phát hiện chồng câu → tăng tốc câu trước (tránh cắt giữa từ)",
        value=True,
        disabled=mode != "dub",
    )
    max_overlap_tempo = st.slider(
        "Trần tăng tốc khi chồng câu",
        min_value=1.20,
        max_value=2.00,
        value=1.85,
        step=0.05,
        disabled=mode != "dub" or not resolve_overlap,
    )

    st.caption("Lần đầu tải model Whisper có thể mất vài phút. GPU giúp medium/large nhanh hơn nhiều.")

uploaded = st.file_uploader(
    "Tải video hoặc audio",
    type=["mp4", "mkv", "mov", "webm", "avi", "m4v", "mp3", "wav", "m4a", "aac"],
)

col_a, col_b = st.columns([2, 1])
with col_a:
    st.caption("Hỗ trợ mp4 / mkv / mov / webm / avi và file tiếng mp3, wav.")
with col_b:
    run = st.button("Bắt đầu dịch", type="primary", use_container_width=True, disabled=uploaded is None)

status = st.empty()
bar = st.progress(0)
result_box = st.container()


def _save_upload(file) -> Path:
    dest_dir = OUTPUT_DIR / "_uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file.name
    dest.write_bytes(file.getbuffer())
    return dest


if run and uploaded is not None:
    video_path = _save_upload(uploaded)
    status.info(f"Đã nhận file `{video_path.name}` — khởi động pipeline…")

    def progress(msg: str, pct: float) -> None:
        bar.progress(min(100, int(pct * 100)))
        status.info(msg)

    try:
        pipe = VideoTranslatePipeline(model_size=model_size, device=device)
        result = pipe.run(
            video_path=video_path,
            target_lang=target_lang,
            source_lang=source_lang,
            mode=mode,
            bilingual=bilingual,
            voice=voice,
            fit_timing=fit_timing,
            resolve_overlap=resolve_overlap,
            max_overlap_tempo=max_overlap_tempo,
            progress=progress,
        )
    except Exception as exc:
        status.error(f"Lỗi: {exc}")
        st.stop()

    bar.progress(100)
    status.success("Hoàn tất.")

    with result_box:
        m1, m2, m3 = st.columns(3)
        m1.metric("Ngôn ngữ gốc", result.detected_language)
        m2.metric("Số đoạn thoại", result.segment_count)
        m3.metric("Chế độ", result.mode)

        st.subheader("Tải kết quả")
        c1, c2, c3 = st.columns(3)
        c1.download_button(
            "SRT đã dịch",
            data=Path(result.srt_translated).read_bytes(),
            file_name=Path(result.srt_translated).name,
            mime="text/plain",
        )
        c2.download_button(
            "SRT gốc",
            data=Path(result.srt_original).read_bytes(),
            file_name=Path(result.srt_original).name,
            mime="text/plain",
        )
        c3.download_button(
            "SRT song ngữ",
            data=Path(result.srt_bilingual).read_bytes(),
            file_name=Path(result.srt_bilingual).name,
            mime="text/plain",
        )

        if result.output_video and Path(result.output_video).exists():
            st.video(result.output_video)
            st.download_button(
                "Tải video đã xử lý",
                data=Path(result.output_video).read_bytes(),
                file_name=Path(result.output_video).name,
                mime="video/mp4",
            )

        with st.expander("Xem transcript JSON"):
            st.code(Path(result.transcript_json).read_text(encoding="utf-8")[:8000], language="json")
else:
    status.caption("Chọn file và nhấn **Bắt đầu dịch**.")
    bar.progress(0)
