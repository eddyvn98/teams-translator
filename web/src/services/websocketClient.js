/**
 * WebSocket client for real-time bidirectional communication with FastAPI backend
 */

export class StreamWebSocketClient {
  constructor({ onTranscript, onTranslation, onSentence, onStatus, onError }) {
    this.onTranscript = onTranscript;
    this.onTranslation = onTranslation;
    this.onSentence = onSentence;
    this.onStatus = onStatus;
    this.onError = onError;
    this.ws = null;
    this.isConnected = false;
    this.url = null;
  }

  connect(customUrl = null) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (customUrl) {
      this.url = customUrl;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      // If running on Vite dev (5173), point to 8000
      const port = window.location.port === '5173' ? '8000' : (window.location.port || '8000');
      this.url = `${protocol}//${host}:${port}/ws/stream`;
    }

    try {
      this.ws = new WebSocket(this.url);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        this.isConnected = true;
        if (this.onStatus) this.onStatus('connected');
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        if (this.onStatus) this.onStatus('disconnected');
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        if (this.onError) this.onError(err);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'sentence' && this.onSentence) {
            this.onSentence(data);
          } else if (data.type === 'transcript' && this.onTranscript) {
            this.onTranscript(data);
          } else if (data.type === 'translation' && this.onTranslation) {
            this.onTranslation(data);
          } else if (data.type === 'status' && this.onStatus) {
            this.onStatus(data.message);
          } else if (data.type === 'error' && this.onError) {
            this.onError(data.message);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };
    } catch (err) {
      console.error('Failed to initialize WebSocket:', err);
      if (this.onError) this.onError(err);
    }
  }

  sendConfig({ sourceLang, targetLang, echo, systemInstruction }) {
    if (this.isConnected && this.ws) {
      this.ws.send(
        JSON.stringify({
          type: 'config',
          source_lang: sourceLang,
          target_lang: targetLang,
          echo,
          system_instruction: systemInstruction,
        })
      );
    }
  }

  sendAudioChunk(pcmArrayBuffer) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(pcmArrayBuffer);
    }
  }

  sendTextInput(text) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: 'text_input',
          text,
        })
      );
    }
  }

  disconnect() {
    if (this.ws) {
      try {
        this.ws.close();
      } catch (e) {
        // ignore
      }
      this.ws = null;
      this.isConnected = false;
    }
  }
}
