import React from 'react';
import { Mic, MicOff, Monitor, MonitorOff, X, Radio, Send } from 'lucide-react';

export default function FloatingControlPill({
  isLive,
  audioLevel = 0,
  isMicActive,
  isTabShareActive,
  onToggleTabShare,
  onToggleMic,
  onStopStream,
  onSendText,
}) {
  const [inputText, setInputText] = React.useState('');
  const [showTextInput, setShowTextInput] = React.useState(false);

  const handleSend = (e) => {
    e.preventDefault();
    if (inputText.trim() && onSendText) {
      onSendText(inputText.trim());
      setInputText('');
    }
  };

  // Height multiplier for 4 visualizer bars based on audio level
  const barHeights = [
    Math.max(4, Math.min(20, audioLevel * 140)),
    Math.max(6, Math.min(24, audioLevel * 200)),
    Math.max(4, Math.min(22, audioLevel * 170)),
    Math.max(5, Math.min(18, audioLevel * 120)),
  ];

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex flex-col items-center select-none">
      {/* Optional quick text input for testing / manual entry */}
      {showTextInput && (
        <form
          onSubmit={handleSend}
          className="mb-2 flex items-center space-x-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-full shadow-lg border border-[#dadce0] w-96 animate-in slide-in-from-bottom-2 duration-200"
        >
          <input
            type="text"
            placeholder="Nhập câu nói thử nghiệm (tiếng Anh hoặc Việt)..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 text-xs bg-transparent outline-none px-2 text-[#1f1f1f]"
            autoFocus
          />
          <button
            type="submit"
            className="p-1 rounded-full bg-[#1a73e8] text-white hover:bg-[#1557b0] transition-colors"
          >
            <Send size={12} />
          </button>
        </form>
      )}

      {/* Main Pill Dock (matching Image 2) */}
      <div className="flex items-center space-x-3 bg-white/95 backdrop-blur-md px-4 py-2 rounded-full shadow-xl border border-[#dadce0] text-[#1f1f1f] transition-all">
        {/* Status Indicator */}
        <div className="flex items-center space-x-2 pl-1 pr-2">
          {isLive ? (
            <>
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-[13px] font-medium text-[#202124]">Stream is live</span>
              <button
                onClick={onStopStream}
                className="p-1 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] hover:text-[#202124] transition-colors ml-1"
                title="Dừng phiên live"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              <span className="inline-flex rounded-full h-2.5 w-2.5 bg-gray-300"></span>
              <span className="text-[13px] font-medium text-[#5f6368]">Sẵn sàng</span>
            </>
          )}
        </div>

        {/* Separator */}
        <div className="w-[1px] h-5 bg-[#dadce0]" />

        {/* Dynamic Waveform Visualizer */}
        <div className="flex items-center space-x-1 px-1.5 h-6">
          {barHeights.map((h, i) => (
            <div
              key={i}
              className="w-1 bg-[#1a73e8] rounded-full transition-all duration-75"
              style={{ height: `${isLive ? h : 4}px` }}
            />
          ))}
        </div>

        {/* Mic Toggle Button */}
        <button
          onClick={onToggleMic}
          className={`p-2 rounded-full transition-all duration-150 ${
            isMicActive
              ? 'bg-[#e8f0fe] text-[#1a73e8] hover:bg-[#d2e3fc]'
              : 'hover:bg-[#f1f3f4] text-[#5f6368]'
          }`}
          title={isMicActive ? 'Tắt Micro' : 'Bật Micro của bạn'}
        >
          {isMicActive ? <Mic size={18} /> : <MicOff size={18} />}
        </button>

        {/* Tab/Screen Audio Share Button (Matches Image 1 & 2) */}
        <button
          onClick={onToggleTabShare}
          className={`p-2 rounded-full transition-all duration-150 ${
            isTabShareActive
              ? 'bg-[#e8f0fe] text-[#1a73e8] hover:bg-[#d2e3fc]'
              : 'hover:bg-[#f1f3f4] text-[#5f6368]'
          }`}
          title={isTabShareActive ? 'Dừng chia sẻ âm thanh thẻ' : 'Bắt đầu chia sẻ thẻ trình duyệt kèm âm thanh'}
        >
          {isTabShareActive ? <Monitor size={18} /> : <MonitorOff size={18} />}
        </button>

        {/* Toggle Manual Text Input */}
        <button
          onClick={() => setShowTextInput(!showTextInput)}
          className={`p-2 rounded-full transition-all duration-150 text-xs font-medium ${
            showTextInput ? 'bg-[#f1f3f4] text-[#1a73e8]' : 'text-[#5f6368] hover:bg-[#f1f3f4]'
          }`}
          title="Nhập văn bản thủ công"
        >
          Aa
        </button>
      </div>
    </div>
  );
}
