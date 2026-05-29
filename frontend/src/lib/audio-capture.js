/**
 * AudioWorklet-based microphone audio capture — PCM16 mono at 16 kHz.
 * 
 * Uses AudioWorklet for real-time processing (per brief requirement).
 * Falls back to ScriptProcessorNode if AudioWorklet is unavailable.
 */

export class AudioCapture {
  constructor(onAudioChunk) {
    this.onAudioChunk = onAudioChunk;
    this.audioCtx = null;
    this.stream = null;
    this.workletNode = null;
    this.source = null;
    this.useWorklet = true;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });

    this.audioCtx = new AudioContext();
    this.source = this.audioCtx.createMediaStreamSource(this.stream);

    // Try AudioWorklet first (required by brief)
    try {
      await this.audioCtx.audioWorklet.addModule('/audio-worklet-processor.js');
      
      this.workletNode = new AudioWorkletNode(this.audioCtx, 'pcm16-capture-processor');
      
      this.workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audio') {
          this.onAudioChunk(event.data.data);
        }
      };

      this.source.connect(this.workletNode);
      this.workletNode.connect(this.audioCtx.destination);
      
      console.log('✓ AudioWorklet capture initialized at 16kHz PCM16');
    } catch (err) {
      // Fallback to ScriptProcessorNode if AudioWorklet fails
      console.warn('AudioWorklet unavailable, falling back to ScriptProcessorNode:', err);
      this.useWorklet = false;
      this.initScriptProcessor();
    }
  }

  initScriptProcessor() {
    const processor = this.audioCtx.createScriptProcessor(4096, 1, 1);
    
    processor.onaudioprocess = (event) => {
      const float32 = event.inputBuffer.getChannelData(0);
      const targetRate = 16000;
      const currentRate = this.audioCtx.sampleRate;

      const downsampled = this.downsample(float32, currentRate, targetRate);
      const pcm16 = this.floatToPCM16(downsampled);
      this.onAudioChunk(pcm16.buffer);
    };

    this.source.connect(processor);
    processor.connect(this.audioCtx.destination);
    this.workletNode = processor; // Store for cleanup
    
    console.log('⚠ ScriptProcessorNode fallback active');
  }

  downsample(buffer, inputRate, outputRate) {
    if (inputRate === outputRate) return buffer;
    const ratio = inputRate / outputRate;
    const outputLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(outputLength);
    for (let i = 0; i < outputLength; i++) {
      result[i] = buffer[Math.round(i * ratio)];
    }
    return result;
  }

  floatToPCM16(float32) {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
  }

  stop() {
    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    if (this.audioCtx) {
      this.audioCtx.close().catch(() => {});
      this.audioCtx = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
  }
}
