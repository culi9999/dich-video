"""Cấu hình ngôn ngữ, model và giọng đọc."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "output" / "tmp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

LANGUAGES = {
    "auto": "Tự phát hiện",
    "vi": "Tiếng Việt",
    "en": "English",
    "zh-CN": "中文 (Giản thể)",
    "zh-TW": "中文 (Phồn thể)",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
    "th": "ไทย",
    "id": "Bahasa Indonesia",
    "hi": "हिन्दी",
    "ar": "العربية",
    "it": "Italiano",
}

WHISPER_LANG_MAP = {
    "zh-CN": "zh",
    "zh-TW": "zh",
    "auto": None,
}

WHISPER_MODELS = {
    "tiny": "Nhanh nhất — chất lượng thấp (dùng thử)",
    "base": "Nhanh — đủ dùng video rõ tiếng",
    "small": "Cân bằng (khuyến nghị máy yếu)",
    "medium": "Tốt — khuyến nghị mặc định",
    "large-v3": "Chính xác nhất — cần GPU/RAM lớn",
}

# VieNeu-TTS — https://github.com/pnnbao97/VieNeu-TTS
VIENEU_MODE = "v3nano"
VIENEU_DEFAULT_VOICE = "Đức Trí"
VIENEU_VOICES = [
    "Đức Trí",
    "Anh Khôi",
    "Minh Quân",
    "Hữu Quân",
    "Mạnh Dũng",
    "Adam",
    "Mai Anh",
    "Trúc Ly",
    "Ái Hân",
    "Mỹ Duyên",
    "Xuân Tiên",
]

EDGE_VOICE_MAP = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "es": "es-ES-ElviraNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural",
    "id": "id-ID-GadisNeural",
    "hi": "hi-IN-SwaraNeural",
    "ar": "ar-SA-ZariyahNeural",
    "it": "it-IT-ElsaNeural",
}

EDGE_VOICE_ALTERNATES = {
    "vi": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
    "en": ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"],
    "zh-CN": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"],
    "ja": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
    "ko": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"],
}

SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v", ".mpeg", ".mpg"}
SUPPORTED_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
