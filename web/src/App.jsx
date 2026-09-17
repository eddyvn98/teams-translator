import React, { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import TranscriptBoard from './components/TranscriptBoard';
import PipVideoPreview from './components/PipVideoPreview';
import FloatingControlPill from './components/FloatingControlPill';
import SettingsDrawer from './components/SettingsDrawer';
import HistoryModal from './components/HistoryModal';
import { AudioCaptureService } from './services/audioCapture';
import { StreamWebSocketClient } from './services/websocketClient';

export default function App() {
  // Navigation & UI state
  const [activeTab, setActiveTab] = useState('playground');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(true);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Stream state
  const [isCapturing, setIsCapturing] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [isTabShareActive, setIsTabShareActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [mediaStream, setMediaStream] = useState(null);
  const [streamTitle, setStreamTitle] = useState('');

  // Transcripts & Language state
  const [sentences, setSentences] = useState([]);
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('vi');
  const [echoTargetLang, setEchoTargetLang] = useState(false);
  const [systemInstructions, setSystemInstructions] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini-live');

  // Services references
  const audioServiceRef = useRef(null);
  const wsClientRef = useRef(null);

  // Initialize Audio & WebSocket service
  useEffect(() => {
    audioServiceRef.current = new AudioCaptureService((level) => {
      setAudioLevel(level);
    });

    wsClientRef.current = new StreamWebSocketClient({
      onSentence: (data) => {
        setSentences((prev) => {
          const idx = prev.findIndex((s) => s.id === data.id);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = {
              ...copy[idx],
              source: data.source,
              translated: data.translated,
              is_final: data.is_final,
            };
            return copy;
          } else {
            return [
              ...prev,
              {
                id: data.id,
                source: data.source,
                translated: data.translated,
                is_final: data.is_final,
                src_lang: data.src_lang || sourceLang,
                target_lang: data.target_lang || targetLang,
                timestamp: data.timestamp || Date.now() / 1000,
              },
            ];
          }
        });

        // Echo target language via Web SpeechSynthesis if enabled & sentence finalized
        if (data.is_final && echoTargetLang && data.translated) {
          speakText(data.translated, targetLang);
        }
      },
      onTranscript: (data) => {
        // Fallback for standalone input
        if (data.text) {
          setSentences((prev) => {
            const last = prev[prev.length - 1];
            if (last && !last.is_final) {
              const copy = [...prev];
              copy[copy.length - 1] = { ...last, source: data.text };
              return copy;
            }
            return prev;
          });
        }
      },
      onTranslation: (data) => {
        // Fallback for standalone input
        setSentences((prev) => {
          const last = prev[prev.length - 1];
          if (last && !last.is_final) {
            const copy = [...prev];
            copy[copy.length - 1] = { ...last, translated: data.translated, is_final: true };
            return copy;
          }
          return [
            ...prev,
            {
              id: String(Date.now()),
              source: data.original,
              translated: data.translated,
              is_final: true,
              src_lang: data.src_lang || sourceLang,
              target_lang: data.target_lang || targetLang,
              timestamp: data.timestamp || Date.now() / 1000,
            },
          ];
        });
      },
      onStatus: (msg) => {
        console.log('[WS Status]', msg);
      },
      onError: (err) => {
        console.error('[WS Error]', err);
      },
    });

    wsClientRef.current.connect();

    return () => {
      if (audioServiceRef.current) {
        audioServiceRef.current.stopCapture();
      }
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
      }
    };
  }, [echoTargetLang, sourceLang, targetLang]);

  // Sync config to WebSocket server whenever changed
  useEffect(() => {
    if (wsClientRef.current) {
      wsClientRef.current.sendConfig({
        sourceLang,
        targetLang,
        echo: echoTargetLang,
        systemInstruction: systemInstructions,
      });
    }
  }, [sourceLang, targetLang, echoTargetLang, systemInstructions]);

  // Web SpeechSynthesis helper
  const speakText = (text, lang) => {
    try {
      window.speechSynthesis.cancel(); // Stop any pending speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      if (lang === 'vi') utterance.lang = 'vi-VN';
      else if (lang === 'en') utterance.lang = 'en-US';
      else utterance.lang = lang;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('SpeechSynthesis error:', e);
    }
  };

  // Start / Toggle Tab Share (Chrome tab capture with audio)
  const handleToggleTabShare = async () => {
    if (isTabShareActive) {
      handleStopStream();
      return;
    }

    try {
      const stream = await audioServiceRef.current.startTabCapture((pcmChunk) => {
        if (wsClientRef.current) {
          wsClientRef.current.sendAudioChunk(pcmChunk);
        }
      });

      setMediaStream(stream);
      setIsTabShareActive(true);
      setIsCapturing(true);

      const videoTrack = stream.getVideoTracks()[0];
      setStreamTitle(videoTrack ? videoTrack.label : 'Tab trình duyệt');

      videoTrack.onended = () => {
        handleStopStream();
      };
    } catch (err) {
      if (err.name !== 'NotAllowedError') {
        alert(err.message || 'Không thể bắt âm thanh từ thẻ trình duyệt.');
      }
      setIsTabShareActive(false);
      setIsCapturing(false);
    }
  };

  // Start / Toggle Microphone Capture
  const handleToggleMic = async () => {
    if (isMicActive) {
      if (audioServiceRef.current) {
        audioServiceRef.current.stopCapture();
      }
      setIsMicActive(false);
      if (!isTabShareActive) {
        setIsCapturing(false);
      }
      return;
    }

    try {
      await audioServiceRef.current.startMicCapture((pcmChunk) => {
        if (wsClientRef.current) {
          wsClientRef.current.sendAudioChunk(pcmChunk);
        }
      });
      setIsMicActive(true);
      setIsCapturing(true);
    } catch (err) {
      alert('Không thể truy cập microphone. Vui lòng cấp quyền trong trình duyệt.');
      setIsMicActive(false);
    }
  };

  // Stop all active streams
  const handleStopStream = useCallback(() => {
    if (audioServiceRef.current) {
      audioServiceRef.current.stopCapture();
    }
    setMediaStream(null);
    setIsTabShareActive(false);
    setIsMicActive(false);
    setIsCapturing(false);
    setAudioLevel(0);
    setStreamTitle('');
  }, []);

  // Send manual text for testing translation
  const handleSendText = (text) => {
    if (wsClientRef.current) {
      wsClientRef.current.sendTextInput(text);
    }
  };

  // AI Reply Assistant request
  const handleGetReplySuggestions = async (context) => {
    try {
      const res = await fetch('/api/reply-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context,
          instruction: systemInstructions || 'Gợi ý 3 câu phản hồi lịch sự, thông minh, ngắn gọn.',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.suggestions;
      }
    } catch (e) {
      console.error('Reply Assistant request failed:', e);
    }
    return [];
  };

  // One-click Summary request
  const handleSummarizeMeeting = async (text) => {
    try {
      const res = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.summary;
      }
    } catch (e) {
      console.error('Summarize request failed:', e);
    }
    return '';
  };

  // New session
  const handleNewSession = async () => {
    try {
      await fetch('/api/session/new', { method: 'POST' });
      setSentences([]);
    } catch (e) {
      console.error('New session error:', e);
    }
  };

  // Export transcripts as text file
  const handleExportTranscripts = () => {
    if (sentences.length === 0) {
      alert('Chưa có nội dung cuộc họp để xuất file.');
      return;
    }
    const content = sentences
      .map((s) => `[${s.src_lang || sourceLang}]: ${s.source}\n[${s.target_lang || targetLang}]: ${s.translated}\n`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Meeting_Transcript_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Build current meeting context for AI
  const meetingFullText = sentences.map((s) => s.source).join(' ');

  return (
    <div className="flex h-screen w-screen bg-[#ffffff] overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewSession={handleNewSession}
        onOpenSettings={() => setIsSettingsOpen(!isSettingsOpen)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        collapsed={isSidebarCollapsed}
        setCollapsed={setIsSidebarCollapsed}
      />

      {/* Main Center Area */}
      <div className="flex-1 flex flex-col h-screen min-w-0 relative">
        {/* Header with Share notification bar */}
        <Header
          isCapturing={isCapturing}
          streamTitle={streamTitle}
          onStopSharing={handleStopStream}
          onToggleSettings={() => setIsSettingsOpen(!isSettingsOpen)}
          isSettingsOpen={isSettingsOpen}
          onClearTranscripts={() => setSentences([])}
          onExportTranscripts={handleExportTranscripts}
        />

        {/* Dual-column Transcript Board */}
        <TranscriptBoard
          sentences={sentences}
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSpeakText={(text) => speakText(text, targetLang)}
        />

        {/* Floating PiP Video Preview for captured tab */}
        <PipVideoPreview
          mediaStream={mediaStream}
          isVisible={isTabShareActive}
          onClose={() => setMediaStream(null)}
        />

        {/* Floating Bottom Control Pill */}
        <FloatingControlPill
          isLive={isCapturing}
          audioLevel={audioLevel}
          isMicActive={isMicActive}
          isTabShareActive={isTabShareActive}
          onToggleTabShare={handleToggleTabShare}
          onToggleMic={handleToggleMic}
          onStopStream={handleStopStream}
          onSendText={handleSendText}
        />
      </div>

      {/* Right Settings & Assistant Drawer */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        targetLang={targetLang}
        setTargetLang={setTargetLang}
        echoTargetLang={echoTargetLang}
        setEchoTargetLang={setEchoTargetLang}
        systemInstructions={systemInstructions}
        setSystemInstructions={setSystemInstructions}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        onGetReplySuggestions={handleGetReplySuggestions}
        onSummarizeMeeting={handleSummarizeMeeting}
        meetingText={meetingFullText}
      />

      {/* History Modal */}
      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
    </div>
  );
}
