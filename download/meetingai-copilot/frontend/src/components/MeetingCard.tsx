'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Clock, Globe, Trash2, FileAudio, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient, Meeting } from '@/lib/api';
import clsx from 'clsx';

interface MeetingCardProps {
  meeting: Meeting;
  onDelete: (id: string) => void;
}

const STATUS_CONFIG: Record<
  Meeting['status'],
  { label: string; bgColor: string; textColor: string }
> = {
  uploaded: {
    label: 'Uploaded',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600',
  },
  transcribing: {
    label: 'Transcribing',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-700',
  },
  transcribed: {
    label: 'Transcribed',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
  },
  summarizing: {
    label: 'Summarizing',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
  },
  completed: {
    label: 'Completed',
    bgColor: 'bg-emerald-50',
    textColor: 'text-success',
  },
  failed: {
    label: 'Failed',
    bgColor: 'bg-red-50',
    textColor: 'text-error',
  },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '--';
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (minutes > 0) return `${minutes}m ${secs}s`;
  return `${secs}s`;
}

export default function MeetingCard({ meeting, onDelete }: MeetingCardProps) {
  const router = useRouter();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const statusConfig = STATUS_CONFIG[meeting.status] || STATUS_CONFIG.uploaded;
  const isProcessing =
    meeting.status === 'transcribing' || meeting.status === 'summarizing';

  const handleClick = () => {
    router.push(`/meeting/${meeting.id}`);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true);
      return;
    }

    setDeleting(true);
    try {
      await apiClient.deleteMeeting(meeting.id);
      onDelete(meeting.id);
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(false);
  };

  return (
    <div
      onClick={handleClick}
      className={clsx(
        'card cursor-pointer p-5 transition-all duration-200 hover:shadow-md',
        isProcessing && 'animate-pulse-slow'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
              <FileAudio className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-sm font-semibold text-dark">{meeting.title}</h3>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(meeting.created_at)}
                </span>
                {meeting.audio_duration && (
                  <span className="inline-flex items-center gap-1">
                    {formatDuration(meeting.audio_duration)}
                  </span>
                )}
                {meeting.audio_filename && (
                  <span className="inline-flex items-center gap-1 truncate max-w-[150px]">
                    {meeting.audio_filename}
                  </span>
                )}
                {meeting.language && (
                  <span className="inline-flex items-center gap-1">
                    <Globe className="h-3 w-3" />
                    {meeting.language.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-shrink-0 items-center gap-2">
          <span
            className={clsx(
              'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusConfig.bgColor,
              statusConfig.textColor
            )}
          >
            {isProcessing && <Loader2 className="h-3 w-3 animate-spin" />}
            {meeting.status === 'failed' && <AlertCircle className="h-3 w-3" />}
            {statusConfig.label}
          </span>

          {showDeleteConfirm ? (
            <div className="flex items-center gap-1">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-md bg-error px-2 py-1 text-xs font-medium text-white hover:bg-red-600"
              >
                {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Delete'}
              </button>
              <button
                onClick={handleCancelDelete}
                className="rounded-md px-2 py-1 text-xs font-medium text-muted hover:text-dark"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={handleDelete}
              className="rounded-md p-1.5 text-muted transition-colors hover:bg-red-50 hover:text-error"
              title="Delete meeting"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
