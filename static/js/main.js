// main.js – Frontend logic cho TTS App

// ============================================================
// DOM REFERENCES
// ============================================================
const textInput       = document.getElementById('text-input');
const charCount       = document.getElementById('char-count');
const speakerSelect   = document.getElementById('speaker-select');
const btnConvert      = document.getElementById('btn-convert');
const statusBar       = document.getElementById('status-bar');

const resultPlaceholder = document.getElementById('result-placeholder');
const audioResult       = document.getElementById('audio-result');
const waveformBars      = document.getElementById('waveform-bars');

const audioNative     = document.getElementById('audio-native');
const btnPlay         = document.getElementById('btn-play');
const progressBg      = document.getElementById('progress-bg');
const progressFill    = document.getElementById('progress-fill');
const timeCurrent     = document.getElementById('time-current');
const timeTotal       = document.getElementById('time-total');
const btnDownload     = document.getElementById('btn-download');
const vniChips        = document.getElementById('vni-chips');

// ============================================================
// CHAR COUNTER
// ============================================================
textInput.addEventListener('input', () => {
  const len = textInput.value.length;
  charCount.textContent = `${len} ký tự`;
  charCount.classList.remove('warning');
});

// ============================================================
// STATUS BAR HELPER
// ============================================================
function setStatus(type, message) {
  statusBar.textContent = message;
  statusBar.className = `status-bar visible ${type}`;
}

function clearStatus() {
  statusBar.className = 'status-bar';
}

// ============================================================
// CONVERT BUTTON – Gọi API /api/tts
// ============================================================
btnConvert.addEventListener('click', async () => {
  const text = textInput.value.trim();
  if (!text) {
    setStatus('error', '⚠ Vui lòng nhập văn bản trước khi chuyển đổi.');
    return;
  }

  const speakerId = parseInt(speakerSelect.value, 10) || 1;

  // UI: loading state
  btnConvert.classList.add('loading');
  btnConvert.disabled = true;
  setStatus('loading', '⏳ Đang xử lý âm thanh...');

  try {
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, speaker_id: speakerId }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Lỗi server: ${response.status}`);
    }

    const data = await response.json();
    // data = { audio_url: "...", vni_codes: [...], not_found: [...] }

    const notFound = data.not_found || [];
    const fallbackUsed = data.fallback_used || [];
    showAudioResult(data.audio_url, data.vni_codes || [], notFound);

    if (notFound.length > 0) {
      setStatus(
        'error',
        `⚠ Đã bỏ qua ${notFound.length} từ chưa có audio. Xem bảng Missing_Audio để bổ sung.`
      );
    } else if (fallbackUsed.length > 0) {
      setStatus(
        'success',
        `✅ Chuyển đổi thành công (dùng audio dự phòng cho ${fallbackUsed.length} từ).`
      );
    } else {
      setStatus('success', '✅ Chuyển đổi thành công!');
    }

  } catch (err) {
    console.error('[TTS]', err);
    setStatus('error', `❌ ${err.message}`);
  } finally {
    btnConvert.classList.remove('loading');
    btnConvert.disabled = false;
  }
});

// ============================================================
// SHOW AUDIO RESULT
// ============================================================
function showAudioResult(audioUrl, vniCodes, notFound = []) {
  // Hiển thị panel kết quả
  resultPlaceholder.style.display = 'none';
  audioResult.classList.add('visible');

  // Load audio (thêm timestamp để tránh cache)
  audioNative.src = audioUrl + '?t=' + Date.now();
  audioNative.load();

  // Download link
  btnDownload.href = audioUrl;

  // VNI chips
  vniChips.innerHTML = '';
  vniCodes.forEach(code => {
    const chip = document.createElement('span');
    chip.className = 'vni-chip';
    chip.textContent = code;
    
    // Đổi màu nếu không tìm thấy từ trong CSDL
    if (notFound.includes(code)) {
      chip.style.backgroundColor = '#ffebee';
      chip.style.color = '#d32f2f';
      chip.style.borderColor = '#ef9a9a';
    }
    
    vniChips.appendChild(chip);
  });
}

// ============================================================
// CUSTOM AUDIO PLAYER
// ============================================================
btnPlay.addEventListener('click', () => {
  if (audioNative.paused) {
    audioNative.play();
  } else {
    audioNative.pause();
  }
});

audioNative.addEventListener('play', () => {
  btnPlay.textContent = '⏸';
  waveformBars.classList.add('playing');
});

audioNative.addEventListener('pause', () => {
  btnPlay.textContent = '▶';
  waveformBars.classList.remove('playing');
});

audioNative.addEventListener('ended', () => {
  btnPlay.textContent = '▶';
  waveformBars.classList.remove('playing');
  progressFill.style.width = '0%';
});

audioNative.addEventListener('loadedmetadata', () => {
  timeTotal.textContent = formatTime(audioNative.duration);
  progressFill.style.width = '0%';
});

audioNative.addEventListener('timeupdate', () => {
  const pct = audioNative.duration
    ? (audioNative.currentTime / audioNative.duration) * 100
    : 0;
  progressFill.style.width = pct + '%';
  timeCurrent.textContent = formatTime(audioNative.currentTime);
});

// Click trên progress bar để seek
progressBg.addEventListener('click', (e) => {
  if (!audioNative.duration) return;
  const rect = progressBg.getBoundingClientRect();
  const ratio = (e.clientX - rect.left) / rect.width;
  audioNative.currentTime = ratio * audioNative.duration;
});

// ============================================================
// HELPER: format giây -> m:ss
// ============================================================
function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
