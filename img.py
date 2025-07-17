import yt_dlp
import subprocess
import os
import base64
import glob

def extract_subtitles_and_keyframes(url):
    # 파일명 설정 (임시용)
    subtitle_filename = "temp_subtitles"
    video_filename = "downloaded_video.mp4"
    keyframe_pattern = "frame_%d.jpg"
    
    # 1. 자막 추출 (기존 코드)
    print("자막 추출 중...")
    ydl_opts_subtitles = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['ko'],
        'subtitlesformat': 'vtt',
        'skip_download': True,
        'outtmpl': subtitle_filename
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_subtitles) as ydl:
        ydl.download([url])
    
    # 2. 영상 다운로드 (키프레임 추출용)
    print("영상 다운로드 중...")
    ydl_opts_video = {
        'format': 'best[height<=720]',  # 720p 이하로 제한 (처리 속도 향상)
        'outtmpl': video_filename
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    
    # 3. 키프레임 추출 (네가 제공한 코드 기반)
    print("키프레임 추출 중...")
    try:
        subprocess.run([
            "ffmpeg", "-i", video_filename, 
            "-vf", "fps=1/600",  # 10분(600초)마다 1프레임
            keyframe_pattern,
            "-y"  # 기존 파일 덮어쓰기
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"키프레임 추출 오류: {e}")
        return None, None
    
    # 4. 자막 텍스트 읽기
    subtitle_text = ""
    try:
        with open(subtitle_filename+".ko.vtt", 'r', encoding='utf-8') as f:
            subtitle_text = f.read()
        print(f"자막 텍스트 길이: {len(subtitle_text)} 문자")
    except FileNotFoundError:
        print("자막 파일이 생성되지 않았습니다.")
    
    # 5. 생성된 키프레임 파일 목록 가져오기
    keyframe_files = glob.glob("frame_*.jpg")
    keyframe_files.sort()  # 순서대로 정렬
    print(f"추출된 키프레임 수: {len(keyframe_files)}")
    
    # 6. 키프레임을 base64로 변환 (최대 5개로 제한)
    base64_images = []
    for i, frame_file in enumerate(keyframe_files[:5]):  # 최대 5개만 사용
        try:
            with open(frame_file, 'rb') as img_file:
                base64_img = base64.b64encode(img_file.read()).decode('utf-8')
                base64_images.append(base64_img)
                print(f"키프레임 {i+1} 변환 완료: {frame_file}")
        except Exception as e:
            print(f"이미지 변환 오류 ({frame_file}): {e}")
    
    # 7. 임시 파일 정리
    cleanup_files = [subtitle_filename+".ko.vtt", video_filename] + keyframe_files
    for file in cleanup_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"임시 파일 삭제: {file}")
        except Exception as e:
            print(f"파일 삭제 오류 ({file}): {e}")
    
    return subtitle_text, base64_images

# 사용 예시
if __name__ == "__main__":
    url = "https://youtu.be/TTEAEe9OUxA?si=eQYzwiYn9B4fi-In"  # 네 테스트 영상
    
    subtitle_text, keyframe_images = extract_subtitles_and_keyframes(url)
    
    if subtitle_text and keyframe_images:
        # gemini-cli 호출을 위한 입력 준비
        input_content = f"자막 텍스트:\n{subtitle_text}\n\n"
        input_content += f"키프레임 이미지 수: {len(keyframe_images)}\n"
        for i, img in enumerate(keyframe_images):
            input_content += f"Base64 Image {i+1}: {img[:100]}...\n"  # 처음 100자만 출력
        
        # gemini-cli 호출 (이전 오류 해결 후 사용)
        prompt = "{subtitle_filename} 파일의 자막 텍스트와 키프레임 이미지들을 분석해서 영상을 100자 이내로 요약해."
        command = ["gemini", "-m", "gemini-2.5-pro", "-p", prompt]
        
        try:
            process = subprocess.run(
                command,
                input=input_content.encode('utf-8'),
                capture_output=True,
                check=True,
                timeout=600
            )
            summary = process.stdout.decode('utf-8').strip()
            print("="*50)
            print("영상 요약 결과:")
            print(summary)
        except subprocess.CalledProcessError as e:
            print(f"Gemini CLI 오류: {e}")
            print(f"stderr: {e.stderr.decode('utf-8') if e.stderr else '없음'}")
        except Exception as e:
            print(f"기타 오류: {e}")
