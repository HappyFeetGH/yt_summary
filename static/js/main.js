const socket = io();
const urlInput = document.getElementById('youtube-url');
const promptInput = document.getElementById('custom-prompt');
const summarizeBtn = document.getElementById('summarize-btn');
const statusDiv = document.getElementById('status');
const loadingDiv = document.getElementById('loading');
const resultDiv = document.getElementById('result');

// 요약 버튼 클릭 이벤트
summarizeBtn.addEventListener('click', () => {
    const url = urlInput.value.trim();
    const prompt = promptInput.value.trim();
    
    if (!url) {
        alert('유튜브 URL을 입력하세요.');
        return;
    }
    
    // UI 상태 변경
    summarizeBtn.disabled = true;
    resultDiv.textContent = '';
    statusDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    
    // 서버에 요약 요청
    socket.emit('summarize_video', { url, prompt });
});

// 서버 이벤트 리스너
socket.on('thinking', () => {
    loadingDiv.textContent = 'AI가 분석 중입니다...';
    loadingDiv.classList.remove('hidden');
});

socket.on('status', (message) => {
    statusDiv.textContent = message;
    statusDiv.classList.remove('hidden', 'error');
    loadingDiv.classList.add('hidden');
});

socket.on('partial_response', (text) => {
    resultDiv.textContent += text + '\n';
});

socket.on('final_response', (summary) => {
    resultDiv.textContent = summary;
});

socket.on('error', (error) => {
    statusDiv.textContent = `오류: ${error}`;
    statusDiv.classList.add('error');
    statusDiv.classList.remove('hidden');
    loadingDiv.classList.add('hidden');
});

socket.on('done', () => {
    summarizeBtn.disabled = false;
    loadingDiv.classList.add('hidden');
    statusDiv.classList.add('hidden');
});
