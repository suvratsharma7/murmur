'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="border-border shadow-lg rounded-lg bg-popover border p-3 space-y-1">
        <p className="text-xs font-mono text-muted-foreground">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-xs font-mono">
              {entry.name}: {entry.value?.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function Benchmarks() {
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBenchmarks = async () => {
      try {
        const res = await fetch(`${API}/api/benchmarks`);
        if (!res.ok) throw new Error('Failed to fetch benchmarks');
        const data = await res.json();
        setBenchmarks(data.benchmarks || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchBenchmarks();
  }, []);

  if (loading) {
    return (
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="border rounded-lg p-6">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      </div>
    );
  }

  const totalRuns = benchmarks.length;
  const avgTTFT = benchmarks.length > 0 
    ? benchmarks.reduce((acc, b) => acc + (b.ttft_ms || 0), 0) / benchmarks.length 
    : 0;
  const avgE2E = benchmarks.length > 0 
    ? benchmarks.reduce((acc, b) => acc + (b.e2e_ms || 0), 0) / benchmarks.length 
    : 0;
  const avgTPS = benchmarks.length > 0 
    ? benchmarks.reduce((acc, b) => acc + (b.output_tokens_per_second || 0), 0) / benchmarks.length 
    : 0;

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Benchmarks</h1>
        <p className="text-base text-muted-foreground">
          Runtime performance metrics from completed voice pipeline turns.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                Total Runs
              </span>
              <p className="text-2xl font-mono tabular-nums" data-testid="kpi-total-runs">
                {totalRuns}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                Avg TTFT
              </span>
              <p className="text-2xl font-mono tabular-nums" data-testid="kpi-avg-ttft">
                {avgTTFT.toFixed(0)} <span className="text-sm text-muted-foreground">ms</span>
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                Avg E2E
              </span>
              <p className="text-2xl font-mono tabular-nums" data-testid="kpi-avg-e2e">
                {avgE2E.toFixed(0)} <span className="text-sm text-muted-foreground">ms</span>
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wide text-muted-foreground">
                Avg Throughput
              </span>
              <p className="text-2xl font-mono tabular-nums" data-testid="kpi-avg-tps">
                {avgTPS.toFixed(1)} <span className="text-sm text-muted-foreground">tok/s</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card data-testid="benchmarks-charts">
        <CardHeader>
          <CardTitle className="text-sm font-sans">Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="latency">
            <TabsList data-testid="benchmarks-runtime-tabs">
              <TabsTrigger value="latency">Latency</TabsTrigger>
              <TabsTrigger value="throughput">Throughput</TabsTrigger>
            </TabsList>

            <TabsContent value="latency" className="pt-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={benchmarks.slice(0, 20)} data-testid="benchmarks-ttft-chart">
                  <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" opacity={0.6} />
                  <XAxis dataKey="runtime" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="ttft_ms" fill="hsl(var(--chart-1))" name="TTFT (ms)" />
                  <Bar dataKey="ttfb_audio_ms" fill="hsl(var(--chart-2))" name="TTFB Audio (ms)" />
                  <Bar dataKey="e2e_ms" fill="hsl(var(--chart-3))" name="E2E (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="throughput" className="pt-6">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={benchmarks.slice(0, 20)} data-testid="benchmarks-throughput-chart">
                  <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" opacity={0.6} />
                  <XAxis dataKey="runtime" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line type="monotone" dataKey="output_tokens_per_second" stroke="hsl(var(--chart-1))" name="Tokens/sec" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-sans">Raw Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table data-testid="benchmarks-raw-table">
              <TableHeader>
                <TableRow>
                  <TableHead className="font-mono text-xs">Runtime</TableHead>
                  <TableHead className="font-mono text-xs text-right">STT (ms)</TableHead>
                  <TableHead className="font-mono text-xs text-right">TTFT (ms)</TableHead>
                  <TableHead className="font-mono text-xs text-right">TTFB Audio (ms)</TableHead>
                  <TableHead className="font-mono text-xs text-right">E2E (ms)</TableHead>
                  <TableHead className="font-mono text-xs text-right">Tokens/s</TableHead>
                  <TableHead className="font-mono text-xs text-right">Tokens</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {benchmarks.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-sm text-muted-foreground py-8">
                      No benchmark data available yet. Run voice turns in Demo to generate metrics.
                    </TableCell>
                  </TableRow>
                ) : (
                  benchmarks.map((bench, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono text-xs">{bench.runtime || 'N/A'}</TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.stt_latency_ms?.toFixed(0) || '—'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.ttft_ms?.toFixed(0) || '—'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.ttfb_audio_ms?.toFixed(0) || '—'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.e2e_ms?.toFixed(0) || '—'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.output_tokens_per_second?.toFixed(1) || '—'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-right tabular-nums">
                        {bench.tokens_emitted || '—'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
