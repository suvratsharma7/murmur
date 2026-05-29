'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Menu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const DOCS_LIST = [
  { slug: '01-intro', title: 'Introduction', path: '/docs/01-intro.md' },
  { slug: '02-setup', title: 'Setup Guide', path: '/docs/02-setup.md' },
  { slug: '03-runtime-abstraction', title: 'Runtime Abstraction', path: '/docs/03-runtime-abstraction.md' },
  { slug: '04-api', title: 'API Reference', path: '/docs/04-api.md' },
  { slug: '05-runbook', title: 'GPU Deployment Runbook', path: '/docs/05-runbook.md' },
  { slug: '06-decisions', title: 'Architecture Decisions', path: '/docs/06-decisions.md' },
  { slug: '07-benchmarks', title: 'Benchmark Methodology', path: '/docs/07-benchmarks.md' },
  { slug: '08-future', title: 'Future Work', path: '/docs/08-future.md' },
];

export default function Docs() {
  const [activeDoc, setActiveDoc] = useState('01-intro');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDoc = async () => {
      setLoading(true);
      const doc = DOCS_LIST.find((d) => d.slug === activeDoc);
      if (!doc) return;

      try {
        const res = await fetch(doc.path);
        if (!res.ok) throw new Error('Failed to load document');
        const text = await res.text();
        setContent(text);
      } catch (err) {
        setContent(`# Error\n\nFailed to load document: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    loadDoc();
  }, [activeDoc]);

  const Sidebar = () => (
    <ScrollArea className="h-full" data-testid="docs-sidebar-nav">
      <div className="space-y-1">
        {DOCS_LIST.map((doc) => (
          <Button
            key={doc.slug}
            variant={activeDoc === doc.slug ? 'secondary' : 'ghost'}
            className="w-full justify-start text-sm"
            onClick={() => setActiveDoc(doc.slug)}
            data-testid={`docs-sidebar-link-${doc.slug}`}
          >
            {doc.title}
          </Button>
        ))}
      </div>
    </ScrollArea>
  );

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" data-testid="docs-sidebar-open-button">
                <Menu className="h-4 w-4 mr-2" />
                Documentation
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64">
              <Sidebar />
            </SheetContent>
          </Sheet>
        </div>

        <aside className="hidden md:block col-span-3">
          <Card className="sticky top-20">
            <CardContent className="pt-4">
              <Sidebar />
            </CardContent>
          </Card>
        </aside>

        <main className="col-span-12 md:col-span-9">
          <Card>
            <CardContent className="pt-6">
              {loading ? (
                <div className="space-y-4">
                  <div className="h-8 bg-muted animate-pulse rounded" />
                  <div className="h-4 bg-muted animate-pulse rounded w-3/4" />
                  <div className="h-4 bg-muted animate-pulse rounded w-1/2" />
                </div>
              ) : (
                <article
                  className="prose prose-invert max-w-none prose-headings:font-sans prose-headings:tracking-tight prose-code:font-mono prose-pre:bg-muted/40 prose-pre:border prose-pre:border-border prose-a:text-foreground prose-a:underline prose-a:decoration-border prose-a:underline-offset-4 hover:prose-a:decoration-foreground"
                  data-testid="docs-content"
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                </article>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
