'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { PushToTalk } from '@/components/PushToTalk';
import { LatencyHUD } from '@/components/LatencyHUD';
import { RuntimeSelector } from '@/components/RuntimeSelector';
import { TranscriptDisplay } from '@/components/TranscriptDisplay';
import { MurmurWSClient } from '@/lib/ws-client';
import { AudioCapture } from '@/lib/audio-capture';
import { AudioPlayback } from '@/lib/audio-playback';

// Backend URL resolution:
//   1. NEXT_PUBLIC_BACKEND_URL  (exposed by next.config.js from REACT_APP_BACKEND_URL)
//   2. '' — same-origin relative URLs. The K8s ingress routes /api/* to the
//      backend and everything else to the frontend, so the WS path MUST be
//      /api/ws (which matches the FastAPI route `app.include_router(ws_router, prefix='/api')`).
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.REACT_APP_BACKEND_URL ||
  '';

// Build the WebSocket base URL. If BACKEND_URL is empty (same-origin), derive
// from window.location at runtime. Otherwise swap http(s) → ws(s) and append /api.
function buildWsBase(): string {
  if (BACKEND_URL) return BACKEND_URL.replace(/^http/, 'ws') + '/api';
  if (typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/api`;
  }
  return '/api';
}

export default function Demo() {
  const [status, setStatus] = useState('idle');
  const [runtime, setRuntime] = useState('sglang');
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const captureRef = useRef(null);
  const playbackRef = useRef(null);
  // Track the runtime the live socket is bound to so we don't tear down + rebuild
  // the WS on unrelated state changes (only when the user actually switches runtime).
  const boundRuntimeRef = useRef(null);

  const connectWS = useCallback((runtimeName: string) => {
    if (wsRef.current) wsRef.current.disconnect();

    const wsUrl = buildWsBase();
    const client = new MurmurWSClient(wsUrl);

    client.on('open', () => setWsConnected(true));
    client.on('close', () => setWsConnected(false));
    client.on('error', () => {
      setError('WebSocket connection failed');
      setWsConnected(false);
    });

    client.on('status', (msg) => {
      setStatus(msg.phase);
      if (msg.phase === 'error') setError(msg.detail);
    });

    client.on('transcript', (msg) => setTranscript(msg.text));
    client.on('token', (msg) => setResponse((prev) => prev + msg.text));

    client.on('metrics', (msg) => {
      setMetrics(msg);
      setMetricsHistory((prev) => [msg, ...prev].slice(0, 20));
    });

    client.on('audio', (pcm16Buffer) => {
      if (!playbackRef.current) playbackRef.current = new AudioPlayback(24000);
      playbackRef.current.queuePCM16(pcm16Buffer);
    });

    client.on('done', () => setStatus('idle'));

    client.connect(runtimeName);
    wsRef.current = client;
    boundRuntimeRef.current = runtimeName;
  }, []);

  // Connect on mount and whenever the user switches runtime. The boundRuntimeRef
  // guard prevents reconnect storms from unrelated re-renders.
  useEffect(() => {
    if (boundRuntimeRef.current !== runtime) {
      connectWS(runtime);
    }
    return () => {
      // Only fully tear down on unmount, not on every render.
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
        boundRuntimeRef.current = null;
      }
      if (playbackRef.current) {
        playbackRef.current.close();
        playbackRef.current = null;
      }
    };
  }, [runtime, connectWS]);

  const handlePressStart = async () => {
    setError(null);
    setTranscript('');
    setResponse('');
    if (playbackRef.current) playbackRef.current.stop();

    if (!wsRef.current?.connected) {
      setError('WebSocket not connected');
      return;
    }

    wsRef.current.sendAudioStart();

    captureRef.current = new AudioCapture((pcm16Buffer) => {
      wsRef.current.sendAudioFrame(pcm16Buffer);
    });

    try {
      await captureRef.current.start();
    } catch {
      setError('Microphone access denied. Please allow microphone access and try again.');
      setStatus('idle');
    }
  };

  const handlePressEnd = () => {
    if (captureRef.current) {
      captureRef.current.stop();
      captureRef.current = null;
    }
    if (wsRef.current) wsRef.current.sendAudioEnd();
  };

  const handleRuntimeChange = (newRuntime) => {
    setRuntime(newRuntime);
    setStatus('idle');
    setTranscript('');
    setResponse('');
    setMetrics(null);
    setError(null);
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
      <div className="grid grid-cols-12 gap-4 lg:gap-6">
        {/* Left: Controls + Transcript */}
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="flex items-center justify-center py-8">
            <PushToTalk
              status={status}
              onPressStart={handlePressStart}
              onPressEnd={handlePressEnd}
              disabled={!wsConnected}
            />
          </div>

          <TranscriptDisplay transcript={transcript} response={response} status={status} />

          {error && (
            <div
              className="text-sm text-destructive bg-destructive/10 rounded-md px-4 py-3 border border-destructive/20"
              data-testid="error-message"
            >
              {error}
            </div>
          )}
        </div>

        {/* Right: Runtime + HUD */}
        <div className="col-span-12 lg:col-span-5 space-y-4">
          <RuntimeSelector value={runtime} onChange={handleRuntimeChange} connected={wsConnected} />
          <LatencyHUD metrics={metrics} history={metricsHistory} status={status} />
        </div>
      </div>
    </div>
  );
}
