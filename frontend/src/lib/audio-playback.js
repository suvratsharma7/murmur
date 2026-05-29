/**
 * Audio playback queue for TTS audio.
 * 
 * Queues PCM16 chunks and plays them sequentially using AudioContext.
 * Handles smooth concatenation of audio chunks without gaps or clicks.
 */

export class AudioPlayback {
  constructor(sampleRate = 24000) {
    this.sampleRate = sampleRate;
    this.audioCtx = null;
    this.queue = [];
    this.playing = false;
    this.nextStartTime = 0;
  }

  queuePCM16(arrayBuffer) {
    if (!this.audioCtx) {
      this.audioCtx = new AudioContext({ sampleRate: this.sampleRate });
      this.nextStartTime = this.audioCtx.currentTime;
    }

    // Convert PCM16 (Int16Array) to Float32Array
    const pcm16 = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
      float32[i] = pcm16[i] / (pcm16[i] < 0 ? 0x8000 : 0x7fff);
    }

    // Create AudioBuffer
    const audioBuffer = this.audioCtx.createBuffer(1, float32.length, this.sampleRate);
    audioBuffer.getChannelData(0).set(float32);

    // Schedule playback
    const source = this.audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioCtx.destination);

    const startTime = Math.max(this.nextStartTime, this.audioCtx.currentTime);
    source.start(startTime);
    this.nextStartTime = startTime + audioBuffer.duration;

    this.queue.push(source);
    this.playing = true;

    // Clean up after playback
    source.onended = () => {
      const idx = this.queue.indexOf(source);
      if (idx > -1) this.queue.splice(idx, 1);
      if (this.queue.length === 0) this.playing = false;
    };
  }

  stop() {
    this.queue.forEach((source) => {
      try {
        source.stop();
      } catch (e) {
        // Ignore if already stopped
      }
    });
    this.queue = [];
    this.playing = false;
    if (this.audioCtx) {
      this.nextStartTime = this.audioCtx.currentTime;
    }
  }

  close() {
    this.stop();
    if (this.audioCtx) {
      this.audioCtx.close().catch(() => {});
      this.audioCtx = null;
    }
  }
}
