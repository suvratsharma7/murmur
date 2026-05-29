'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Mic, Cpu, Volume2, ArrowRight, Gauge, BarChart3 } from 'lucide-react';

export default function Home() {
  const router = useRouter();

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20 space-y-16 md:space-y-24">
      {/* Hero */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* Left: Copy + CTAs */}
        <div className="space-y-6">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight">
            Real-time voice pipeline benchmarking
          </h1>
          <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
            Measure STT → LLM → TTS latency across vLLM, SGLang, and Ollama with a
            measurement-first design. Built for engineers who need debuggable, reproducible
            metrics.
          </p>
          <div className="flex flex-wrap gap-4 pt-4">
            <Button
              size="lg"
              onClick={() => router.push('/demo')}
              data-testid="cta-demo"
              className="gap-2"
            >
              Open Demo
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="secondary"
              onClick={() => router.push('/benchmarks')}
              data-testid="cta-benchmarks"
            >
              View Benchmarks
            </Button>
          </div>
        </div>

        {/* Right: Architecture Diagram */}
        <Card className="p-8">
          <CardContent className="p-0">
            <div className="flex items-center justify-between gap-6">
              {/* STT */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-lg bg-secondary border border-border flex items-center justify-center">
                  <Mic className="h-8 w-8 text-[hsl(var(--chart-1))]" />
                </div>
                <span className="text-xs font-mono text-muted-foreground">STT</span>
              </div>

              {/* Arrow */}
              <ArrowRight className="h-5 w-5 text-border" />

              {/* LLM */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-lg bg-secondary border border-border flex items-center justify-center">
                  <Cpu className="h-8 w-8 text-[hsl(var(--chart-2))]" />
                </div>
                <span className="text-xs font-mono text-muted-foreground">LLM</span>
              </div>

              {/* Arrow */}
              <ArrowRight className="h-5 w-5 text-border" />

              {/* TTS */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-lg bg-secondary border border-border flex items-center justify-center">
                  <Volume2 className="h-8 w-8 text-[hsl(var(--chart-3))]" />
                </div>
                <span className="text-xs font-mono text-muted-foreground">TTS</span>
              </div>
            </div>
            <p className="text-xs text-center text-muted-foreground mt-8">
              Push-to-talk → streaming orchestration → audio playback
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Feature Strip */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Gauge className="h-8 w-8 text-[hsl(var(--chart-1))]" />
            <h3 className="text-lg font-medium">Real-time Pipeline</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              WebSocket-based push-to-talk with streaming STT, token-by-token LLM responses, and
              chunked TTS audio playback.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 space-y-3">
            <BarChart3 className="h-8 w-8 text-[hsl(var(--chart-2))]" />
            <h3 className="text-lg font-medium">Latency HUD</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Live metrics dashboard showing STT, TTFT, TTFB-audio, E2E latency, and throughput
              with threshold indicators.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 space-y-3">
            <Cpu className="h-8 w-8 text-[hsl(var(--chart-3))]" />
            <h3 className="text-lg font-medium">Benchmark Viewer</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Compare vLLM, SGLang, and Ollama across concurrency levels with reproducible JSON
              results and charts.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* How It Works */}
      <section className="space-y-6">
        <h2 className="text-3xl font-semibold tracking-tight">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wide text-muted-foreground">
              Step 1
            </span>
            <p className="text-sm leading-relaxed">
              Hold the push-to-talk button and speak. Audio is captured at 16kHz PCM16 and
              streamed over WebSocket to the orchestrator.
            </p>
          </div>
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wide text-muted-foreground">
              Step 2
            </span>
            <p className="text-sm leading-relaxed">
              The orchestrator sends audio to Whisper STT, streams the transcript to your chosen
              LLM runtime (vLLM/SGLang/Ollama), and chunks responses by sentence boundaries.
            </p>
          </div>
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wide text-muted-foreground">
              Step 3
            </span>
            <p className="text-sm leading-relaxed">
              TTS synthesis begins on the first sentence (or 20-token fallback), minimizing
              TTFB-audio. Audio chunks are queued and played smoothly.
            </p>
          </div>
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wide text-muted-foreground">
              Step 4
            </span>
            <p className="text-sm leading-relaxed">
              All per-turn metrics (STT latency, TTFT, TTFB-audio, E2E, tokens/sec) are persisted
              to MongoDB and displayed live in the Latency HUD.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 pt-8 pb-4 text-center">
        <p className="text-xs text-muted-foreground">
          Built with FastAPI, React, and WebSockets. Designed for engineers who measure.
        </p>
      </footer>
    </div>
  );
}
