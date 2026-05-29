import { Inter_Tight, JetBrains_Mono } from 'next/font/google';
import { Toaster } from '@/components/ui/sonner';
import { Layout } from '@/components/Layout';
import '@/index.css';

const interTight = Inter_Tight({ 
  subsets: ['latin'],
  variable: '--font-inter-tight',
  weight: ['300', '400', '500', '600', '700'],
});

const jetBrainsMono = JetBrains_Mono({ 
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  weight: ['400', '500', '600'],
});

export const metadata = {
  title: 'MURMUR - Real-time Voice Pipeline Benchmarking',
  description: 'Measure STT → LLM → TTS latency across vLLM, SGLang, and Ollama with a measurement-first design.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${interTight.variable} ${jetBrainsMono.variable}`}>
        <Layout>{children}</Layout>
        <Toaster />
      </body>
    </html>
  );
}
