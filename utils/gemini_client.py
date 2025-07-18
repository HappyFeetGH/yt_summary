import subprocess
import os
import shutil
from config import Config

class GeminiClient:
    def __init__(self):
        self.config = Config()
    
    def summarize_with_keyframes(self, subtitle_text, keyframe_files, summary_length, emit_callback):
        """Gemini를 사용해 영상 요약 (서버 측 프롬프트 생성)"""
        emit_callback('status', 'AI 분석 중...')
        
        # 서버 측 고정 프롬프트 템플릿 (보안 위해 클라이언트 입력 사용 안 함)
        full_prompt = f"이 자막과 키프레임 이미지를 바탕으로 {summary_length}자 이내로 요약해 주세요."
        
        if subtitle_text:
            full_prompt += f"\n\n자막 내용:\n{subtitle_text}"
        
        if keyframe_files:
            full_prompt += f"\n\n키프레임 이미지 파일들:"
            for i, keyframe_file in enumerate(keyframe_files):
                full_prompt += f"\n이미지 {i+1}: {os.path.abspath(keyframe_file)}"
        
        # Gemini CLI 실행
        command = ['gemini', '-m', 'gemini-2.5-pro', '-p', full_prompt]
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            response = ""
            for stdout_line in iter(process.stdout.readline, ""):
                response += stdout_line
                emit_callback('partial_response', stdout_line.strip())
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code != 0:
                error_message = process.stderr.read()
                raise Exception(f'Gemini CLI 오류: {error_message}')
            
            return response.strip()
            
        finally:
            # 키프레임 파일들의 임시 디렉토리 정리
            if keyframe_files:
                temp_dir = os.path.dirname(keyframe_files[0])
                shutil.rmtree(temp_dir, ignore_errors=True)
