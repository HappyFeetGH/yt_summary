import yt_dlp

url = "https://youtu.be/brkqur0KdgI?si=2cb4X9QQ2iqNh9l8"
subtitle_filename = "temp_subtitles"  # 지정할 파일 이름 (임시용)

ydl_opts = {
    'writesubtitles': True,          # 업로드된 자막 다운로드 (필요 시)
    'writeautomaticsub': True,       # 자동 생성 자막 다운로드 (한국어 영상에 필수)
    'subtitleslangs': ['ko'],        # 한국어 자막 우선 (ko: Korean)
    'subtitlesformat': 'vtt',        # VTT 형식으로 저장
    'skip_download': True,           # 영상 다운로드 없이 자막만 추출
    'outtmpl': subtitle_filename     # 파일 이름 지정 (디렉토리 포함 가능, 예: '/tmp/%(title)s.%(ext)s')
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

# 추출된 자막 파일 읽기 예시 (VTT 파일 생성 후)
with open(subtitle_filename+".ko.vtt", 'r', encoding='utf-8') as f:  # 파일명은 영상 ID + .ko.vtt 형태로 생성됨
    subtitle_text = f.read()
print("추출된 자막 텍스트:", subtitle_text[:200])  # 테스트 출력 (첫 200자)"""

import subprocess
"""
video_file = "downloaded_video.mp4"  # yt-dlp로 다운로드한 파일
output_pattern = "frame_%d.jpg"  # 출력 파일 패턴
subprocess.run(["ffmpeg", "-i", video_file, "-vf", "fps=1/600", output_pattern])  # 10분(600초)마다 1프레임 추출
"""

# 자막 텍스트 로드 (yt-dlp 후 파일 읽기)
with open(subtitle_filename+".ko.vtt", 'r') as f:
    subtitle_text = f.read()

prompt = f"{subtitle_filename} 파일의 자막 텍스트를 1000자 이내로 요약해."
command = ["gemini", "-m", "gemini-2.5-pro", "-p", prompt]
process = subprocess.run(command, input=subtitle_text.encode('utf-8'), capture_output=True, check=True)
summary = process.stdout.decode('utf-8').strip()
print("요약 결과:", summary)
