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
