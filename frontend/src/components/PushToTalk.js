import { Mic, MicOff } from 'lucide-react';

const STATUS_COLORS = {
  idle: 'hsl(215, 10%, 55%)',
  listening: 'hsl(160, 18%, 52%)',
  thinking: 'hsl(35, 22%, 58%)',
  speaking: 'hsl(210, 22%, 62%)',
  error: 'hsl(0, 55%, 42%)',
  done: 'hsl(215, 10%, 55%)',
};

const STATUS_LABELS = {
  idle: 'Hold to talk',
  listening: 'Listening…',
  thinking: 'Thinking…',
  speaking: 'Speaking…',
  error: 'Error',
  done: 'Hold to talk',
};

export const PushToTalk = ({ status, onPressStart, onPressEnd, disabled }) => {
  const isActive = status === 'listening';
  const color = STATUS_COLORS[status] || STATUS_COLORS.idle;
  const label = STATUS_LABELS[status] || STATUS_LABELS.idle;
  const canPress = !disabled && (status === 'idle' || status === 'done');

  const handlePointerDown = (e) => {
    e.preventDefault();
    if (!canPress) return;
    onPressStart();
  };

  const handlePointerUp = (e) => {
    e.preventDefault();
    if (status === 'listening') onPressEnd();
  };

  let ringAnim = 'none';
  let ringOpacity = 0.45;
  let dashArray = '365';
  if (status === 'listening') {
    ringAnim = 'ringBreathe 1.5s ease-in-out infinite';
    ringOpacity = 0.85;
  } else if (status === 'thinking') {
    ringAnim = 'ringDash 2s linear infinite';
    dashArray = '20 10';
    ringOpacity = 0.7;
  } else if (status === 'speaking') {
    ringOpacity = 0.8;
  }

  return (
    <div className="flex flex-col items-center gap-4" data-testid="push-to-talk-container">
      <div className="relative inline-flex items-center justify-center w-28 h-28 md:w-32 md:h-32">
        <svg
          className="absolute inset-0 w-full h-full -rotate-90"
          viewBox="0 0 128 128"
          aria-hidden
        >
          <circle
            cx="64"
            cy="64"
            r="58"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={dashArray}
            style={{ opacity: ringOpacity, animation: ringAnim }}
          />
        </svg>

        <button
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          onContextMenu={(e) => e.preventDefault()}
          disabled={disabled}
          aria-pressed={isActive}
          aria-label={label}
          data-testid="push-to-talk-button"
          className={`
            relative z-10 w-24 h-24 md:w-28 md:h-28 rounded-full
            flex items-center justify-center
            bg-secondary border border-border
            transition-colors duration-150
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
            focus-visible:ring-offset-2 focus-visible:ring-offset-background
            ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:border-foreground/20'}
            ${isActive ? 'scale-[0.96] bg-accent' : ''}
          `}
        >
          {disabled ? (
            <MicOff className="h-8 w-8 text-muted-foreground" />
          ) : (
            <Mic className="h-8 w-8" style={{ color }} />
          )}
        </button>
      </div>

      <span
        className="text-sm text-muted-foreground font-mono tabular-nums"
        data-testid="push-to-talk-label"
      >
        {label}
      </span>
    </div>
  );
};
