import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { User, Bot } from 'lucide-react';

export const TranscriptDisplay = ({ transcript, response, status }) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, response]);

  const showCursor = status === 'thinking' || status === 'speaking';

  return (
    <Card data-testid="transcript-display">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-sans">Conversation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] overflow-y-auto pr-2">
          {!transcript && !response && (
            <div className="text-sm text-muted-foreground py-12 text-center">
              Press and hold the microphone button to speak.
            </div>
          )}

          {transcript && (
            <div className="border-l-2 border-border pl-4 py-2 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <User className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs uppercase tracking-wide text-muted-foreground">
                  You
                </span>
              </div>
              <p className="text-sm" data-testid="transcript-user-text">
                {transcript}
              </p>
            </div>
          )}

          {(response || showCursor) && (
            <div className="border-l-2 border-accent pl-4 py-2">
              <div className="flex items-center gap-2 mb-1">
                <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs uppercase tracking-wide text-muted-foreground">
                  Assistant
                </span>
              </div>
              <p className="text-sm" data-testid="transcript-assistant-text">
                {response}
                {showCursor && (
                  <span className="inline-block w-1.5 h-4 bg-foreground/60 animate-pulse ml-0.5 align-middle" />
                )}
              </p>
            </div>
          )}

          <div ref={endRef} />
        </div>
      </CardContent>
    </Card>
  );
};
