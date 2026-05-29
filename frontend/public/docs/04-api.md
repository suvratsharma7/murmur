# API Reference

MURMUR exposes both REST and WebSocket APIs for voice pipeline orchestration and metrics access.

## Base URL

```
Development: http://localhost:8001
Production: https://api.yourdomain.com
```

## REST API

### Health Check

**GET** `/api/healthz`

Check orchestrator and upstream service health.

**Response:**
```json
{
  "status": "healthy",
  "runtime": "mock",
  "services": {
    "stt": "healthy",
    "tts": "healthy",
    "llm": "healthy"
  },
  "timestamp": "2026-05-27T20:00:00Z"
}
```

**Status Codes:**
- `200 OK` - All services healthy
- `503 Service Unavailable` - One or more services unhealthy

---

### List Runtimes

**GET** `/api/runtimes`

Get available LLM runtimes and their health status.

**Response:**
```json
{
  "runtimes": [
    {"name": "mock", "healthy": true},
    {"name": "vllm", "healthy": true},
    {"name": "sglang", "healthy": false},
    {"name": "ollama", "healthy": true}
  ]
}
```

---

### Get Recent Turns

**GET** `/api/turns?limit=20`

Retrieve recent voice pipeline turns with metrics.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Maximum number of turns to return |

**Response:**
```json
{
  "turns": [
    {
      "turn_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-05-27T20:00:00Z",
      "runtime": "mock",
      "model": "default",
      "transcript_chars": 42,
      "response_tokens": 17,
      "stt_latency_ms": 150.2,
      "ttft_ms": 85.1,
      "first_chunk_size_tokens": 8,
      "ttfb_audio_ms": 195.4,
      "tpot_mean_ms": 28.5,
      "e2e_ms": 621.3,
      "output_tokens_per_second": 27.4,
      "error": null
    }
  ]
}
```

---

### Get Benchmark Results

**GET** `/api/benchmarks?runtime=mock`

Retrieve aggregated benchmark metrics.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `runtime` | string | No | Filter by runtime (mock, vllm, sglang, ollama) |

**Response:**
```json
{
  "benchmarks": [
    {
      "runtime": "mock",
      "concurrency": 1,
      "ttft_ms": 100.2,
      "e2e_ms": 621.1,
      "tpot_ms": 32.5,
      "output_tokens_per_second": 27.4,
      "tokens_emitted": 17,
      "stt_latency_ms": 150.0,
      "ttfb_audio_ms": 195.0,
      "timestamp": "2026-05-27T20:00:00Z"
    }
  ]
}
```

---

## WebSocket API

### Connect

**WS** `/api/ws/stream?runtime=mock`

Establish WebSocket connection for push-to-talk session.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `runtime` | string | No | `mock` | LLM runtime to use |

**Connection Flow:**
```
1. Client connects to ws://localhost:8001/api/ws/stream?runtime=mock
2. Server sends: {"type": "ready", "runtime": "mock"}
3. Client sends: {"type": "audio_start"}
4. Client sends: binary audio frames (PCM16, 16kHz, mono)
5. Client sends: {"type": "audio_end"}
6. Server processes and sends events
7. Client receives: transcript, tokens, audio, metrics
8. Server sends: {"type": "done"}
```

### Message Types

#### Client → Server

**audio_start**
```json
{"type": "audio_start"}
```
Signals start of audio capture session.

**audio_frame**
```
Binary data: PCM16 audio (Int16Array)
```
Audio chunk from microphone. Should be 16kHz mono PCM16.

**audio_end**
```json
{"type": "audio_end"}
```
Signals end of audio capture.

---

#### Server → Client

**ready**
```json
{
  "type": "ready",
  "runtime": "mock",
  "model": "default"
}
```
Connection established, ready for audio.

**status**
```json
{
  "type": "status",
  "phase": "listening",
  "detail": "Capturing audio..."
}
```

**Phases:**
- `idle` - Waiting for audio_start
- `listening` - Receiving audio
- `thinking` - Processing STT and LLM
- `speaking` - Streaming TTS audio
- `done` - Turn complete
- `error` - Error occurred

**transcript**
```json
{
  "type": "transcript",
  "text": "What is the capital of France?",
  "confidence": 0.98
}
```
STT transcription result.

**token**
```json
{
  "type": "token",
  "text": "The ",
  "index": 0
}
```
Single LLM token streamed.

