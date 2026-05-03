'use client';

import React, { useState } from 'react';
import { Copy, Check, Clock, Globe, FileText } from 'lucide-react';

interface TranscriptionViewProps {
  transcription: string | null;
  language: string | null;
  duration: number | null;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

function getWordCount(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0).length;
}

export default function TranscriptionView({
  transcription,
  language,
  duration,
}: TranscriptionViewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!transcription) return;

    try {
      await navigator.clipboard.writeText(transcription);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = transcription;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!transcription) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-gray-100 text-muted">
          <FileText className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-medium text-dark">No transcription yet</h3>
        <p className="mt-1 text-sm text-muted">
          Run the transcription to generate a text version of your meeting.
        </p>
      </div>
    );
  }

  const wordCount = getWordCount(transcription);

  return (
    <div className="space-y-4">
      {/* Badges and Actions */}
      <div className="flex flex-wrap items-center gap-3">
        {duration && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
            <Clock className="h-3 w-3" />
            {formatDuration(duration)}
          </span>
        )}
        {language && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-success">
            <Globe className="h-3 w-3" />
            {language.toUpperCase()}
          </span>
        )}
        <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-muted">
          {wordCount.toLocaleString()} words
        </span>
        <div className="ml-auto">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:bg-gray-50 hover:text-dark"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-success" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Transcription Text */}
      <div className="max-h-[600px] overflow-y-auto rounded-xl border border-border bg-white p-6">
        <div className="prose prose-sm max-w-none">
          {transcription.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-3 text-sm leading-relaxed text-dark last:mb-0">
              {paragraph || '\u00A0'}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
