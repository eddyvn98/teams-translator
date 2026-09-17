import React from 'react';
import { Monitor, Square, Code2, SlidersHorizontal, Trash2, Download } from 'lucide-react';

export default function Header({
  isCapturing,
  streamTitle,
  onStopSharing,
  onToggleSettings,
  isSettingsOpen,
  onClearTranscripts,
  onExportTranscripts,
}) {
  return (
    <header className="h-14 border-b border-[#e3e3e3] bg-white px-5 flex items-center justify-between shrink-0 z-10 select-none">
      {/* Left: Section title */}
      <div className="flex items-center space-x-3">
        <h1 className="text-[17px] font-medium text-[#1f1f1f] tracking-tight">Playground</h1>
        <span className="text-xs px-2 py-0.5 rounded-full bg-[#f1f3f4] text-[#444746] font-medium">
          Live Translate
        </span>
      </div>

      {/* Center: Share Status Notification Bar (Matching Image 2) */}
      <div className="flex items-center">
        {isCapturing && (
          <div className="flex items-center space-x-3 bg-[#f8f9fa] border border-[#dadce0] px-4 py-1.5 rounded-full shadow-xs text-xs animate-in fade-in duration-300">
            <Monitor size={14} className="text-[#1a73e8]" />
            <span className="text-[#3c4043] font-normal">
              Đang chia sẻ <strong className="font-medium text-[#202124]">{streamTitle || 'màn hình / thẻ'}</strong> với thẻ này
            </span>
            <button
              onClick={onStopSharing}
              className="bg-[#202124] hover:bg-[#3c4043] text-white px-3 py-1 rounded-full text-[11px] font-medium transition-colors flex items-center space-x-1"
            >
              <Square size={10} className="fill-white" />
              <span>Dừng chia sẻ</span>
            </button>
          </div>
        )}
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onExportTranscripts}
          className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors"
          title="Tải về bản ghi cuộc họp"
        >
          <Download size={14} />
          <span>Xuất file</span>
        </button>

        <button
          onClick={onClearTranscripts}
          className="flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors"
          title="Xóa cuộc hội thoại hiện tại"
        >
          <Trash2 size={14} />
        </button>

        <button
          className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-[#444746] hover:bg-[#f1f3f4] rounded-lg transition-colors"
          title="Xem mã tích hợp"
        >
          <Code2 size={14} />
          <span>&lt;&gt; Get code</span>
        </button>

        <button
          onClick={onToggleSettings}
          className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border ${
            isSettingsOpen
              ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8]'
              : 'border-[#dadce0] text-[#3c4043] hover:bg-[#f1f3f4]'
          }`}
        >
          <SlidersHorizontal size={14} />
          <span>Run settings</span>
        </button>
      </div>
    </header>
  );
}
