import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Languages,
  Copy,
  Check,
  Volume2,
  Trash2,
  X,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Loader2,
  Sparkles,
} from 'lucide-react';

export default function VietnameseComposer({
  isOpen,
  onClose,
  onSpeakText,
}) {
  const [vietnameseText, setVietnameseText] = useState('');
  const [englishTranslation, setEnglishTranslation] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const textareaRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Cleanup pending requests on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized && textareaRef.current) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [isOpen, isMinimized]);

  // Translate function with AbortController to avoid out-of-order race conditions
  const handleTranslate = useCallback(async (textToTranslate) => {
    const query = (textToTranslate ?? vietnameseText).trim();
    if (!query) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      setEnglishTranslation('');
      setIsTranslating(false);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsTranslating(true);
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: query,
          source_lang: 'vi',
          target_lang: 'en',
        }),
        signal: controller.signal,
      });

      if (response.ok) {
        const data = await response.json();
        setEnglishTranslation(data.translated || '');
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Translation error:', err);
      }
    } finally {
      if (abortControllerRef.current === controller) {
        setIsTranslating(false);
      }
    }
  }, [vietnameseText]);

  // Auto-translate debounce on typing
  const handleTextChange = (e) => {
    const text = e.target.value;
    setVietnameseText(text);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!text.trim()) {
      setEnglishTranslation('');
      setIsTranslating(false);
      return;
    }

    debounceTimerRef.current = setTimeout(() => {
      handleTranslate(text);
    }, 450);
  };

  // Keyboard shortcut: Enter or Ctrl+Enter / Cmd+Enter
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleTranslate();
    }
  };

  const handleCopy = () => {
    if (!englishTranslation || !navigator.clipboard?.writeText) return;
    navigator.clipboard.writeText(englishTranslation)
      .then(() => {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 1800);
      })
      .catch((err) => console.error('Copy failed:', err));
  };

  const handleSpeak = () => {
    if (!englishTranslation) return;
    setIsPlayingAudio(true);
    if (onSpeakText) {
      onSpeakText(englishTranslation, 'en');
    }
    setTimeout(() => setIsPlayingAudio(false), 2000);
  };

  const handleClear = () => {
    setVietnameseText('');
    setEnglishTranslation('');
    textareaRef.current?.focus();
  };

  if (!isOpen) return null;

  return (
    <div
      className={`fixed z-30 transition-all duration-200 ease-out left-1/2 -translate-x-1/2 w-[96vw] max-w-3xl ${
        isMinimized
          ? 'bottom-4 bg-white/95 backdrop-blur-md rounded-full shadow-lg border border-[#dadce0] px-4 py-2 flex items-center justify-between'
          : 'bottom-4 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-[#dadce0] overflow-hidden'
      }`}
    >
      {/* Minimized view */}
      {isMinimized ? (
        <div className="flex items-center justify-between w-full select-none">
          <div className="flex items-center space-x-2">
            <span className="p-1 rounded-full bg-[#e8f0fe] text-[#1a73e8]">
              <Languages size={15} />
            </span>
            <span className="text-xs font-semibold text-[#1f1f1f]">
              Soạn Tiếng Việt → Dịch Tiếng Anh
            </span>
            {englishTranslation && (
              <span className="text-xs text-[#5f6368] truncate max-w-[200px] sm:max-w-[300px]">
                : &ldquo;{englishTranslation}&rdquo;
              </span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <button
              type="button"
              onClick={() => setIsMinimized(false)}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
              title="Mở rộng khung soạn thảo"
            >
              <ChevronUp size={16} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
              title="Đóng"
            >
              <X size={15} />
            </button>
          </div>
        </div>
      ) : (
        /* Expanded full composer */
        <div className="flex flex-col">
          {/* Header */}
          <div className="h-10 px-4 flex items-center justify-between border-b border-[#e8eaed] bg-[#f8f9fa] select-none">
            <div className="flex items-center space-x-2">
              <div className="p-1 rounded bg-[#e8f0fe] text-[#1a73e8]">
                <Languages size={14} />
              </div>
              <span className="text-xs font-semibold text-[#1f1f1f]">
                Soạn Tiếng Việt → Dịch Tiếng Anh
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                VI &rarr; EN
              </span>
              <span className="hidden sm:inline text-[11px] text-[#80868b]">
                (Nhấn <kbd className="px-1 py-0.5 bg-white border border-[#dadce0] rounded text-[10px] font-mono">Ctrl+Enter</kbd> để dịch)
              </span>
            </div>

            <div className="flex items-center space-x-1">
              <button
                type="button"
                onClick={() => setIsMinimized(true)}
                className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4] transition-colors"
                title="Thu gọn"
              >
                <ChevronDown size={16} />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4] transition-colors"
                title="Đóng khung soạn thảo"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Dual Panel Body: VI Input on Left/Top, EN Output on Right/Bottom */}
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#e8eaed] p-3 gap-3">
            {/* Left: Vietnamese Input Box */}
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between select-none">
                <span className="text-[11px] font-semibold text-[#444746] uppercase tracking-wide">
                  Tiếng Việt (Nội dung bạn muốn nói)
                </span>
                <span className="text-[10px] text-[#80868b] font-mono">
                  {vietnameseText.length}/2000
                </span>
              </div>

              <textarea
                ref={textareaRef}
                value={vietnameseText}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                maxLength={2000}
                placeholder="Nhập nội dung tiếng Việt bạn muốn phát biểu hoặc nhắn tin vào Teams..."
                className="w-full h-24 sm:h-28 text-sm p-2.5 rounded-lg border border-[#dadce0] focus:border-[#1a73e8] focus:ring-1 focus:ring-[#1a73e8] outline-none resize-none bg-white text-[#1f1f1f] placeholder-[#80868b] transition-all"
              />

              {/* Action Bar for Input */}
              <div className="flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={!vietnameseText}
                  className="flex items-center space-x-1 text-xs text-[#5f6368] hover:text-red-600 disabled:opacity-30 disabled:hover:text-[#5f6368] transition-colors py-1 px-2 rounded hover:bg-black/5"
                  title="Xóa nội dung"
                >
                  <Trash2 size={13} />
                  <span>Xóa</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleTranslate()}
                  disabled={!vietnameseText.trim() || isTranslating}
                  className="flex items-center space-x-1.5 bg-[#1a73e8] hover:bg-[#1557b0] disabled:bg-[#dadce0] text-white text-xs font-medium px-3 py-1.5 rounded-lg shadow-xs transition-colors"
                  title="Dịch sang tiếng Anh ngay"
                >
                  {isTranslating ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      <span>Đang dịch...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={13} />
                      <span>Dịch sang tiếng Anh</span>
                      <ArrowRight size={12} />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Right: English Translation Result */}
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between select-none">
                <span className="text-[11px] font-semibold text-[#1967d2] uppercase tracking-wide flex items-center space-x-1">
                  <span>English Translation (Bản dịch tiếng Anh)</span>
                </span>
                {isTranslating && (
                  <span className="text-[10px] text-[#1a73e8] flex items-center space-x-1 font-medium">
                    <Loader2 size={11} className="animate-spin" />
                    <span>Live translating</span>
                  </span>
                )}
              </div>

              <div className="w-full h-24 sm:h-28 text-sm p-2.5 rounded-lg border border-[#e8eaed] bg-[#f8f9fa] overflow-y-auto select-text">
                {englishTranslation ? (
                  <p className="text-[#1f1f1f] font-medium leading-relaxed select-text">
                    {englishTranslation}
                  </p>
                ) : (
                  <p className="text-[#80868b] italic text-xs select-none">
                    {isTranslating
                      ? 'Đang dịch...'
                      : 'Bản dịch tiếng Anh sẽ xuất hiện ở đây khi bạn gõ tiếng Việt...'}
                  </p>
                )}
              </div>

              {/* Action Bar for Translation Output */}
              <div className="flex items-center justify-end space-x-2 pt-1">
                <button
                  type="button"
                  onClick={handleSpeak}
                  disabled={!englishTranslation}
                  className="flex items-center space-x-1.5 text-xs text-[#3c4043] hover:text-[#1a73e8] disabled:opacity-30 disabled:hover:text-[#3c4043] border border-[#dadce0] hover:border-[#1a73e8] px-2.5 py-1.5 rounded-lg bg-white transition-colors"
                  title="Nghe phát âm tiếng Anh chuẩn"
                >
                  <Volume2 size={14} className={isPlayingAudio ? 'text-[#1a73e8] animate-pulse' : ''} />
                  <span>Phát âm (Speak)</span>
                </button>

                <button
                  type="button"
                  onClick={handleCopy}
                  disabled={!englishTranslation}
                  className={`flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all shadow-xs ${
                    isCopied
                      ? 'bg-emerald-600 text-white'
                      : 'bg-[#1f1f1f] hover:bg-[#3c4043] text-white disabled:bg-[#dadce0] disabled:text-gray-500'
                  }`}
                  title="Sao chép bản dịch tiếng Anh để dán vào Teams chat"
                >
                  {isCopied ? (
                    <>
                      <Check size={13} />
                      <span>Đã sao chép!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={13} />
                      <span>Sao chép tiếng Anh</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
