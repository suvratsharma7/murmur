/**
 * AudioWorklet Processor for real-time PCM16 audio capture.
 * 
 * Captures microphone audio at the browser's native sample rate,
 * downsamples to 16kHz mono, converts to PCM16, and sends to main thread.
 */

class PCM16CaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    this.sourceSampleRate = sampleRate; // Browser's native rate
    this.resampleRatio = this.sourceSampleRate / this.targetSampleRate;
    this.buffer = [];
    this.frameIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0]) {
      return true;
    }

    const inputChannel = input[0]; // Mono channel

    // Downsample to 16kHz
    const downsampled = this.downsample(inputChannel);

    // Convert Float32 to PCM16
    const pcm16 = this.floatToPCM16(downsampled);

    // Send to main thread
    this.port.postMessage({
      type: 'audio',
      data: pcm16.buffer,
    }, [pcm16.buffer]);

    return true;
  }

  downsample(buffer) {
    if (this.resampleRatio === 1) {
      return buffer;
    }

    const outputLength = Math.round(buffer.length / this.resampleRatio);
    const result = new Float32Array(outputLength);

    for (let i = 0; i < outputLength; i++) {
      const sourceIndex = Math.round(i * this.resampleRatio);
      result[i] = buffer[sourceIndex];
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
}

registerProcessor('pcm16-capture-processor', PCM16CaptureProcessor);
