import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from './ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

// Backend URL resolution order:
//   1. NEXT_PUBLIC_BACKEND_URL  (exposed by next.config.js from REACT_APP_BACKEND_URL)
//   2. Same-origin '' (relative URLs) — works because K8s ingress routes /api/* to backend
// We never fall back to localhost:8001 in production builds; relative URLs are safer.
const API =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.REACT_APP_BACKEND_URL ||
  '';

export const RuntimeSelector = ({ value, onChange, connected }) => {
  // Seed with the current value so the dropdown is never empty even before the
  // first fetch resolves. Items are merged with the fetched health-checked list
  // once it arrives — no more "only mock visible" race window.
  const [runtimes, setRuntimes] = useState(() => [{ name: value, healthy: true }]);
  const lastValueRef = useRef(value);

  // Keep the seed item in sync if the parent changes `value` before the first
  // fetch completes (e.g. user switches before health-check returns).
  useEffect(() => {
    if (lastValueRef.current === value) return;
    lastValueRef.current = value;
    setRuntimes((prev) =>
      prev.some((r) => r.name === value) ? prev : [...prev, { name: value, healthy: true }]
    );
  }, [value]);

  useEffect(() => {
    let mounted = true;
    const ctrl = new AbortController();

    const fetchRuntimes = async () => {
      try {
        const res = await fetch(`${API}/api/runtimes`, { signal: ctrl.signal });
        if (!mounted) return;
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!mounted) return;
        if (Array.isArray(data.runtimes) && data.runtimes.length > 0) {
          setRuntimes(data.runtimes);
        }
      } catch (err) {
        // Three abort flavors we deliberately ignore:
        //   1) Our AbortController (cleanup)        → err.name === 'AbortError'
        //   2) Browser-level abort (Next.js nav)    → TypeError: 'Failed to fetch'
        //   3) Already-unmounted component          → mounted === false
        if (!mounted) return;
        if (err && err.name === 'AbortError') return;
        if (ctrl.signal.aborted) return;
        // Stay quiet on transient TypeError during route prefetch / page lifecycle,
        // it'll self-heal on the next 15s interval poll.
        if (err && err.name === 'TypeError') return;
        console.error('Failed to fetch runtimes:', err);
      }
    };

    fetchRuntimes();
    const interval = setInterval(fetchRuntimes, 15000);

    return () => {
      mounted = false;
      ctrl.abort();
      clearInterval(interval);
    };
  }, []);

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <span className="text-xs uppercase tracking-wide text-muted-foreground">
              Runtime
            </span>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`w-2 h-2 rounded-full ${
                  connected ? 'bg-[hsl(160,18%,52%)]' : 'bg-destructive'
                }`}
              />
              <span className="text-xs text-muted-foreground">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          <Select value={value} onValueChange={onChange}>
            <SelectTrigger className="w-[180px]" data-testid="runtime-selector-trigger">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {runtimes.map((rt) => (
                <SelectItem
                  key={rt.name}
                  value={rt.name}
                  data-testid={`runtime-selector-option-${rt.name}`}
                >
                  <span className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        rt.healthy ? 'bg-[hsl(160,18%,52%)]' : 'bg-muted-foreground'
                      }`}
                    />
                    <span className="font-mono text-sm">{rt.name}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
};
