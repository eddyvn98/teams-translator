/**
 * Audio capture service for capturing Tab Audio / Screen Audio and Microphone
 * Downsamples audio to 16kHz 16-bit PCM for low-latency ASR
 */

export class AudioCaptureService {
  constructor(onAudioLevel = null) {
    this.onAudioLevel = onAudioLevel;
    this.audioContext = null;
    this.mediaStream = null;
    this.micStream = null;
    this.processorNode = null;
    this.sourceNode = null;
    this.analyserNode = null;
    this.isCapturing = false;
    this.animationFrameId = null;
  }

  /**
   * Request display media (Tab or Screen) with audio
   * Triggers the Chrome dialog shown in Image 1
   */
  async startTabCapture(onPcmChunk) {
    try {
      this.mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: 'browser',
          frameRate: 15,
        },
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      const audioTracks = this.mediaStream.getAudioTracks();
      if (!audioTracks || audioTracks.length === 0) {
        throw new Error('Vui lòng tích chọn "Chia sẻ kèm âm thanh của thẻ" trong hộp thoại!');
      }

      await this._setupAudioPipeline(this.mediaStream, onPcmChunk);
      this.isCapturing = true;
      return this.mediaStream;
    } catch (err) {
      console.error('Lỗi bắt âm thanh tab:', err);
      throw err;
    }
  }

  /**
   * Request user microphone
   */
  async startMicCapture(onPcmChunk) {
    try {
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });

      await this._setupAudioPipeline(this.micStream, onPcmChunk);
      this.isCapturing = true;
      return this.micStream;
    } catch (err) {
      console.error('Lỗi mở micro:', err);
      throw err;
    }
  }

  async _setupAudioPipeline(stream, onPcmChunk) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass({ sampleRate: 48000 });
    const targetSampleRate = 16000;

    this.sourceNode = this.audioContext.createMediaStreamSource(stream);

    // Analyser for audio visualizer
    this.analyserNode = this.audioContext.createAnalyser();
    this.analyserNode.fftSize = 64;
    this.sourceNode.connect(this.analyserNode);

    // Visualizer loop
    const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
    const updateLevel = () => {
      if (!this.isCapturing) return;
      this.analyserNode.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const avg = sum / dataArray.length / 255.0;
      if (this.onAudioLevel) {
        this.onAudioLevel(avg);
      }
      this.animationFrameId = requestAnimationFrame(updateLevel);
    };
    updateLevel();

    // Script processor to convert to 16kHz 16-bit PCM
    const bufferSize = 4096;
    this.processorNode = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

    this.processorNode.onaudioprocess = (e) => {
      if (!this.isCapturing) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const resampledData = this._downsampleBuffer(
        inputData,
        this.audioContext.sampleRate,
        targetSampleRate
      );
      const pcm16 = this._floatTo16BitPCM(resampledData);
      if (onPcmChunk) {
        onPcmChunk(pcm16.buffer);
      }
    };

    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(this.audioContext.destination);

    // Listen for tab share end (e.g. user clicks Chrome "Stop sharing" button)
    stream.getVideoTracks().forEach((track) => {
      track.onended = () => {
        this.stopCapture();
      };
    });
  }

  _downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
      return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  _floatTo16BitPCM(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16Array;
  }

  stopCapture() {
    this.isCapturing = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }
    if (this.analyserNode) {
      this.analyserNode.disconnect();
      this.analyserNode = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    if (this.micStream) {
      this.micStream.getTracks().forEach((track) => track.stop());
      this.micStream = null;
    }
    if (this.onAudioLevel) {
      this.onAudioLevel(0);
    }
  }
}
