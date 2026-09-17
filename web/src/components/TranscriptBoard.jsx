import React, { useEffect, useRef, useState } from 'react';
import { Languages, Volume2, Copy, Check, AlignJustify, List } from 'lucide-react';

export default function TranscriptBoard({
  sentences = [],
  sourceLang = 'EN',
  targetLang = 'VI',
  onSpeakText,
}) {
  const scrollRef = useRef(null);
  const [copiedId, setCopiedId] = useState(null);
  const [viewMode, setViewMode] = useState('flow'); // 'flow' (Google AI Studio style) or 'list'

  // Auto-scroll to bottom as new speech arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [sentences]);

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const hasContent = sentences.length > 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Column Headers with View Mode Switch (Matching Image 2) */}
      <div className="grid grid-cols-2 border-b border-[#f1f3f4] bg-white px-8 py-2.5 shrink-0 items-center">
        {/* Left Column Header */}
        <div className="flex items-center space-x-2">
          <span className="text-[13px] font-medium text-[#444746]">Input transcript</span>
        </div>

        {/* Right Column Header with Layout Switch */}
        <div className="flex items-center justify-between pl-4">
          <div className="flex items-center space-x-2">
            <span className="text-[13px] font-medium text-[#444746]">Output transcript</span>
          </div>

          {/* View mode toggle */}
          <div className="flex items-center space-x-1 bg-[#f1f3f4] p-0.5 rounded-lg text-xs">
            <button
              onClick={() => setViewMode('flow')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                viewMode === 'flow'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Chế độ văn bản liền mạch (Google AI Studio)"
            >
              <AlignJustify size={12} />
              <span>Liền mạch</span>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Chế độ danh sách câu"
            >
              <List size={12} />
              <span>Từng câu</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 pt-6 pb-36 scroll-smooth"
      >
        {!hasContent ? (
          <div className="h-full flex flex-col items-center justify-center text-[#80868b] space-y-3 select-none pb-20">
            <div className="w-12 h-12 rounded-full bg-[#f8f9fa] border border-[#e8eaed] flex items-center justify-center text-[#5f6368]">
              <Languages size={24} />
            </div>
            <p className="text-sm font-normal">
              Bấm nút <strong className="text-[#1f1f1f] font-medium">Chia sẻ thẻ</strong> ở thanh bên dưới để bắt đầu dịch thời gian thực
            </p>
            <p className="text-xs text-[#9aa0a6]">
              Hệ thống sẽ tự động ghép câu hoàn chỉnh và dịch mượt mà như Google AI Studio
            </p>
          </div>
        ) : viewMode === 'flow' ? (
          /* ======================================================== */
          /* FLOWING PARAGRAPH MODE (Exact match to Google AI Studio)  */
          /* ======================================================== */
          <div className="grid grid-cols-2 gap-10 items-start">
            {/* Left Flowing Column */}
            <div className="text-[15px] leading-relaxed text-[#1f1f1f] pr-2">
              <span className="inline-block mr-2 px-1.5 py-0.5 rounded text-[11px] font-bold bg-[#e8f0fe] text-[#1967d2] uppercase tracking-wide align-baseline">
                {sourceLang.slice(0, 2).toUpperCase()}
              </span>
              {sentences.map((item, idx) => (
                <span
                  key={item.id || idx}
                  className={`transition-colors duration-150 rounded px-0.5 ${
                    !item.is_final ? 'text-[#1f1f1f] font-normal bg-amber-50/70' : 'hover:bg-[#f1f3f4]'
                  }`}
                  title={item.source}
                >
                  {item.source}{' '}
                </span>
              ))}
            </div>

            {/* Right Flowing Column */}
            <div className="text-[15px] leading-relaxed text-[#1f1f1f] pl-2">
              <span className="inline-block mr-2 px-1.5 py-0.5 rounded text-[11px] font-bold bg-[#e8f0fe] text-[#1967d2] uppercase tracking-wide align-baseline">
                {targetLang.slice(0, 2).toUpperCase()}
              </span>
              {sentences.map((item, idx) => (
                <span
                  key={item.id || idx}
                  className={`transition-colors duration-150 rounded px-0.5 group relative ${
                    !item.is_final ? 'text-[#1f1f1f] font-normal bg-amber-50/70' : 'hover:bg-[#f1f3f4]'
                  }`}
                  title={item.translated}
                >
                  {item.translated || '...'}{' '}
                </span>
              ))}
            </div>
          </div>
        ) : (
          /* ======================================================== */
          /* SENTENCE LIST MODE (Clean full sentences with actions)   */
          /* ======================================================== */
          <div className="space-y-4">
            {sentences.map((item, idx) => (
              <div
                key={item.id || idx}
                className="grid grid-cols-2 gap-8 items-start group hover:bg-[#fafafa] -mx-4 px-4 py-2.5 rounded-xl transition-colors border-b border-[#f8f9fa] last:border-b-0"
              >
                {/* Left: Full Input Sentence */}
                <div className="text-[15px] leading-relaxed text-[#1f1f1f] pr-4">
                  <div className="flex items-baseline space-x-2">
                    <span className="text-[11px] font-semibold text-[#1967d2] uppercase tracking-wider select-none shrink-0">
                      {sourceLang.slice(0, 2).toUpperCase()}
                    </span>
                    <span className={!item.is_final ? 'text-[#444746] italic' : ''}>
                      {item.source}
                    </span>
                  </div>
                </div>

                {/* Right: Full Output Sentence */}
                <div className="text-[15px] leading-relaxed text-[#1f1f1f] pl-4 relative">
                  <div className="flex items-baseline space-x-2">
                    <span className="text-[11px] font-semibold text-[#1967d2] uppercase tracking-wider select-none shrink-0">
                      {targetLang.slice(0, 2).toUpperCase()}
                    </span>
                    <span className={!item.is_final ? 'text-[#444746] italic' : 'font-normal'}>
                      {item.translated || 'Đang dịch...'}
                    </span>
                  </div>

                  {/* Quick Action Icons */}
                  <div className="absolute right-0 top-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1 bg-white/95 px-1 py-0.5 rounded-lg border border-[#e8eaed] shadow-xs">
                    {onSpeakText && (
                      <button
                        onClick={() => onSpeakText(item.translated)}
                        className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4]"
                        title="Nghe phát âm"
                      >
                        <Volume2 size={13} />
                      </button>
                    )}
                    <button
                      onClick={() => handleCopy(item.translated, item.id || idx)}
                      className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4]"
                      title="Sao chép"
                    >
                      {copiedId === (item.id || idx) ? (
                        <Check size={13} className="text-green-600" />
                      ) : (
                        <Copy size={13} />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Spacing buffer so floating control bar never covers bottom captions */}
        {hasContent && <div className="h-28 shrink-0 pointer-events-none" aria-hidden="true" />}
      </div>
    </div>
  );
}
