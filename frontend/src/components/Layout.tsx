'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from './ui/button';
import { Moon, Sun } from 'lucide-react';

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<string>('dark');
  const pathname = usePathname();

  useEffect(() => {
    const stored = localStorage.getItem('murmur-theme') || 'dark';
    setTheme(stored);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('murmur-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const isActive = (path: string) => pathname === path;

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <header
        className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60"
        data-testid="top-nav"
      >
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 md:h-16 items-center justify-between">
            {/* Left: wordmark + status dot */}
            <div className="flex items-center gap-3">
              <Link href="/" className="text-lg md:text-xl font-semibold tracking-tight">
                MURMUR
              </Link>
              <span
                className="w-1.5 h-1.5 rounded-full bg-[hsl(160,18%,52%)]"
                data-testid="status-dot"
                title="System operational"
              />
            </div>

            {/* Right: nav links + theme toggle */}
            <div className="flex items-center gap-6">
              <nav className="hidden md:flex items-center gap-6" data-testid="nav-links">
                <Link
                  href="/demo"
                  className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                    isActive('/demo')
                      ? 'underline decoration-border underline-offset-8 text-foreground'
                      : 'text-muted-foreground'
                  }`}
                  data-testid="topnav-link-demo"
                >
                  Demo
                </Link>
                <Link
                  href="/benchmarks"
                  className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                    isActive('/benchmarks')
                      ? 'underline decoration-border underline-offset-8 text-foreground'
                      : 'text-muted-foreground'
                  }`}
                  data-testid="topnav-link-benchmarks"
                >
                  Benchmarks
                </Link>
                <Link
                  href="/docs"
                  className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                    isActive('/docs')
                      ? 'underline decoration-border underline-offset-8 text-foreground'
                      : 'text-muted-foreground'
                  }`}
                  data-testid="topnav-link-docs"
                >
                  Docs
                </Link>
              </nav>

              <Button
                variant="ghost"
                size="sm"
                onClick={toggleTheme}
                data-testid="theme-toggle"
                className="h-9 w-9 p-0"
              >
                {theme === 'dark' ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
                <span className="sr-only">Toggle theme</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <main>{children}</main>
    </div>
  );
};
