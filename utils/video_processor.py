import os
import subprocess
import glob
import yt_dlp
import tempfile
import shutil
from config import Config

class VideoProcessor:
    def __init__(self):
        self.config = Config()
    
    def process_video(self, url, emit_callback):
        """유튜브 영상에서 자막과 키프레임 추출"""
        temp_dir = tempfile.mkdtemp(dir=self.config.TEMP_DIR)
        
        try:
            # 자막 추출
            emit_callback('status', '자막 추출 중...')
            subtitle_text = self._extract_subtitles(url, temp_dir)
            
            # 키프레임 추출
            emit_callback('status', '키프레임 추출 중...')
            keyframe_files = self._extract_keyframes(url, temp_dir)
            
            return subtitle_text, keyframe_files
            
        except Exception as e:
            emit_callback('error', f'영상 처리 오류: {str(e)}')
            return None, None
        finally:
            # 임시 파일 정리는 Gemini 처리 후에 수행
            pass
    
    def _extract_subtitles(self, url, temp_dir):
        """자막 추출 로직"""
        subtitle_filename = os.path.join(temp_dir, "subtitles.ko.vtt")
        
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': subtitle_filename
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(subtitle_filename):
            with open(subtitle_filename, 'r', encoding='utf-8') as f:
                return f.read()[:self.config.SUBTITLE_MAX_LENGTH]
        return ""
    
    def _extract_keyframes(self, url, temp_dir):
        """키프레임 추출 로직"""
        video_filename = os.path.join(temp_dir, "video.mp4")
        keyframe_pattern = os.path.join(temp_dir, "frame_%d.jpg")
        
        # 영상 다운로드
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': video_filename
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 키프레임 추출
        subprocess.run([
            "ffmpeg", "-i", video_filename,
            "-vf", f"fps=1/{self.config.KEYFRAME_INTERVAL}",
            keyframe_pattern,
            "-y"
        ], check=True, capture_output=True)
        
        keyframe_files = glob.glob(os.path.join(temp_dir, "frame_*.jpg"))
        return sorted(keyframe_files)[:self.config.MAX_KEYFRAMES]
