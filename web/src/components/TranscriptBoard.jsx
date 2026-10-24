import React, { useEffect, useRef, useState } from 'react';
import {
  Languages,
  Volume2,
  Copy,
  Check,
  AlignJustify,
  List,
  Rows2,
  Columns2,
} from 'lucide-react';

export default function TranscriptBoard({
  sentences = [],
  sourceLang = 'EN',
  targetLang = 'VI',
  onSpeakText,
}) {
  const topScrollRef = useRef(null);
  const bottomScrollRef = useRef(null);

  const [copiedId, setCopiedId] = useState(null);
  const [copiedTop, setCopiedTop] = useState(false);
  const [copiedBottom, setCopiedBottom] = useState(false);

  const [viewMode, setViewMode] = useState('flow'); // 'flow' or 'list'
  const [layout, setLayout] = useState('vertical'); // 'vertical' (Top/Bottom) or 'horizontal' (Side-by-Side)

  // Auto-scroll both panels down synchronously as new speech arrives
  useEffect(() => {
    if (topScrollRef.current) {
      topScrollRef.current.scrollTop = topScrollRef.current.scrollHeight;
    }
    if (bottomScrollRef.current) {
      bottomScrollRef.current.scrollTop = bottomScrollRef.current.scrollHeight;
    }
  }, [sentences]);

  const handleCopy = (text, id) => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => {
          setCopiedId(id);
          setTimeout(() => setCopiedId(null), 1500);
        })
        .catch((err) => console.error('Failed to copy text:', err));
    }
  };

  const copyAllSource = () => {
    const text = sentences.map((s) => s.source).join(' ');
    if (!text || !navigator.clipboard?.writeText) return;
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopiedTop(true);
        setTimeout(() => setCopiedTop(false), 1500);
      })
      .catch((err) => console.error(err));
  };

  const copyAllTranslated = () => {
    const text = sentences.map((s) => s.translated).join(' ');
    if (!text || !navigator.clipboard?.writeText) return;
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopiedBottom(true);
        setTimeout(() => setCopiedBottom(false), 1500);
      })
      .catch((err) => console.error(err));
  };

  const hasContent = sentences.length > 0;
  const isVertical = layout === 'vertical';

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Top Bar: Controls & Layout Switches */}
      <div className="flex items-center justify-between border-b border-[#f1f3f4] bg-white px-3 sm:px-6 py-2 shrink-0 select-none">
        {/* Left: Language Indicator */}
        <div className="flex items-center space-x-2">
          <span className="text-[13px] font-semibold text-[#1f1f1f]">
            {viewMode === 'flow' ? 'Bilingual Flow' : 'Sentence List'}
          </span>
          <div className="flex items-center space-x-1 text-xs text-[#5f6368]">
            <span className="px-1.5 py-0.5 rounded bg-[#e8f0fe] text-[#1967d2] font-semibold text-[10px] uppercase">
              {sourceLang.slice(0, 2)}
            </span>
            <span>&rarr;</span>
            <span className="px-1.5 py-0.5 rounded bg-[#e8f0fe] text-[#1967d2] font-semibold text-[10px] uppercase">
              {targetLang.slice(0, 2)}
            </span>
          </div>
        </div>

        {/* Right: Layout Split Toggle & View Mode Toggle */}
        <div className="flex items-center space-x-1.5 sm:space-x-2">
          {/* Split Mode Toggle */}
          <div className="flex items-center bg-[#f1f3f4] p-0.5 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => setLayout('vertical')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                layout === 'vertical'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Chia Trên - Dưới (Tối ưu cho cửa sổ hẹp, thấy cả 2 bản cùng lúc)"
            >
              <Rows2 size={12} />
              <span className="hidden sm:inline">Trên / Dưới</span>
            </button>
            <button
              type="button"
              onClick={() => setLayout('horizontal')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                layout === 'horizontal'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Chia Trái - Phải (Cho màn hình rộng)"
            >
              <Columns2 size={12} />
              <span className="hidden sm:inline">Trái / Phải</span>
            </button>
          </div>

          {/* View Mode Toggle: Flow vs List */}
          <div className="flex items-center bg-[#f1f3f4] p-0.5 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => setViewMode('flow')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                viewMode === 'flow'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Văn bản liền mạch"
            >
              <AlignJustify size={12} />
              <span>Flow</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-[#1a73e8] shadow-xs'
                  : 'text-[#5f6368] hover:text-[#1f1f1f]'
              }`}
              title="Danh sách từng câu"
            >
              <List size={12} />
              <span>List</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {!hasContent ? (
        <div className="flex-1 flex flex-col items-center justify-center text-[#80868b] space-y-3 select-none p-6">
          <div className="w-12 h-12 rounded-full bg-[#f8f9fa] border border-[#e8eaed] flex items-center justify-center text-[#5f6368]">
            <Languages size={24} />
          </div>
          <p className="text-sm font-normal text-[#444746] text-center">
            Bấm nút <strong className="text-[#1f1f1f] font-medium">Chia sẻ thẻ</strong> hoặc <strong className="text-[#1f1f1f] font-medium">Micro</strong> ở thanh điều khiển phía trên để bắt đầu
          </p>
          <p className="text-xs text-[#9aa0a6] text-center max-w-sm">
            Bản gốc và bản dịch sẽ hiển thị đồng thời song song theo thời gian thực
          </p>
        </div>
      ) : (
        /* Split Dual-Panel Container: Fills 100% of remaining screen height */
        <div
          className={`flex-1 min-h-0 flex ${
            isVertical ? 'flex-col' : 'flex-col md:flex-row'
          } overflow-hidden`}
        >
          {/* ========================================================= */}
          {/* PANEL 1: ORIGINAL (Ô TRÊN / TRÁI - BẢN GỐC)               */}
          {/* ========================================================= */}
          <div
            className={`flex-1 min-h-0 min-w-0 flex flex-col bg-[#fafafa]/60 ${
              isVertical ? 'border-b border-[#dadce0]' : 'border-r border-[#dadce0]'
            }`}
          >
            {/* Header for Panel 1 */}
            <div className="h-8 px-3 sm:px-4 flex items-center justify-between border-b border-[#e8eaed] bg-[#f8f9fa] shrink-0 select-none">
              <div className="flex items-center space-x-1.5">
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#e8f0fe] text-[#1967d2] uppercase tracking-wide">
                  {sourceLang.slice(0, 2).toUpperCase()}
                </span>
                <span className="text-[12px] font-medium text-[#444746]">Input Transcript (Bản gốc)</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-[#80868b]">{sentences.length} câu</span>
                <button
                  type="button"
                  onClick={copyAllSource}
                  className="flex items-center space-x-1 text-[11px] text-[#5f6368] hover:text-[#1a73e8] p-1 rounded hover:bg-black/5 transition-colors"
                  title="Sao chép toàn bộ bản gốc"
                >
                  {copiedTop ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
                  <span className="hidden sm:inline">Sao chép</span>
                </button>
              </div>
            </div>

            {/* Scrollable text area for Panel 1 */}
            <div
              ref={topScrollRef}
              className="flex-1 overflow-y-auto p-3 sm:p-4 scroll-smooth select-text"
            >
              {viewMode === 'flow' ? (
                /* Continuous Flowing Paragraph */
                <div className="text-[14px] sm:text-[15px] leading-relaxed text-[#1f1f1f] select-text cursor-text">
                  {sentences.map((item, idx) => (
                    <span
                      key={item.id || idx}
                      className={`transition-colors duration-150 rounded px-0.5 select-text ${
                        !item.is_final ? 'text-[#1f1f1f] font-normal bg-amber-50/90' : 'hover:bg-[#f1f3f4]'
                      }`}
                      title={item.source}
                    >
                      {item.source}{' '}
                    </span>
                  ))}
                </div>
              ) : (
                /* Sentence List Mode */
                <div className="space-y-2 select-text cursor-text">
                  {sentences.map((item, idx) => (
                    <div
                      key={item.id || idx}
                      className="p-2 rounded-lg hover:bg-black/5 text-[14px] leading-relaxed flex items-start space-x-2 select-text"
                    >
                      <span className="text-[10px] text-[#80868b] font-mono mt-0.5 select-none shrink-0">
                        #{idx + 1}
                      </span>
                      <span className={`select-text ${!item.is_final ? 'text-[#444746] italic' : 'text-[#1f1f1f]'}`}>
                        {item.source}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ========================================================= */}
          {/* PANEL 2: TRANSLATION (Ô DƯỚI / PHẢI - BẢN DỊCH)           */}
          {/* ========================================================= */}
          <div className="flex-1 min-h-0 min-w-0 flex flex-col bg-white">
            {/* Header for Panel 2 */}
            <div className="h-8 px-3 sm:px-4 flex items-center justify-between border-b border-[#e8eaed] bg-white shrink-0 select-none">
              <div className="flex items-center space-x-1.5">
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#e8f0fe] text-[#1967d2] uppercase tracking-wide">
                  {targetLang.slice(0, 2).toUpperCase()}
                </span>
                <span className="text-[12px] font-semibold text-[#1967d2]">Output Translation (Bản dịch)</span>
              </div>
              <button
                type="button"
                onClick={copyAllTranslated}
                className="flex items-center space-x-1 text-[11px] text-[#5f6368] hover:text-[#1a73e8] p-1 rounded hover:bg-black/5 transition-colors"
                title="Sao chép toàn bộ bản dịch"
              >
                {copiedBottom ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
                <span className="hidden sm:inline">Sao chép tất cả</span>
              </button>
            </div>

            {/* Scrollable text area for Panel 2 */}
            <div
              ref={bottomScrollRef}
              className="flex-1 overflow-y-auto p-3 sm:p-4 pb-4 scroll-smooth select-text"
            >
              {viewMode === 'flow' ? (
                /* Continuous Flowing Translation */
                <div className="text-[14px] sm:text-[15px] leading-relaxed text-[#1f1f1f] select-text cursor-text">
                  {sentences.map((item, idx) => (
                    <span
                      key={item.id || idx}
                      className={`transition-colors duration-150 rounded px-0.5 group relative select-text ${
                        !item.is_final ? 'text-[#1f1f1f] font-normal bg-amber-50/90' : 'hover:bg-[#f1f3f4]'
                      }`}
                      title={item.translated}
                    >
                      {item.translated || '...'}{' '}
                    </span>
                  ))}
                </div>
              ) : (
                /* Sentence List Translation with Pronounce & Copy */
                <div className="space-y-2 select-text cursor-text">
                  {sentences.map((item, idx) => (
                    <div
                      key={item.id || idx}
                      className="p-2 rounded-lg hover:bg-[#f8f9fa] text-[14px] leading-relaxed flex items-start justify-between space-x-2 group select-text"
                    >
                      <div className="flex items-start space-x-2 flex-1 min-w-0 select-text">
                        <span className="text-[10px] text-[#1967d2] font-semibold font-mono mt-0.5 select-none shrink-0">
                          #{idx + 1}
                        </span>
                        <span className={`select-text ${!item.is_final ? 'text-[#444746] italic' : 'font-medium text-[#1f1f1f]'}`}>
                          {item.translated || 'Translating...'}
                        </span>
                      </div>

                      {/* Item Quick Actions */}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1 shrink-0 bg-white px-1 py-0.5 rounded shadow-xs border border-[#dadce0]">
                        {onSpeakText && (
                          <button
                            type="button"
                            onClick={() => onSpeakText(item.translated)}
                            className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4]"
                            title="Nghe phát âm"
                          >
                            <Volume2 size={12} />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleCopy(item.translated, item.id || idx)}
                          className="p-1 rounded text-[#5f6368] hover:text-[#1f1f1f] hover:bg-[#f1f3f4]"
                          title="Sao chép câu này"
                        >
                          {copiedId === (item.id || idx) ? (
                            <Check size={12} className="text-green-600" />
                          ) : (
                            <Copy size={12} />
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
