/**
 * AudioRouter Service for Browser-Based Dual Output Audio Routing (Cách 1)
 * Routes audio streams to Teams Virtual Mic (BlackHole / CABLE) and Local Monitor Speaker/Headset
 * using HTMLMediaElement.setSinkId(), Web Audio API, and Anti-Throttling Keep-Alive.
 */

class AudioRouter {
  constructor() {
    this.audioOutputs = [];
    this.virtualDeviceId = localStorage.getItem('teams_virtual_device_id') || '';
    this.monitorDeviceId = localStorage.getItem('teams_monitor_device_id') || '';
    this.isKeepAliveActive = false;
    this.keepAliveCtx = null;
    this.wakeLock = null;
    this.isLeader = true;
    this.channel = null;
    this.tabId = Math.random().toString(36).substring(2, 9);
    this.listeners = new Set();

    this._initChannel();
  }

  _initChannel() {
    if (typeof BroadcastChannel !== 'undefined') {
      try {
        this.channel = new BroadcastChannel('teams_translator_audio_leader');
        this.channel.onmessage = (event) => {
          const data = event.data;
          if (data.type === 'CLAIM_LEADER') {
            if (data.tabId !== this.tabId) {
              // Another tab claimed leadership
              this.isLeader = false;
            }
          } else if (data.type === 'WHO_IS_LEADER') {
            if (this.isLeader) {
              this.channel.postMessage({ type: 'I_AM_LEADER', tabId: this.tabId });
            }
          } else if (data.type === 'I_AM_LEADER') {
            if (data.tabId !== this.tabId) {
              this.isLeader = false;
            }
          } else if (data.type === 'LEADER_EXIT') {
            // Former leader tab exited; re-elect a new leader with random jitter
            this.isLeader = true;
            const jitter = Math.floor(Math.random() * 200);
            setTimeout(() => {
              if (this.isLeader && this.channel) {
                this.channel.postMessage({ type: 'CLAIM_LEADER', tabId: this.tabId });
              }
            }, jitter);
          }
        };

        // Query if there is an existing leader
        this.channel.postMessage({ type: 'WHO_IS_LEADER', tabId: this.tabId });
        setTimeout(() => {
          if (this.isLeader) {
            this.channel.postMessage({ type: 'CLAIM_LEADER', tabId: this.tabId });
          }
        }, 250);

        window.addEventListener('beforeunload', () => {
          if (this.isLeader && this.channel) {
            this.channel.postMessage({ type: 'LEADER_EXIT', tabId: this.tabId });
          }
        });
      } catch (e) {
        console.warn('[AudioRouter] BroadcastChannel not supported:', e);
      }
    }
  }

