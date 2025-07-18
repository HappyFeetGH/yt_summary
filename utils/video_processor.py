import os
import subprocess
import glob
import yt_dlp
import tempfile
import shutil
from config import Config
import traceback
import logging

class VideoProcessor:
    def __init__(self):
        self.config = Config()
    
    def process_video(self, url, emit_callback, language='ko'):
        """유튜브 영상에서 자막과 키프레임 추출 (언어 동적 설정)"""
        temp_dir = tempfile.mkdtemp(dir=self.config.TEMP_DIR)
        logging.info(f"임시 디렉토리 생성: {temp_dir}")
        
        subtitle_text = None
        keyframe_files = None
        
        try:
            # 자막 추출
            emit_callback('status', '자막 추출 중...')
            logging.info(f"자막 추출 시작 (언어: {language})")
            subtitle_text = self._extract_subtitles(url, temp_dir, language)
            logging.info(f"자막 추출 완료: 길이={len(subtitle_text) if subtitle_text else 0}")
            
            # 키프레임 추출
            emit_callback('status', '키프레임 추출 중...')
            logging.info("키프레임 추출 시작")
            keyframe_files = self._extract_keyframes(url, temp_dir)
            logging.info(f"키프레임 추출 완료: 수={len(keyframe_files)}")
            
            return subtitle_text, keyframe_files
        
        except Exception as e:
            error_msg = f"영상 처리 오류: {str(e)}\n{traceback.format_exc()}"  # 상세 스택 트레이스
            logging.error(error_msg)
            emit_callback('error', error_msg)
            return None, None
        finally:
            # 임시 디렉토리 정리 (실패 시에도 실행)
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"임시 디렉토리 삭제: {temp_dir}")
            except Exception as cleanup_e:
                logging.error(f"임시 파일 삭제 오류: {cleanup_e}")

    def _extract_subtitles(self, url, temp_dir, language='ko'):
        """자막 추출 로직"""
        subtitle_template = os.path.join(temp_dir, "subtitles.%(ext)s")
        
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [language],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': subtitle_template,
            'verbose': True,
            'no_warnings': False
        }
        
        try:
            logging.debug(f"yt_dlp 옵션: {ydl_opts}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            subtitle_files = glob.glob(os.path.join(temp_dir, "subtitles*.vtt"))
            if not subtitle_files:
                logging.warning("자막 파일 없음. 영상에 자막이 없을 수 있음.")
                return ""
            
            subtitle_filename = subtitle_files[0]
            with open(subtitle_filename, 'r', encoding='utf-8') as f:
                return f.read()[:self.config.SUBTITLE_MAX_LENGTH]
        
        except Exception as e:
            logging.error(f"자막 추출 중 예외: {str(e)}", exc_info=True)
            return ""

    def _extract_keyframes(self, url, temp_dir):
        """키프레임 추출 로직"""
        video_filename = os.path.join(temp_dir, "video.mp4")
        keyframe_pattern = os.path.join(temp_dir, "frame_%d.jpg")
        
        try:
            # 영상 다운로드
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': video_filename,
                'verbose': True
            }
            logging.debug(f"영상 다운로드 옵션: {ydl_opts}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not os.path.exists(video_filename):
                raise FileNotFoundError("영상 파일 다운로드 실패")
            
            # 키프레임 추출
            logging.info(f"FFmpeg 명령어 실행: ffmpeg -i {video_filename} -vf fps=1/{self.config.KEYFRAME_INTERVAL} {keyframe_pattern}")
            result = subprocess.run([
                "ffmpeg", "-i", video_filename,
                "-vf", f"fps=1/{self.config.KEYFRAME_INTERVAL}",
                keyframe_pattern,
                "-y"
            ], check=True, capture_output=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg 오류: {result.stderr.decode('utf-8')}")
            
            keyframe_files = glob.glob(os.path.join(temp_dir, "frame_*.jpg"))
            return sorted(keyframe_files)[:self.config.MAX_KEYFRAMES]
        
        except Exception as e:
            logging.error(f"키프레임 추출 중 예외: {str(e)}", exc_info=True)
            return []
