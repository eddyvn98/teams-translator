import React, { useEffect, useState } from 'react';
import { X, Download, Clock, RefreshCw, MessageSquare } from 'lucide-react';

export default function HistoryModal({ isOpen, onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [meetingId, setMeetingId] = useState('');

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.transcripts || []);
        setMeetingId(data.meeting_id || '');
      }
    } catch (e) {
      console.error('Failed to load history:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleExport = () => {
    const text = history
      .map(
        (t) =>
          `[${new Date(t.ts * 1000).toLocaleTimeString()}] (${t.source_lang || 'EN'}): ${t.source_text}\n` +
          `-> (VI): ${t.translated_text}\n`
      )
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${meetingId || 'meeting'}_transcript.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-[#dadce0] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#f1f3f4]">
          <div className="flex items-center space-x-2">
            <Clock size={18} className="text-[#1a73e8]" />
            <h2 className="text-[16px] font-medium text-[#1f1f1f]">Lịch sử cuộc họp</h2>
            <span className="text-xs px-2 py-0.5 rounded-md bg-[#f1f3f4] text-[#5f6368]">
              {meetingId}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExport}
              disabled={history.length === 0}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-[#1a73e8] hover:bg-[#e8f0fe] rounded-lg transition-colors disabled:opacity-50"
            >
              <Download size={14} />
              <span>Xuất file txt</span>
            </button>
            <button
              onClick={fetchHistory}
              className="p-1.5 rounded-full text-[#5f6368] hover:bg-[#f1f3f4]"
              title="Làm mới"
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-full text-[#5f6368] hover:bg-[#f1f3f4]"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {history.length === 0 ? (
            <div className="py-12 text-center text-[#80868b] space-y-2">
              <MessageSquare size={32} className="mx-auto text-[#dadce0]" />
              <p className="text-sm">Chưa có bản ghi nào trong phiên hiện tại.</p>
            </div>
          ) : (
            history.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] space-y-1.5"
              >
                <div className="flex items-center justify-between text-[11px] text-[#747775]">
                  <span className="font-semibold text-[#1a73e8] uppercase">
                    {item.source_lang || 'EN'}
                  </span>
                  <span>
                    {item.ts ? new Date(item.ts * 1000).toLocaleTimeString() : ''}
                  </span>
                </div>
                <div className="text-xs text-[#202124]">{item.source_text}</div>
                <div className="text-xs text-[#1967d2] font-normal pt-1 border-t border-[#f1f3f4]">
                  {item.translated_text}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