**audio**
```
Binary data: PCM16 audio (Int16Array, 24kHz)
```
TTS audio chunk for playback.

**metrics**
```json
{
  "type": "metrics",
  "turn_id": "550e8400-e29b-41d4-a716-446655440000",
  "stt_latency_ms": 150.2,
  "ttft_ms": 85.1,
  "ttfb_audio_ms": 195.4,
  "e2e_ms": 621.3,
  "tokens_emitted": 17,
  "output_tokens_per_second": 27.4,
  "tpot_mean_ms": 28.5
}
```
Per-turn performance metrics.

**done**
```json
{
  "type": "done",
  "turn_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
Turn processing complete.

**error**
```json
{
  "type": "error",
  "code": "STT_TIMEOUT",
  "message": "Speech-to-text service timeout",
  "recoverable": true
}
```

**Error Codes:**
- `STT_ERROR` - Speech-to-text failure
- `LLM_ERROR` - Language model failure
- `TTS_ERROR` - Text-to-speech failure
- `RUNTIME_ERROR` - Runtime adapter error
- `INVALID_AUDIO` - Audio format/quality issue

---

## WebSocket Example (JavaScript)

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8001/api/ws/stream?runtime=mock');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = async (event) => {
  if (event.data instanceof Blob) {
    // Binary audio frame
    const arrayBuffer = await event.data.arrayBuffer();
    playAudio(arrayBuffer);  // Play PCM16 audio
  } else {
    // JSON message
    const msg = JSON.parse(event.data);
    
    switch (msg.type) {
      case 'ready':
        console.log('Ready to receive audio');
        break;
      case 'status':
        console.log('Phase:', msg.phase);
        break;
      case 'transcript':
        console.log('User said:', msg.text);
        break;
      case 'token':
        console.log('AI token:', msg.text);
        break;
      case 'metrics':
        console.log('Metrics:', msg);
        break;
      case 'done':
        console.log('Turn complete');
        break;
      case 'error':
        console.error('Error:', msg.message);
        break;
    }
  }
};

// Start recording
ws.send(JSON.stringify({type: 'audio_start'}));

// Send audio frames
// (Use AudioWorklet to capture PCM16 @ 16kHz)
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => {
    const audioContext = new AudioContext({sampleRate: 16000});
    const source = audioContext.createMediaStreamSource(stream);
    // ... setup AudioWorklet processor
    // ... send chunks via ws.send(pcm16Buffer)
  });

// End recording
ws.send(JSON.stringify({type: 'audio_end'}));
```

## Audio Format Specifications

### Client → Server (Microphone Input)

- **Format:** PCM16 (Int16Array)
- **Sample Rate:** 16kHz
- **Channels:** Mono (1)
- **Bit Depth:** 16-bit signed integer
- **Byte Order:** Little-endian
- **Frame Size:** Variable (typically 4096 samples = 256ms)

### Server → Client (TTS Output)

- **Format:** PCM16 (Int16Array)
- **Sample Rate:** 24kHz
- **Channels:** Mono (1)
- **Bit Depth:** 16-bit signed integer
- **Byte Order:** Little-endian
- **Frame Size:** Variable (typically 2400 samples = 100ms)

## Rate Limits

Currently no rate limits enforced. For production deployment, consider:

- Max concurrent WebSocket connections per IP
- Max audio duration per turn (e.g., 30 seconds)
- Max turns per minute per user

## Authentication

MURMUR does not include built-in authentication. For production:

1. Deploy behind reverse proxy (nginx/Caddy)
2. Add JWT validation middleware
3. Use API gateway for rate limiting and auth

Example nginx config:
```nginx
location /api/ {
    auth_request /auth;
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Monitoring

### Prometheus Metrics (Future)

```
# HELP murmur_turns_total Total voice turns processed
# TYPE murmur_turns_total counter
murmur_turns_total{runtime="mock",status="success"} 142

# HELP murmur_stt_latency_seconds STT latency distribution
# TYPE murmur_stt_latency_seconds histogram
murmur_stt_latency_seconds_bucket{le="0.1"} 0
murmur_stt_latency_seconds_bucket{le="0.2"} 128
murmur_stt_latency_seconds_bucket{le="0.5"} 142
```

---

**Previous:** [← Setup Guide](02-setup.md) | **Next:** [Runbook →](05-runbook.md)
