import React from 'react';
import {
  Mic,
  MicOff,
  Monitor,
  MonitorOff,
  X,
  SlidersHorizontal,
  Trash2,
  Download,
  Plus,
  History,
  Languages,
  Headphones,
} from 'lucide-react';

export default function Header({
  isCapturing,
  audioLevel = 0,
  isMicActive,
  isTabShareActive,
  onToggleMic,
  onToggleTabShare,
  onStopStream,
  onToggleSettings,
  isSettingsOpen,
  onClearTranscripts,
  onExportTranscripts,
  onNewSession,
  onOpenHistory,
  onOpenAudioGuide,
  isComposerOpen,
  onToggleComposer,
}) {
  // Height multiplier for 4 visualizer bars based on audio level
  const barHeights = [
    Math.max(3, Math.min(16, audioLevel * 120)),
    Math.max(4, Math.min(20, audioLevel * 160)),
    Math.max(3, Math.min(18, audioLevel * 140)),
    Math.max(4, Math.min(15, audioLevel * 100)),
  ];

  return (
    <header className="h-14 border-b border-[#e3e3e3] bg-white px-3 sm:px-5 flex items-center justify-between shrink-0 z-20 select-none">
      {/* Left: Brand / Title */}
      <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-[#1a73e8] text-white flex items-center justify-center font-bold text-sm shadow-xs shrink-0">
          <Languages size={18} />
        </div>
        <div className="flex items-center space-x-2">
          <h1 className="text-[15px] sm:text-[16px] font-semibold text-[#1f1f1f] tracking-tight">
            Teams Translator
          </h1>
          <span className="hidden sm:inline-flex text-[11px] px-2 py-0.5 rounded-full bg-[#f1f3f4] text-[#444746] font-medium">
            Live Stream
          </span>
        </div>
      </div>

      {/* Center: Live Meeting Control Pill (Moved up from bottom) */}
      <div className="flex items-center space-x-1 sm:space-x-2 bg-white sm:bg-[#f8f9fa] border border-[#dadce0] px-2.5 sm:px-3 py-1 rounded-full shadow-2xs">
        {/* Status Indicator */}
        <div className="flex items-center space-x-1.5 pl-0.5 pr-1">
          {isCapturing ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[12px] font-semibold text-[#202124]">Live</span>
              <button
                type="button"
                onClick={onStopStream}
                className="p-0.5 rounded-full hover:bg-black/10 text-[#5f6368] hover:text-[#202124] transition-colors ml-0.5"
                title="Dừng phiên live"
              >
                <X size={13} />
              </button>
            </>
          ) : (
            <>
              <span className="inline-flex rounded-full h-2 w-2 bg-gray-300"></span>
              <span className="text-[12px] font-medium text-[#5f6368]">Ready</span>
            </>
          )}
        </div>

        {/* Separator */}
        <div className="w-[1px] h-4 bg-[#dadce0]" />

        {/* Dynamic Waveform Visualizer */}
        <div className="flex items-center space-x-0.5 px-0.5 h-4">
          {barHeights.map((h, i) => (
            <div
              key={i}
              className="w-0.5 sm:w-1 bg-[#1a73e8] rounded-full transition-all duration-75"
              style={{ height: `${isCapturing ? h : 3}px` }}
            />
          ))}
        </div>

        {/* Mic Toggle Button */}
        <button
          type="button"
          onClick={onToggleMic}
          className={`p-1.5 rounded-full transition-colors ${
            isMicActive
              ? 'bg-[#e8f0fe] text-[#1a73e8]'
              : 'hover:bg-[#e8eaed] text-[#5f6368]'
          }`}
          title={isMicActive ? 'Tắt Micro' : 'Bật Micro'}
        >
          {isMicActive ? <Mic size={15} /> : <MicOff size={15} />}
        </button>

        {/* Tab/Screen Audio Share Button */}
        <button
          type="button"
          onClick={onToggleTabShare}
          className={`p-1.5 rounded-full transition-colors ${
            isTabShareActive
              ? 'bg-[#e8f0fe] text-[#1a73e8]'
              : 'hover:bg-[#e8eaed] text-[#5f6368]'
          }`}
          title={isTabShareActive ? 'Dừng chia sẻ âm thanh thẻ' : 'Chia sẻ âm thanh cuộc họp / thẻ'}
        >
          {isTabShareActive ? <Monitor size={15} /> : <MonitorOff size={15} />}
        </button>

        {/* Nút Aa: Soạn Tiếng Việt -> Dịch Tiếng Anh */}
        <button
          type="button"
          onClick={onToggleComposer}
          className={`px-2 py-0.5 rounded-full text-xs font-semibold transition-all flex items-center space-x-1 ${
            isComposerOpen
              ? 'bg-[#1a73e8] text-white shadow-xs'
              : 'bg-[#f1f3f4] text-[#3c4043] hover:bg-[#e8eaed]'
          }`}
          title="Soạn Tiếng Việt → Dịch Tiếng Anh (Ctrl+Shift+V)"
        >
          <span>Aa</span>
        </button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-1 sm:space-x-1.5 shrink-0">
        <button
          type="button"
          onClick={onNewSession}
          className="flex items-center space-x-1 p-2 sm:px-2.5 sm:py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors border border-transparent hover:border-[#dadce0]"
          title="Start a new meeting session"
        >
          <Plus size={14} />
          <span className="hidden xl:inline">New Session</span>
        </button>

        <button
          type="button"
          onClick={onOpenHistory}
          className="flex items-center space-x-1 p-2 sm:px-2.5 sm:py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors border border-transparent hover:border-[#dadce0]"
          title="Open meeting history"
        >
          <History size={14} />
          <span className="hidden lg:inline">History</span>
        </button>

        <button
          type="button"
          onClick={onExportTranscripts}
          className="flex items-center space-x-1 p-2 sm:px-2.5 sm:py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors border border-transparent hover:border-[#dadce0]"
          title="Export transcript as text file"
        >
          <Download size={14} />
          <span className="hidden lg:inline">Export</span>
        </button>

        <button
          type="button"
          onClick={onClearTranscripts}
          className="flex items-center justify-center p-2 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors"
          title="Clear current transcript"
        >
          <Trash2 size={14} />
        </button>

        <div className="w-[1px] h-5 bg-[#dadce0] mx-0.5 sm:mx-1" />

        <button
          type="button"
          onClick={onOpenAudioGuide}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all border border-[#d2e3fc] bg-[#e8f0fe] text-[#1a73e8] hover:bg-[#d9e7fd] shadow-2xs"
          title="Xem hướng dẫn cấu hình âm thanh cho Mac, Windows và Teams"
        >
          <Headphones size={14} className="shrink-0" />
          <span className="hidden md:inline">Cấu hình Audio</span>
        </button>

        <button
          type="button"
          onClick={onToggleSettings}
          className={`flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium rounded-lg transition-colors border ${
            isSettingsOpen
              ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8]'
              : 'border-[#dadce0] text-[#3c4043] hover:bg-[#f1f3f4]'
          }`}
          title="Toggle settings drawer"
        >
          <SlidersHorizontal size={14} />
          <span className="hidden sm:inline">Settings</span>
        </button>
      </div>
    </header>
  );
}
