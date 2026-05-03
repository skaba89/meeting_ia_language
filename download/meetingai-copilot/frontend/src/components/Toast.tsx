'use client';

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
  exiting?: boolean;
}

interface ToastContextType {
  toast: (type: ToastType, message: string, duration?: number) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

let toastCounter = 0;

const TOAST_CONFIG: Record<ToastType, { icon: React.ElementType; bgColor: string; borderColor: string; iconColor: string; textColor: string }> = {
  success: {
    icon: CheckCircle,
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    iconColor: 'text-success',
    textColor: 'text-emerald-800',
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    iconColor: 'text-error',
    textColor: 'text-red-800',
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconColor: 'text-info',
    textColor: 'text-blue-800',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    iconColor: 'text-warning',
    textColor: 'text-amber-800',
  },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 250);
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, duration: number = 5000) => {
      const id = `toast-${++toastCounter}`;
      const newToast: Toast = { id, type, message, duration };
      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback(
    (message: string, duration?: number) => addToast('success', message, duration),
    [addToast]
  );
  const error = useCallback(
    (message: string, duration?: number) => addToast('error', message, duration),
    [addToast]
  );
  const info = useCallback(
    (message: string, duration?: number) => addToast('info', message, duration),
    [addToast]
  );
  const warning = useCallback(
    (message: string, duration?: number) => addToast('warning', message, duration),
    [addToast]
  );

  return (
    <ToastContext.Provider value={{ toast: addToast, success, error, info, warning }}>
      {children}
      {/* Toast container */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed right-4 top-4 z-[100] flex flex-col gap-3 pointer-events-none"
        style={{ maxWidth: '420px', width: 'calc(100% - 2rem)' }}
      >
        {toasts.map((t) => {
          const config = TOAST_CONFIG[t.type];
          const Icon = config.icon;
          return (
            <div
              key={t.id}
              className={clsx(
                'pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lg',
                config.bgColor,
                config.borderColor,
                t.exiting ? 'animate-toast-exit' : 'animate-toast-enter'
              )}
              role="alert"
            >
              <Icon className={clsx('h-5 w-5 flex-shrink-0 mt-0.5', config.iconColor)} />
              <p className={clsx('flex-1 text-sm font-medium', config.textColor)}>
                {t.message}
              </p>
              <button
                onClick={() => removeToast(t.id)}
                className={clsx(
                  'flex-shrink-0 rounded-lg p-1 transition-colors hover:bg-black/5',
                  config.textColor
                )}
                aria-label="Dismiss"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
