import React, { useState } from 'react';
import {
  X,
  Code2,
  Globe,
  Sparkles,
  FileText,
  Copy,
  Check,
  ChevronDown,
  Volume2,
  RefreshCw,
} from 'lucide-react';

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

const MODELS = [
  {
    id: 'gemini-live',
    name: 'Gemini 3.5 Live Translate Preview',
    desc: 'A real-time speech-to-speech translation model delivering low latency translation for 70+ languages.',
  },
  {
    id: 'sensevoice',
    name: 'SenseVoice Small ASR + Google Translate',
    desc: 'Mô hình nhận dạng giọng nói đa ngôn ngữ siêu tốc kết hợp bộ dịch ngữ cảnh.',
  },
  {
    id: 'whisper',
    name: 'Faster Whisper + Realtime Pipeline',
    desc: 'Mô hình ASR chính xác cao tối ưu hóa cho môi trường họp trực tuyến.',
  },
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
  selectedModel,
  setSelectedModel,
  onGetReplySuggestions,
  onSummarizeMeeting,
  meetingText = '',
}) {
  const [replies, setReplies] = useState([]);
  const [summary, setSummary] = useState('');
  const [isLoadingReplies, setIsLoadingReplies] = useState(false);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [copiedReply, setCopiedReply] = useState(null);

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
    navigator.clipboard.writeText(text);
    setCopiedReply(idx);
    setTimeout(() => setCopiedReply(null), 1500);
  };

  return (
    <aside className="w-80 border-l border-[#e3e3e3] bg-white h-screen flex flex-col justify-between shrink-0 select-none z-20 overflow-y-auto">
      {/* Top Header (Matching Image 2) */}
      <div>
        <div className="flex items-center justify-between px-5 h-14 border-b border-[#f1f3f4]">
          <span className="text-[14px] font-medium text-[#1f1f1f]">Run settings</span>
          <div className="flex items-center space-x-1">
            <button
              className="flex items-center space-x-1 px-2 py-1 text-xs text-[#444746] hover:bg-[#f1f3f4] rounded"
              title="Get code"
            >
              <Code2 size={13} />
              <span>&lt;&gt; Get code</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-full text-[#444746] hover:bg-[#f1f3f4]"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-6">
          {/* Model Card */}
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-[#444746]">Model</label>
            <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#e8eaed] space-y-1">
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full text-xs font-semibold text-[#1f1f1f] bg-transparent outline-none cursor-pointer"
              >
                {MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-[#5f6368] leading-relaxed">
                {MODELS.find((m) => m.id === selectedModel)?.desc || ''}
              </p>
            </div>
          </div>

          {/* System instructions */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[12px] font-medium text-[#444746]">System instructions</label>
            </div>
            <p className="text-[11px] text-[#747775]">Optional tone and style instructions for the model</p>
            <textarea
              rows={3}
              value={systemInstructions}
              onChange={(e) => setSystemInstructions(e.target.value)}
              placeholder="Ví dụ: Dịch tự nhiên theo phong cách hội họp công nghệ, xưng hô anh/em lịch sự..."
              className="w-full text-xs p-2.5 rounded-lg border border-[#dadce0] focus:border-[#1a73e8] focus:ring-1 focus:ring-[#1a73e8] outline-none text-[#1f1f1f] resize-none"
            />
          </div>

          {/* Target language (matching Image 2) */}
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-[#444746]">Target language</label>
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

          {/* Echo target language toggle (matching Image 2) */}
          <div className="flex items-center justify-between pt-1">
            <div>
              <div className="text-[12px] font-medium text-[#1f1f1f]">Echo target language</div>
              <div className="text-[11px] text-[#747775]">Phát âm thanh bản dịch qua loa (TTS)</div>
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
                className="text-[11px] text-[#1a73e8] hover:underline disabled:opacity-50 flex items-center space-x-1"
              >
                {isLoadingReplies && <RefreshCw size={10} className="animate-spin" />}
                <span>Gợi ý</span>
              </button>
            </div>

            {replies.length > 0 && (
              <div className="space-y-1.5 pt-1">
                {replies.map((reply, i) => (
                  <div
                    key={i}
                    onClick={() => copyToClipboard(reply, i)}
                    className="p-2 rounded-lg bg-[#f8f9fa] border border-[#e8eaed] text-[11px] text-[#3c4043] hover:border-[#1a73e8] cursor-pointer group flex items-start justify-between space-x-2"
                  >
                    <span className="flex-1">{reply}</span>
                    <button className="text-[#80868b] group-hover:text-[#1a73e8] shrink-0 pt-0.5">
                      {copiedReply === i ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* One-click Meeting Summary */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <FileText size={14} className="text-[#1a73e8]" />
                <span className="text-[12px] font-medium text-[#1f1f1f]">Tóm tắt cuộc họp</span>
              </div>
              <button
                onClick={handleGenerateSummary}
                disabled={isLoadingSummary || !meetingText}
                className="text-[11px] text-[#1a73e8] hover:underline disabled:opacity-50 flex items-center space-x-1"
              >
                {isLoadingSummary && <RefreshCw size={10} className="animate-spin" />}
                <span>Tóm tắt</span>
              </button>
            </div>

            {summary && (
              <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#e8eaed] text-[11px] text-[#3c4043] leading-relaxed whitespace-pre-line">
                {summary}
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
