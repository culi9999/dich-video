# Dịch Video

Dịch lời thoại trong video trên máy bạn: tách tiếng → nhận dạng (Whisper) → dịch → xuất phụ đề SRT hoặc lồng tiếng Việt bằng [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) (fallback [Edge TTS](https://github.com/rany2/edge-tts) cho ngôn ngữ khác).

Không cần API xAI / không cần agent. Chạy localhost.

## Cần có sẵn

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) và `ffprobe` trong PATH
- Kết nối mạng lần đầu (tải model Whisper + VieNeu-TTS / Google Translate)

## Cài đặt

```bash
git clone https://github.com/culi9999/dich-video.git
cd dich-video
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy giao diện

```bash
streamlit run app.py
```

## Chạy dòng lệnh

```bash
python cli.py "./input.mp4" --to vi --mode soft --model medium
python cli.py "./input.mp4" --to vi --mode srt
python cli.py "./input.mp4" --to vi --mode hard
python cli.py "./input.mp4" --to vi --mode dub --voice "Đức Trí"
python cli.py "./input.mp4" --to vi --mode dub --voice "Đức Trí" --max-overlap-tempo 1.85
```

## Chế độ xuất

| Mode | Kết quả |
|------|--------|
| `srt` | 3 file SRT + JSON transcript |
| `soft` | Video kèm phụ đề mềm |
| `hard` | Phụ đề cháy vào khung hình |
| `dub` | Lồng tiếng VieNeu-TTS, mix ~12% audio gốc, nhúng SRT |

Mode `dub` mặc định khớp nhịp thoại gốc và **tăng tốc câu trước** nếu audio đè câu sau (trần 1.85×, không cắt cứng giữa từ). Tắt bằng `--no-resolve-overlap`.

Mỗi lần chạy tạo thư mục `output/<job_id>/` (không commit lên Git).
