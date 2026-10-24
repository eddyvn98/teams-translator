/**
 * High-quality Natural Speech Synthesis Service
 * Provides studio-quality pronunciation (Google Natural Voice)
 * with smart fallback to filtered, natural browser voices.
 */

let activeAudio = null;

/**
 * Filter and select the best, most human-sounding voice available in the browser.
 * Strictly excludes robotic novelty voices (Fred, Albert, Zarvox, etc.).
 */
export function getBestVoice(lang = 'en') {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const isEn = lang.toLowerCase().startsWith('en');
  const targetPrefix = isEn ? 'en' : 'vi';

  // 1. Filter matching language
  const langVoices = voices.filter(
    (v) => v.lang && v.lang.toLowerCase().replace('_', '-').startsWith(targetPrefix)
  );
  if (langVoices.length === 0) return voices[0];

  // List of robotic novelty voices to NEVER select
  const badVoiceNames = [
    'fred',
    'albert',
    'zarvox',
    'trinoids',
    'whisper',
    'deranged',
    'bad news',
    'bells',
    'boing',
    'cellos',
    'pipe organ',
    'hysterical',
    'junior',
    'kathy',
    'princess',
    'ralph',
    'vicki',
    'victoria',
    'bahh',
    'bubbles',
    'good news',
    'organ',
    'sin-ji',
    'tink',
  ];

  const cleanVoices = langVoices.filter(
    (v) => !badVoiceNames.some((bad) => v.name.toLowerCase().includes(bad))
  );
  const candidates = cleanVoices.length > 0 ? cleanVoices : langVoices;

  // Priority order for natural, pleasant, human-sounding voices
  const preferredKeywords = [
    'natural',
    'online',
    'neural',
    'google us english',
    'google uk english female',
    'google',
    'samantha',
    'ava',
    'allison',
    'serena',
    'jenny',
    'aria',
    'guy',
    'karen',
    'daniel',
    'siri',
    'alex',
  ];

  for (const keyword of preferredKeywords) {
    const match = candidates.find((v) => v.name.toLowerCase().includes(keyword));
    if (match) return match;
  }

  // Fallback to default or first clean voice
  const defaultVoice = candidates.find((v) => v.default);
  return defaultVoice || candidates[0];
}

// Pre-load voices on browser ready
if (typeof window !== 'undefined' && window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    try {
      window.speechSynthesis.getVoices();
    } catch {
      // ignore
    }
  };
}

/**
 * Play text aloud with natural, studio-quality pronunciation.
 */
export function playNaturalSpeech(text, lang = 'en') {
  if (!text || !text.trim()) return;
  const cleanText = text.trim();
  const cleanLang = lang.toLowerCase().startsWith('en')
    ? 'en'
    : lang.toLowerCase().startsWith('vi')
    ? 'vi'
    : lang;

  // Stop any active audio or speech
  try {
    if (activeAudio) {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeAudio = null;
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  } catch {
    // ignore
  }

  // Fallback function: SpeechSynthesis with filtered natural voice
  const speakWithSynthesis = () => {
    try {
      if (typeof window === 'undefined' || !window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 0.95; // Warm, natural cadence
      utterance.pitch = 1.0;
      utterance.lang = cleanLang === 'en' ? 'en-US' : cleanLang === 'vi' ? 'vi-VN' : cleanLang;

      const voice = getBestVoice(cleanLang);
      if (voice) {
        utterance.voice = voice;
      }
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn('SpeechSynthesis error:', err);
    }
  };

  // Primary: High-Quality TTS via Backend Proxy (with chunking, Referer emulation, and LRU cache)
  try {
    const proxyUrl = `/api/tts?text=${encodeURIComponent(cleanText)}&lang=${cleanLang}`;
    const audio = new Audio(proxyUrl);
    activeAudio = audio;

    let hasPlayed = false;

    audio.oncanplaythrough = () => {
      if (!hasPlayed) {
        hasPlayed = true;
        audio.play().catch(() => {
          speakWithSynthesis();
        });
      }
    };

    audio.onerror = () => {
      if (!hasPlayed) {
        hasPlayed = true;
        speakWithSynthesis();
      }
    };

    // Safety timeout: if audio takes > 1.2s to load, fall back to speech synthesis
    setTimeout(() => {
      if (!hasPlayed && audio.readyState < 2) {
        hasPlayed = true;
        try {
          audio.pause();
        } catch {
          // ignore
        }
        speakWithSynthesis();
      }
    }, 1200);

    audio.load();
  } catch {
    speakWithSynthesis();
  }
}
