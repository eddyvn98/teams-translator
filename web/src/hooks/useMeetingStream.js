import { useState, useEffect, useRef, useCallback } from 'react';
import { AudioCaptureService } from '../services/audioCapture';
import { StreamWebSocketClient } from '../services/websocketClient';
import { audioRouter } from '../services/audioRouter';

export function useMeetingStream({
  sourceLang,
  targetLang,
  echoTargetLang,
  systemInstructions,
  onFinalSentence,
}) {
  const [isCapturing, setIsCapturing] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [isTabShareActive, setIsTabShareActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [mediaStream, setMediaStream] = useState(null);
  const [streamTitle, setStreamTitle] = useState('');
  const [sentences, setSentences] = useState([]);

  const audioServiceRef = useRef(null);
  const wsClientRef = useRef(null);
  const sourceLangRef = useRef(sourceLang);
  const targetLangRef = useRef(targetLang);
  const onFinalSentenceRef = useRef(onFinalSentence);

  useEffect(() => {
    sourceLangRef.current = sourceLang;
  }, [sourceLang]);

  useEffect(() => {
    targetLangRef.current = targetLang;
  }, [targetLang]);

  useEffect(() => {
    onFinalSentenceRef.current = onFinalSentence;
  }, [onFinalSentence]);

  useEffect(() => {
    audioRouter.init().catch(console.warn);

    audioServiceRef.current = new AudioCaptureService((level) => {
      setAudioLevel(level);
    });

    wsClientRef.current = new StreamWebSocketClient({
      onRemoteSpeech: (data) => {
        if (data.audio_base64) {
          audioRouter.playDualAudio(data.audio_base64);
        }
      },
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
          }
          return [
            ...prev,
            {
              id: data.id,
              source: data.source,
              translated: data.translated,
              is_final: data.is_final,
              src_lang: data.src_lang || sourceLangRef.current,
              target_lang: data.target_lang || targetLangRef.current,
              timestamp: data.timestamp || Date.now() / 1000,
            },
          ];
        });

        if (data.is_final && onFinalSentenceRef.current && data.translated) {
          onFinalSentenceRef.current(data.translated, targetLangRef.current);
        }
      },
      onTranscript: (data) => {
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
              src_lang: data.src_lang || sourceLangRef.current,
              target_lang: data.target_lang || targetLangRef.current,
              timestamp: data.timestamp || Date.now() / 1000,
            },
          ];
        });
      },
      onStatus: (msg) => console.log('[WS Status]', msg),
      onError: (err) => console.error('[WS Error]', err),
    });

    wsClientRef.current.connect();

    return () => {
      if (audioServiceRef.current) audioServiceRef.current.stopCapture();
      if (wsClientRef.current) wsClientRef.current.disconnect();
    };
  }, []);

  // Sync config on change
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

  const handleStopStream = useCallback(() => {
    if (audioServiceRef.current) audioServiceRef.current.stopCapture();
    audioRouter.stopKeepAlive();
    setMediaStream(null);
    setIsTabShareActive(false);
    setIsMicActive(false);
    setIsCapturing(false);
    setAudioLevel(0);
    setStreamTitle('');
  }, []);

  const handleToggleTabShare = async () => {
    if (isTabShareActive) {
      handleStopStream();
      return;
    }
    try {
      audioRouter.startKeepAlive();
      const stream = await audioServiceRef.current.startTabCapture((chunk) => {
        if (wsClientRef.current) wsClientRef.current.sendAudioChunk(chunk);
      });
      setMediaStream(stream);
      setIsTabShareActive(true);
      setIsCapturing(true);
      const videoTrack = stream.getVideoTracks()[0];
      setStreamTitle(videoTrack ? videoTrack.label : 'Shared Tab');
      if (videoTrack) {
        videoTrack.onended = () => handleStopStream();
      }
    } catch (err) {
      if (err.name !== 'NotAllowedError') alert(err.message || 'Unable to capture tab audio.');
      setIsTabShareActive(false);
      setIsCapturing(false);
      audioRouter.stopKeepAlive();
    }
  };

  const handleToggleMic = async () => {
    if (isMicActive) {
      if (audioServiceRef.current) audioServiceRef.current.stopCapture();
      setIsMicActive(false);
      if (!isTabShareActive) {
        setIsCapturing(false);
        audioRouter.stopKeepAlive();
      }
      return;
    }
    try {
      audioRouter.startKeepAlive();
      await audioServiceRef.current.startMicCapture((chunk) => {
        if (wsClientRef.current) wsClientRef.current.sendAudioChunk(chunk);
      });
      setIsMicActive(true);
      setIsCapturing(true);
    } catch (err) {
      console.error('Mic error:', err);
      alert('Cannot access microphone. Please grant permission in browser.');
      setIsMicActive(false);
    }
  };

  const handleSendText = (text) => {
    if (wsClientRef.current) wsClientRef.current.sendTextInput(text);
  };

  return {
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
    handleSendText,
  };
}
