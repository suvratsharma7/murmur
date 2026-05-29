/**
 * WebSocket client for the Murmur orchestrator.
 *
 * Handles connection lifecycle, message parsing (text JSON + binary audio),
 * and provides an event-emitter interface for the Demo page.
 *
 * Runtime is REQUIRED on connect() — no silent fallback. If the caller forgets
 * to pass a runtime, the client throws so the bug is visible at the call site.
 */

export class MurmurWSClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.ws = null;
    this.listeners = {};
  }

  connect(runtime) {
    if (!runtime) {
      throw new Error(
        'MurmurWSClient.connect(runtime) requires an explicit runtime name (e.g. "sglang", "vllm", "ollama", "mock")'
      );
    }

    if (this.ws) this.disconnect();

    const url = `${this.baseUrl}/ws?runtime=${encodeURIComponent(runtime)}`;
    this.ws = new WebSocket(url);
    this.ws.binaryType = 'arraybuffer';

    this.ws.onopen = () => this._emit('open');
    this.ws.onclose = () => this._emit('close');
    this.ws.onerror = (e) => this._emit('error', e);

    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const view = new Uint8Array(event.data);
        if (view.length > 1 && view[0] === 0x01) {
          this._emit('audio', event.data.slice(1));
        }
      } else {
        try {
          const msg = JSON.parse(event.data);
          this._emit(msg.type, msg);
        } catch (_) {
          // Ignore malformed messages
        }
      }
    };
  }

  sendAudioStart() {
    this._send({ type: 'audio_start', sample_rate: 16000, encoding: 'pcm16' });
  }

  sendAudioFrame(pcm16ArrayBuffer) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(pcm16ArrayBuffer);
    }
  }

  sendAudioEnd() {
    this._send({ type: 'audio_end' });
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
    return () => {
      this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners = {};
  }

  get connected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  _send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }

  _emit(event, data) {
    (this.listeners[event] || []).forEach((cb) => cb(data));
  }
}
