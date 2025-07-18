import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from config import Config
from utils.video_processor import VideoProcessor
from utils.gemini_client import GeminiClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# Flask 앱 초기화
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*")

# 유틸리티 클래스 초기화
video_processor = VideoProcessor()
gemini_client = GeminiClient()

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logging.info('클라이언트가 연결되었습니다.')

@socketio.on('summarize_video')
def handle_summarize_video(data):
    """유튜브 영상 요약 처리"""
    from flask_socketio import emit
    
    youtube_url = data.get('url')
    
    # 입력 검증 (기존 유지)
    allowed_languages = ['ko', 'en']
    language = data.get('language', 'ko')
    if language not in allowed_languages:
        language = 'ko'
    
    allowed_lengths = [100, 200, 500, 1000]
    summary_length = data.get('summaryLength', 200)
    if summary_length not in allowed_lengths:
        summary_length = 200
    
    if not youtube_url:
        emit('error', '유튜브 URL이 제공되지 않았습니다.')
        emit('done')  # GUI 복구
        return
    
    emit('thinking')
    logging.info(f"영상 요약 요청: {youtube_url} (언어: {language}, 길이: {summary_length})")
    
    try:
        # 영상 처리 (언어 전달)
        logging.info("영상 처리 시작...")
        subtitle_text, keyframe_files = video_processor.process_video(youtube_url, emit, language=language)
        
        if not subtitle_text and not keyframe_files:
            logging.warning("자막과 키프레임 모두 추출 실패. 요약 불가능.")
            emit('error', '자막 또는 키프레임 추출에 실패했습니다. 영상을 확인하세요.')
            emit('done')  # GUI 복구
            return
        
        logging.info(f"추출 성공: 자막 길이={len(subtitle_text)}, 키프레임 수={len(keyframe_files)}")
        
        # Gemini로 요약
        logging.info("Gemini 요약 시작...")
        summary = gemini_client.summarize_with_keyframes(
            subtitle_text, keyframe_files, summary_length, emit
        )
        
        emit('final_response', summary)
        emit('done')
        
    except Exception as e:
        logging.error(f"요약 처리 중 예외 발생: {str(e)}", exc_info=True)  # 상세 예외 로그
        emit('error', f'서버 오류가 발생했습니다: {str(e)}')
        emit('done')  # GUI 복구

if __name__ == '__main__':
    # 필요한 디렉토리 생성
    os.makedirs('temp', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("유튜브 영상 요약 서버를 시작합니다.")
    print("http://localhost:5000 에서 접속하세요.")
    socketio.run(app, debug=True, port=5000)