  async init() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      return;
    }

    navigator.mediaDevices.addEventListener('devicechange', () => {
      this.refreshDevices();
    });

    await this.refreshDevices();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  _notify() {
    for (const listener of this.listeners) {
      try {
        listener({
          audioOutputs: this.audioOutputs,
          virtualDeviceId: this.virtualDeviceId,
          monitorDeviceId: this.monitorDeviceId,
          isSupported: this.isSetSinkIdSupported(),
        });
      } catch (e) {
        console.error('[AudioRouter] Listener error:', e);
      }
    }
  }

  isSetSinkIdSupported() {
    return typeof HTMLMediaElement !== 'undefined' && 'setSinkId' in HTMLMediaElement.prototype;
  }

  async refreshDevices() {
    try {
      if (!navigator.mediaDevices?.enumerateDevices) return [];
      const devices = await navigator.mediaDevices.enumerateDevices();
      const outputs = devices.filter((d) => d.kind === 'audiooutput');

      this.audioOutputs = outputs;

      // Auto-detect if not explicitly selected or current selection missing
      const virtualKeywords = ['blackhole', 'cable input', 'vb-audio', 'virtual', 'soundflower', 'loopback'];
      const monitorKeywords = ['loa', 'macbook', 'speaker', 'headphone', 'headset', 'airpod', 'earphone'];

      const hasVirtual = outputs.some((d) => d.deviceId === this.virtualDeviceId);
      if (!this.virtualDeviceId || !hasVirtual) {
        const foundVirtual = outputs.find((d) =>
          virtualKeywords.some((kw) => (d.label || '').toLowerCase().includes(kw))
        );
        if (foundVirtual) {
          this.virtualDeviceId = foundVirtual.deviceId;
          localStorage.setItem('teams_virtual_device_id', this.virtualDeviceId);
        }
      }

      const hasMonitor = outputs.some((d) => d.deviceId === this.monitorDeviceId);
      if (!this.monitorDeviceId || !hasMonitor) {
        const foundMonitor = outputs.find((d) =>
          monitorKeywords.some((kw) => (d.label || '').toLowerCase().includes(kw))
        );
        if (foundMonitor) {
          this.monitorDeviceId = foundMonitor.deviceId;
          localStorage.setItem('teams_monitor_device_id', this.monitorDeviceId);
        } else if (outputs.length > 0) {
          this.monitorDeviceId = outputs[0].deviceId;
        }
      }

      this._notify();
      return outputs;
    } catch (err) {
      console.warn('[AudioRouter] Error enumerating devices:', err);
      return [];
    }
  }

  setVirtualDevice(deviceId) {
    this.virtualDeviceId = deviceId;
    localStorage.setItem('teams_virtual_device_id', deviceId);
    this._notify();
  }

  setMonitorDevice(deviceId) {
    this.monitorDeviceId = deviceId;
    localStorage.setItem('teams_monitor_device_id', deviceId);
    this._notify();
  }

  /**
   * Keep-Alive to prevent Chrome/Edge from throttling or freezing the tab in background
   */
  async startKeepAlive() {
    if (this.isKeepAliveActive) return;
    this.isKeepAliveActive = true;

    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.keepAliveCtx = new AudioContextClass();
        if (this.keepAliveCtx.state === 'suspended') {
          await this.keepAliveCtx.resume();
        }
        // Create an inaudible continuous oscillator (gain 0.00001)
        const osc = this.keepAliveCtx.createOscillator();
        const gain = this.keepAliveCtx.createGain();
        gain.gain.value = 0.00001; // virtually silent
        osc.connect(gain);
        gain.connect(this.keepAliveCtx.destination);
        osc.start();
      }

      // Request Screen Wake Lock if available
      if ('wakeLock' in navigator) {
        try {
          this.wakeLock = await navigator.wakeLock.request('screen');
        } catch {}
      }
    } catch (e) {
      console.debug('[AudioRouter] Keep-alive setup notice:', e);
    }
  }

  stopKeepAlive() {
    this.isKeepAliveActive = false;
    if (this.keepAliveCtx) {
      try {
        this.keepAliveCtx.close();
      } catch {}
      this.keepAliveCtx = null;
    }
    if (this.wakeLock) {
      try {
        this.wakeLock.release();
      } catch {}
      this.wakeLock = null;
    }
  }

  /**
   * Dual Output Playback:
   * Plays incoming audio concurrently to Virtual Mic (for Teams) and Monitor (for User)
   */
  async playDualAudio(audioBase64) {
    if (!audioBase64) return;
    if (!this.isLeader) {
      console.log('[AudioRouter] Another tab is the active audio leader. Skipping playback to prevent echo.');
      return;
    }

    try {
      // Decode Base64 to ArrayBuffer Blob
      const byteCharacters = atob(audioBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);

      const canSetSinkId = this.isSetSinkIdSupported();

      // Stream 1: To Teams (Virtual Cable / BlackHole)
      const playTeams = async () => {
        const audio = new Audio(audioUrl);
        if (canSetSinkId && this.virtualDeviceId) {
          try {
            await audio.setSinkId(this.virtualDeviceId);
          } catch (e) {
            console.warn('[AudioRouter] setSinkId for virtual output failed:', e);
          }
        }
        await audio.play();
      };

      // Stream 2: To User Monitor (Speakers / Headset)
      const playMonitor = async () => {
        // If monitor is different from virtual, play monitor stream
        if (this.monitorDeviceId && this.monitorDeviceId !== this.virtualDeviceId) {
          const audio = new Audio(audioUrl);
          if (canSetSinkId && this.monitorDeviceId && this.monitorDeviceId !== 'default') {
            try {
              await audio.setSinkId(this.monitorDeviceId);
            } catch (e) {
              console.warn('[AudioRouter] setSinkId for monitor output failed:', e);
            }
          }
          await audio.play();
        }
      };

      await Promise.allSettled([playTeams(), playMonitor()]);

      // Clean up object URL after playback finishes
      setTimeout(() => {
        URL.revokeObjectURL(audioUrl);
      }, 30000);
    } catch (err) {
      console.error('[AudioRouter] playDualAudio failed:', err);
    }
  }

  /**
   * Test tone playback to verify both audio channels
   */
  async testPlayback() {
    // Generate a simple pleasant 440Hz test WAV sound
    const sampleRate = 24000;
    const duration = 0.6; // 600ms
    const numSamples = sampleRate * duration;
    const wavBuffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(wavBuffer);

    // Write WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, numSamples * 2, true);

    // Sine wave
    for (let i = 0; i < numSamples; i++) {
      const t = i / sampleRate;
      const sample = Math.sin(2 * Math.PI * 587.33 * t) * 0.4 * Math.exp(-3 * t); // D5 chime
      view.setInt16(44 + i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    }

    const base64 = btoa(
      new Uint8Array(wavBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    );

    await this.playDualAudio(base64);
  }
}

export const audioRouter = new AudioRouter();
