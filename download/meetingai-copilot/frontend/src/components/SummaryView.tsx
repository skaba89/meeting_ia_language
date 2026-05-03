'use client';

import React, { useState } from 'react';
import {
  Copy,
  Check,
  CheckCircle,
  ArrowRight,
  Users,
  FileText,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';

interface SummaryViewProps {
  summary: string | null;
  keyDecisions: string[] | null;
  actionItems: string[] | null;
  participants: string[] | null;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted transition-colors hover:bg-gray-50 hover:text-dark"
    >
      {copied ? (
        <>
          <Check className="h-3 w-3 text-success" />
          Copied
        </>
      ) : (
        <>
          <Copy className="h-3 w-3" />
          Copy
        </>
      )}
    </button>
  );
}

export default function SummaryView({
  summary,
  keyDecisions,
  actionItems,
  participants,
}: SummaryViewProps) {
  if (!summary && !keyDecisions?.length && !actionItems?.length && !participants?.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-gray-100 text-muted">
          <Brain className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-medium text-dark">No summary yet</h3>
        <p className="mt-1 text-sm text-muted">
          Generate a summary to extract key insights from your meeting.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {summary && (
        <div className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-100 text-primary-600">
                <FileText className="h-4 w-4" />
              </div>
              <h3 className="text-base font-semibold text-dark">Executive Summary</h3>
            </div>
            <CopyButton text={summary} />
          </div>
          <div className="prose prose-sm max-w-none">
            {summary.split('\n').map((paragraph, index) => (
              <p key={index} className="mb-3 text-sm leading-relaxed text-dark last:mb-0">
                {paragraph || '\u00A0'}
              </p>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        {/* Key Decisions */}
        {keyDecisions && keyDecisions.length > 0 && (
          <div className="card p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-success">
                  <CheckCircle className="h-4 w-4" />
                </div>
                <h3 className="text-base font-semibold text-dark">Key Decisions</h3>
              </div>
              <CopyButton text={keyDecisions.join('\n')} />
            </div>
            <ul className="space-y-3">
              {keyDecisions.map((decision, index) => (
                <li key={index} className="flex items-start gap-3">
                  <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
                  <span className="text-sm leading-relaxed text-dark">{decision}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Items */}
        {actionItems && actionItems.length > 0 && (
          <div className="card p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-warning">
                  <ArrowRight className="h-4 w-4" />
                </div>
                <h3 className="text-base font-semibold text-dark">Action Items</h3>
              </div>
              <CopyButton text={actionItems.join('\n')} />
            </div>
            <ul className="space-y-3">
              {actionItems.map((item, index) => (
                <li key={index} className="flex items-start gap-3">
                  <ArrowRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
                  <span className="text-sm leading-relaxed text-dark">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Participants */}
      {participants && participants.length > 0 && (
        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <Users className="h-4 w-4" />
            </div>
            <h3 className="text-base font-semibold text-dark">Participants</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {participants.map((participant, index) => (
              <span
                key={index}
                className={clsx(
                  'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium',
                  'bg-gray-100 text-dark'
                )}
              >
                <Users className="h-3 w-3 text-muted" />
                {participant}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
