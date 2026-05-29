import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const MetricRow = ({ label, value, unit, testId, thresholds }) => {
  let badgeLabel = null;
  if (value != null && thresholds) {
    if (thresholds.lower) {
      badgeLabel = value >= thresholds.ok ? 'OK' : value >= thresholds.warn ? 'WARN' : 'LOW';
    } else {
      badgeLabel = value < thresholds.ok ? 'OK' : value < thresholds.warn ? 'WARN' : 'HIGH';
    }
  }

  return (
    <div className="flex items-baseline justify-between gap-3 py-2.5 border-b border-border/40 last:border-0">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-mono tabular-nums" data-testid={testId}>
          {value != null ? (Number.isInteger(value) ? value : value.toFixed(1)) : '—'}
        </span>
        {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
        {badgeLabel && (
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 font-mono">
            {badgeLabel}
          </Badge>
        )}
      </div>
    </div>
  );
};

export const LatencyHUD = ({ metrics, history, status }) => {
  const dot =
    status === 'listening'
      ? 'bg-[hsl(160,18%,52%)]'
      : status === 'thinking'
        ? 'bg-[hsl(35,22%,58%)]'
        : status === 'speaking'
          ? 'bg-[hsl(210,22%,62%)]'
          : status === 'error'
            ? 'bg-destructive'
            : 'bg-muted-foreground';

  return (
    <Card data-testid="latency-hud-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-sans flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${dot}`} />
          Latency HUD
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0">
        <MetricRow label="STT" value={metrics?.stt_latency_ms} unit="ms" testId="latency-hud-stt-ms" thresholds={{ ok: 300, warn: 500 }} />
        <MetricRow label="TTFT" value={metrics?.ttft_ms} unit="ms" testId="latency-hud-ttft-ms" thresholds={{ ok: 200, warn: 400 }} />
        <MetricRow label="TTFB Audio" value={metrics?.ttfb_audio_ms} unit="ms" testId="latency-hud-ttfb-audio-ms" thresholds={{ ok: 800, warn: 1500 }} />
        <MetricRow label="E2E" value={metrics?.e2e_ms} unit="ms" testId="latency-hud-e2e-ms" thresholds={{ ok: 2000, warn: 4000 }} />
        <MetricRow label="Throughput" value={metrics?.output_tokens_per_second} unit="tok/s" testId="latency-hud-tps" thresholds={{ ok: 20, warn: 10, lower: true }} />
        <MetricRow label="Tokens" value={metrics?.tokens_emitted} unit="" testId="latency-hud-tokens" />

        {history && history.length > 1 && (
          <div className="mt-4 pt-3 border-t border-border/40">
            <span className="text-xs uppercase tracking-wide text-muted-foreground">Recent Turns</span>
            <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
              {history.slice(0, 5).map((h, i) => (
                <div key={i} className="flex justify-between text-xs font-mono tabular-nums text-muted-foreground">
                  <span>E2E {h.e2e_ms?.toFixed(0)}ms</span>
                  <span>TTFB {h.ttfb_audio_ms?.toFixed(0)}ms</span>
                  <span>{h.tokens_emitted} tok</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
