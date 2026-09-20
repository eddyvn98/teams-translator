import React, { useState, useCallback, useEffect } from 'react';
import Header from './components/Header';
import TranscriptBoard from './components/TranscriptBoard';
import PipVideoPreview from './components/PipVideoPreview';
import VietnameseComposer from './components/VietnameseComposer';
import SettingsDrawer from './components/SettingsDrawer';
import HistoryModal from './components/HistoryModal';
import AudioGuideModal from './components/AudioGuideModal';
import { useMeetingStream } from './hooks/useMeetingStream';

import { playNaturalSpeech } from './services/speech';

export default function App() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [isAudioGuideOpen, setIsAudioGuideOpen] = useState(false);

  // Global shortcut Ctrl+Shift+V or Cmd+Shift+V to toggle Vietnamese Composer
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'V' || e.key === 'v')) {
        e.preventDefault();
        setIsComposerOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Language & Translation state
  const [sourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('vi');
  const [echoTargetLang, setEchoTargetLang] = useState(false);
  const [systemInstructions, setSystemInstructions] = useState('');

  // Natural studio-quality speech synthesis helper
  const speakText = useCallback((text, lang) => {
    playNaturalSpeech(text, lang);
  }, []);

  const onFinalSentence = useCallback(
    (translatedText, lang) => {
      if (echoTargetLang && translatedText) {
        speakText(translatedText, lang);
      }
    },
    [echoTargetLang, speakText]
  );

  const {
    isCapturing,
    isMicActive,
    isTabShareActive,
    audioLevel,
    mediaStream,
    setMediaStream,
    streamTitle,
    sentences,
    setSentences,
    handleToggleTabShare,
    handleToggleMic,
    handleStopStream,
  } = useMeetingStream({
    sourceLang,
    targetLang,
    echoTargetLang,
    systemInstructions,
    onFinalSentence,
  });

  const handleGetReplySuggestions = async (context) => {
    try {
      const res = await fetch('/api/reply-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context,
          instruction: systemInstructions || 'Suggest 3 polite, smart, concise responses in Vietnamese.',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.suggestions || [];
      }
    } catch (e) {
      console.error('Reply Assistant request failed:', e);
    }
    return [];
  };

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

  const handleNewSession = async () => {
    try {
      await fetch('/api/session/new', { method: 'POST' });
      setSentences([]);
    } catch (e) {
      console.error('New session error:', e);
    }
  };

  const handleExportTranscripts = () => {
    if (sentences.length === 0) {
      alert('No transcripts available to export.');
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

  const meetingFullText = sentences.map((s) => s.source).join(' ');

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden">
      {/* Main Spacious Viewport */}
      <div className="flex-1 flex flex-col h-screen min-w-0 relative">
        <Header
          isCapturing={isCapturing}
          audioLevel={audioLevel}
          isMicActive={isMicActive}
          isTabShareActive={isTabShareActive}
          onToggleMic={handleToggleMic}
          onToggleTabShare={handleToggleTabShare}
          onStopStream={handleStopStream}
          streamTitle={streamTitle}
          onToggleSettings={() => setIsSettingsOpen(!isSettingsOpen)}
          isSettingsOpen={isSettingsOpen}
          onClearTranscripts={() => setSentences([])}
          onExportTranscripts={handleExportTranscripts}
          onNewSession={handleNewSession}
          onOpenHistory={() => setIsHistoryOpen(true)}
          onOpenAudioGuide={() => setIsAudioGuideOpen(true)}
          isComposerOpen={isComposerOpen}
          onToggleComposer={() => setIsComposerOpen((prev) => !prev)}
        />

        <TranscriptBoard
          sentences={sentences}
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSpeakText={(text) => speakText(text, targetLang)}
        />

        <PipVideoPreview
          mediaStream={mediaStream}
          isVisible={isTabShareActive}
          onClose={() => setMediaStream(null)}
        />

        <VietnameseComposer
          isOpen={isComposerOpen}
          onClose={() => setIsComposerOpen(false)}
          onSpeakText={speakText}
        />
      </div>

      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        targetLang={targetLang}
        setTargetLang={setTargetLang}
        echoTargetLang={echoTargetLang}
        setEchoTargetLang={setEchoTargetLang}
        systemInstructions={systemInstructions}
        setSystemInstructions={setSystemInstructions}
        onGetReplySuggestions={handleGetReplySuggestions}
        onSummarizeMeeting={handleSummarizeMeeting}
        onOpenAudioGuide={() => setIsAudioGuideOpen(true)}
        meetingText={meetingFullText}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />

      <AudioGuideModal
        isOpen={isAudioGuideOpen}
        onClose={() => setIsAudioGuideOpen(false)}
      />
    </div>
  );
}
