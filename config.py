import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    TEMP_DIR = 'temp'
    LOG_DIR = 'logs'
    
    # 영상 처리 설정
    MAX_VIDEO_LENGTH = 7200  # 2시간 (초)
    KEYFRAME_INTERVAL = 600  # 10분 간격
    MAX_KEYFRAMES = 10
    SUBTITLE_MAX_LENGTH = 10000  # 자막 최대 길이
