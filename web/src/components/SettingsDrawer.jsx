import React, { useState, useEffect } from 'react';
import {
  X,
  Globe,
  Sparkles,
  FileText,
  Copy,
  Check,
  ChevronDown,
  RefreshCw,
  Headphones,
  ChevronRight,
  Volume2,
  Play,
} from 'lucide-react';
import { audioRouter } from '../services/audioRouter';

const TARGET_LANGUAGES = [
  { code: 'vi', name: 'Vietnamese', native: 'Tiếng Việt' },
  { code: 'en', name: 'English', native: 'English' },
  { code: 'ja', name: 'Japanese', native: '日本語' },
  { code: 'zh-CN', name: 'Chinese', native: '中文 (简体)' },
  { code: 'ko', name: 'Korean', native: '한국어' },
  { code: 'fr', name: 'French', native: 'Français' },
  { code: 'de', name: 'German', native: 'Deutsch' },
  { code: 'es', name: 'Spanish', native: 'Español' },
];

export default function SettingsDrawer({
  isOpen,
  onClose,
  targetLang,
  setTargetLang,
  echoTargetLang,
  setEchoTargetLang,
  systemInstructions,
  setSystemInstructions,
  onGetReplySuggestions,
  onSummarizeMeeting,
  onOpenAudioGuide,
  meetingText = '',
}) {
  const [replies, setReplies] = useState([]);
  const [summary, setSummary] = useState('');
  const [isLoadingReplies, setIsLoadingReplies] = useState(false);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [copiedReply, setCopiedReply] = useState(null);

  const [audioOutputs, setAudioOutputs] = useState(audioRouter.audioOutputs);
  const [virtualDev, setVirtualDev] = useState(audioRouter.virtualDeviceId);
  const [monitorDev, setMonitorDev] = useState(audioRouter.monitorDeviceId);
  const [isTestingAudio, setIsTestingAudio] = useState(false);

  useEffect(() => {
    const unsubscribe = audioRouter.subscribe((state) => {
      setAudioOutputs(state.audioOutputs);
      setVirtualDev(state.virtualDeviceId);
      setMonitorDev(state.monitorDeviceId);
    });
    audioRouter.refreshDevices();
    return unsubscribe;
  }, []);

  if (!isOpen) return null;

  const handleGenerateReplies = async () => {
    if (!meetingText) return;
    setIsLoadingReplies(true);
    try {
      const suggestions = await onGetReplySuggestions(meetingText);
      setReplies(suggestions || []);
    } finally {
      setIsLoadingReplies(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!meetingText) return;
    setIsLoadingSummary(true);
    try {
      const sum = await onSummarizeMeeting(meetingText);
      setSummary(sum || '');
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const copyToClipboard = (text, idx) => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => {
          setCopiedReply(idx);
          setTimeout(() => setCopiedReply(null), 1500);
        })
        .catch((err) => console.error('Failed to copy to clipboard:', err));
    }
  };

  return (
    <aside className="w-80 border-l border-[#e3e3e3] bg-white h-screen flex flex-col justify-between shrink-0 select-none z-20 overflow-y-auto">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-[#f1f3f4]">
          <span className="text-[14px] font-semibold text-[#1f1f1f]">Settings & AI Tools</span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#444746] hover:bg-[#f1f3f4] transition-colors"
            title="Close drawer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-6">
          {/* Audio Setup Guide Banner */}
          <button
            type="button"
            onClick={() => {
              onClose();
              onOpenAudioGuide?.();
            }}
            className="w-full p-3 rounded-xl bg-[#e8f0fe] border border-[#d2e3fc] hover:bg-[#d9e7fd] transition-all flex items-center justify-between text-left group shadow-2xs cursor-pointer"
          >
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#1a73e8] text-white flex items-center justify-center shrink-0 shadow-2xs">
                <Headphones size={16} />
              </div>
              <div>
                <div className="text-[12px] font-semibold text-[#1a73e8]">Cấu hình Audio & Teams</div>
                <div className="text-[10px] text-[#5f6368]">Hướng dẫn macOS, Win, Bluetooth</div>
              </div>
            </div>
            <ChevronRight size={15} className="text-[#1a73e8] group-hover:translate-x-0.5 transition-transform" />
          </button>

          {/* Target language */}
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-[#444746]">Target Language</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-[#5f6368]">
                <Globe size={14} />
              </div>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full pl-8 pr-8 py-2 text-xs font-medium rounded-lg border border-[#dadce0] bg-white text-[#1f1f1f] appearance-none cursor-pointer outline-none focus:border-[#1a73e8]"
              >
                {TARGET_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} ({lang.native})
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none text-[#5f6368]">
                <ChevronDown size={14} />
              </div>
            </div>
          </div>

          {/* Echo target language toggle */}
          <div className="flex items-center justify-between pt-1">
            <div>
              <div className="text-[12px] font-medium text-[#1f1f1f]">Echo via TTS</div>
              <div className="text-[11px] text-[#747775]">Read translation aloud in browser</div>
            </div>
            <button
              onClick={() => setEchoTargetLang(!echoTargetLang)}
              className={`w-10 h-6 flex items-center rounded-full p-1 transition-colors duration-200 cursor-pointer ${
                echoTargetLang ? 'bg-[#1a73e8]' : 'bg-[#dadce0]'
              }`}
            >
              <div
                className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ${
                  echoTargetLang ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          <div className="h-[1px] bg-[#f1f3f4]" />

          {/* Browser Audio Routing (Cách 1) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-[12px] font-semibold text-[#1f1f1f] flex items-center space-x-1.5">
                <Volume2 size={15} className="text-[#1a73e8]" />
                <span>Định tuyến Audio (Cách 1)</span>
              </label>
              <button
                type="button"
                onClick={async () => {
                  setIsTestingAudio(true);
                  await audioRouter.testPlayback();
                  setTimeout(() => setIsTestingAudio(false), 900);
                }}
                className="text-[11px] px-2 py-0.5 rounded-md bg-[#e8f0fe] text-[#1a73e8] hover:bg-[#d2e3fc] transition-colors flex items-center space-x-1 font-medium cursor-pointer"
                title="Phát thử âm thanh vào cả Teams và Loa ngoài"
              >
                <Play size={11} className={isTestingAudio ? 'animate-spin' : ''} />
                <span>{isTestingAudio ? 'Đang phát...' : 'Thử loa & mic'}</span>
              </button>
            </div>

            {/* Virtual Cable Output for Teams */}
            <div className="space-y-1">
              <span className="text-[11px] font-medium text-[#444746]">Cổng vào Teams (BlackHole / CABLE):</span>
              <select
                value={virtualDev}
                onChange={(e) => {
                  setVirtualDev(e.target.value);
                  audioRouter.setVirtualDevice(e.target.value);
                }}
                className="w-full text-xs p-2 rounded-lg border border-[#dadce0] bg-white text-[#1f1f1f] outline-none focus:border-[#1a73e8]"
              >
                <option value="">-- Tự động chọn cáp ảo --</option>
                {audioOutputs.map((d) => (
                  <option key={d.deviceId} value={d.deviceId}>
                    {d.label || `Thiết bị ${d.deviceId.slice(0, 8)}`}
                  </option>
                ))}
              </select>
            </div>

            {/* Monitor Speaker Output */}
            <div className="space-y-1">
              <span className="text-[11px] font-medium text-[#444746]">Cổng Loa kiểm âm (Bạn tự nghe):</span>
              <select
                value={monitorDev}
                onChange={(e) => {
                  setMonitorDev(e.target.value);
                  audioRouter.setMonitorDevice(e.target.value);
                }}
                className="w-full text-xs p-2 rounded-lg border border-[#dadce0] bg-white text-[#1f1f1f] outline-none focus:border-[#1a73e8]"
              >
                <option value="">-- Mặc định hệ thống --</option>
                {audioOutputs.map((d) => (
                  <option key={d.deviceId} value={d.deviceId}>
                    {d.label || `Thiết bị ${d.deviceId.slice(0, 8)}`}
                  </option>
                ))}
              </select>
            </div>

            {audioOutputs.length === 0 && (
              <button
                type="button"
                onClick={async () => {
                  try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    stream.getTracks().forEach((t) => t.stop());
                    audioRouter.refreshDevices();
                  } catch {}
                }}
                className="text-[11px] text-[#1a73e8] underline cursor-pointer"
              >
                Cấp quyền micro để hiển thị danh sách thiết bị
              </button>
            )}
          </div>

          <div className="h-[1px] bg-[#f1f3f4]" />

          {/* System instructions */}
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-[#444746]">System Instructions</label>
            <p className="text-[11px] text-[#747775]">Tone and style guidelines for translation & replies</p>
            <textarea
              rows={3}
              value={systemInstructions}
              onChange={(e) => setSystemInstructions(e.target.value)}
              placeholder="E.g. Professional meeting tone, polite and concise translation..."
              className="w-full text-xs p-2.5 rounded-lg border border-[#dadce0] focus:border-[#1a73e8] focus:ring-1 focus:ring-[#1a73e8] outline-none text-[#1f1f1f] resize-none"
            />
          </div>

          <div className="h-[1px] bg-[#f1f3f4]" />

          {/* AI Reply Assistant Feature */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Sparkles size={14} className="text-[#1a73e8]" />
                <span className="text-[12px] font-medium text-[#1f1f1f]">AI Reply Assistant</span>
              </div>
              <button
                onClick={handleGenerateReplies}
                disabled={isLoadingReplies || !meetingText}
                className="text-[11px] text-[#1a73e8] hover:underline disabled:opacity-50 flex items-center space-x-1 font-medium"
              >
                {isLoadingReplies && <RefreshCw size={10} className="animate-spin" />}
                <span>Suggest</span>
              </button>
            </div>

            {replies.length > 0 ? (
              <div className="space-y-1.5 pt-1">
                {replies.map((reply, i) => (
                  <div
                    key={i}
                    onClick={() => copyToClipboard(reply, i)}
                    className="p-2 rounded-lg bg-[#f8f9fa] border border-[#e8eaed] text-[11px] text-[#3c4043] hover:border-[#1a73e8] cursor-pointer group flex items-start justify-between space-x-2"
                  >
                    <span className="flex-1 leading-snug select-text cursor-text">{reply}</span>
                    <button className="text-[#80868b] group-hover:text-[#1a73e8] shrink-0 pt-0.5">
                      {copiedReply === i ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-[#9aa0a6]">
                Click Suggest to generate quick responses based on recent meeting conversation.
              </p>
            )}
          </div>

          {/* Meeting Summary */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <FileText size={14} className="text-[#1a73e8]" />
                <span className="text-[12px] font-medium text-[#1f1f1f]">Meeting Summary</span>
              </div>
              <button
                onClick={handleGenerateSummary}
                disabled={isLoadingSummary || !meetingText}
                className="text-[11px] text-[#1a73e8] hover:underline disabled:opacity-50 flex items-center space-x-1 font-medium"
              >
                {isLoadingSummary && <RefreshCw size={10} className="animate-spin" />}
                <span>Summarize</span>
              </button>
            </div>

            {summary && (
              <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#e8eaed] text-[11px] text-[#3c4043] leading-relaxed whitespace-pre-line select-text cursor-text">
                {summary}
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
