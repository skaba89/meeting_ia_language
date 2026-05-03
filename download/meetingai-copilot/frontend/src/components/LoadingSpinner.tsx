'use client';

import React from 'react';
import clsx from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  className?: string;
  color?: string;
}

const SIZE_MAP = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
} as const;

const TEXT_SIZE_MAP = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-sm',
  xl: 'text-base',
} as const;

const BORDER_MAP = {
  sm: 'border-[2px]',
  md: 'border-2',
  lg: 'border-[3px]',
  xl: 'border-4',
} as const;

export default function LoadingSpinner({
  size = 'md',
  text,
  className,
  color = 'text-primary-600',
}: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <div
        className={clsx(
          'animate-spin rounded-full border-gray-200 border-t-current',
          SIZE_MAP[size],
          BORDER_MAP[size],
          color
        )}
        role="status"
        aria-label={text || 'Loading'}
      />
      {text && (
        <p className={clsx('font-medium text-muted', TEXT_SIZE_MAP[size])}>
          {text}
        </p>
      )}
    </div>
  );
}

/* Full-page loading overlay */
export function PageLoader({ text }: { text?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}

/* Inline section loader */
export function SectionLoader({ text }: { text?: string }) {
  return (
    <div className="flex items-center justify-center py-16">
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}

/* Pulse animation loader (alternative to spinner) */
export function PulseLoader({ size = 'md', text }: { size?: 'sm' | 'md' | 'lg'; text?: string }) {
  const dotSize = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2 w-2',
    lg: 'h-2.5 w-2.5',
  }[size];

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className={clsx('rounded-full bg-primary-500', dotSize)}
            style={{
              animation: 'pulse 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      {text && <p className="text-sm font-medium text-muted">{text}</p>}
    </div>
  );
}
