'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  FileAudio,
  Clock,
  Globe,
  Play,
  Brain,
  Languages,
  CheckCircle,
  XCircle,
  FileText,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import Navbar from '@/components/Navbar';
import TranscriptionView from '@/components/TranscriptionView';
import SummaryView from '@/components/SummaryView';
import clsx from 'clsx';

interface MeetingDetailData {
  id: string;
  title: string;
  audio_filename: string | null;
  language: string | null;
  status: string;
  transcription_text: string | null;
  summary_json: {
    summary: string;
    key_decisions: string[];
    action_items: string[];
    participants: string[];
  } | null;
  translation_text: string | null;
  target_language: string | null;
  audio_duration: number | null;
  created_at: string;
  updated_at: string;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  uploaded: { label: 'Uploaded', color: 'text-gray-600', bgColor: 'bg-gray-100' },
  transcribing: { label: 'Transcribing', color: 'text-amber-700', bgColor: 'bg-amber-100' },
  transcribed: { label: 'Transcribed', color: 'text-blue-700', bgColor: 'bg-blue-100' },
  summarizing: { label: 'Summarizing', color: 'text-purple-700', bgColor: 'bg-purple-100' },
  completed: { label: 'Completed', color: 'text-emerald-700', bgColor: 'bg-emerald-100' },
  failed: { label: 'Failed', color: 'text-red-700', bgColor: 'bg-red-100' },
};

const LANGUAGES: Record<string, string> = {
  en: 'English',
  fr: 'French',
  es: 'Spanish',
  de: 'German',
  zh: 'Chinese',
  ja: 'Japanese',
  ar: 'Arabic',
  pt: 'Portuguese',
  it: 'Italian',
  ko: 'Korean',
};

type TabId = 'transcription' | 'summary' | 'translation';

export default function MeetingDetailPage() {
  const router = useRouter();
  const params = useParams();
  const meetingId = params.id as string;
  const { user, loading: authLoading } = useAuth();

  const [meeting, setMeeting] = useState<MeetingDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabId>('transcription');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState('');

  const fetchMeeting = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiClient.getMeeting(meetingId);
      setMeeting(data as unknown as MeetingDetailData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meeting.');
    } finally {
      setLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      fetchMeeting();
    }
  }, [user, authLoading, router, fetchMeeting]);

  const handleTranscribe = async () => {
    try {
      setActionLoading('transcribe');
      setActionError('');
      const result = await apiClient.transcribeMeeting(meetingId);
      await fetchMeeting();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Transcription failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSummarize = async () => {
    try {
      setActionLoading('summarize');
      setActionError('');
      const result = await apiClient.summarizeMeeting(meetingId);
      await fetchMeeting();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Summary generation failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!user) return null;

  if (error && !meeting) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <AlertCircle className="h-12 w-12 text-error" />
        <p className="text-lg font-medium text-dark">{error}</p>
        <button onClick={() => router.push('/dashboard')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!meeting) return null;

  const statusConfig = STATUS_CONFIG[meeting.status] || STATUS_CONFIG.uploaded;
  const isInProgress = meeting.status === 'transcribing' || meeting.status === 'summarizing';
  const canTranscribe = meeting.status === 'uploaded';
  const canSummarize = meeting.status === 'transcribed';
  const isCompleted = meeting.status === 'completed';
  const isFailed = meeting.status === 'failed';

  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: 'transcription', label: 'Transcription', icon: <FileText className="h-4 w-4" /> },
    { id: 'summary', label: 'Summary', icon: <Brain className="h-4 w-4" /> },
    { id: 'translation', label: 'Translation', icon: <Languages className="h-4 w-4" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Back button */}
        <button
          onClick={() => router.push('/dashboard')}
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-muted transition-colors hover:text-dark"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>

        {/* Meeting Header */}
        <div className="card mb-6 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl font-bold text-dark">{meeting.title}</h1>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                {/* Status Badge */}
                <span
                  className={clsx(
                    'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium',
                    statusConfig.bgColor,
                    statusConfig.color
                  )}
                >
                  {isInProgress && <Loader2 className="h-3 w-3 animate-spin" />}
                  {isCompleted && <CheckCircle className="h-3 w-3" />}
                  {isFailed && <XCircle className="h-3 w-3" />}
                  {statusConfig.label}
                </span>

                {/* Audio filename */}
                {meeting.audio_filename && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-muted">
                    <FileAudio className="h-3 w-3" />
                    {meeting.audio_filename}
                  </span>
                )}

                {/* Language */}
                {meeting.language && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-success">
                    <Globe className="h-3 w-3" />
                    {LANGUAGES[meeting.language] || meeting.language.toUpperCase()}
                  </span>
                )}

                {/* Duration */}
                {meeting.audio_duration && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
                    <Clock className="h-3 w-3" />
                    {formatDuration(meeting.audio_duration)}
                  </span>
                )}
              </div>
              <p className="mt-2 text-xs text-muted">
                Created {formatDate(meeting.created_at)}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-shrink-0 gap-3">
              {canTranscribe && (
                <button
                  onClick={handleTranscribe}
                  disabled={actionLoading !== null}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  {actionLoading === 'transcribe' ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Transcribing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Transcribe
                    </>
                  )}
                </button>
              )}
              {canSummarize && (
                <button
                  onClick={handleSummarize}
                  disabled={actionLoading !== null}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  {actionLoading === 'summarize' ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Summarizing...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4" />
                      Generate Summary
                    </>
                  )}
                </button>
              )}
              {(isCompleted || isFailed) && canTranscribe === false && canSummarize === false && isCompleted && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-4 py-2 text-sm font-medium text-success">
                  <CheckCircle className="h-4 w-4" />
                  Processing Complete
                </span>
              )}
            </div>
          </div>

          {/* Action Error */}
          {actionError && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{actionError}</span>
            </div>
          )}
        </div>

        {/* Tabs */}
        {(meeting.transcription_text || meeting.summary_json || meeting.translation_text) && (
          <div className="mb-6">
            <div className="flex gap-1 rounded-xl border border-border bg-gray-100 p-1">
              {tabs.map((tab) => {
                const isDisabled =
                  (tab.id === 'transcription' && !meeting.transcription_text) ||
                  (tab.id === 'summary' && !meeting.summary_json) ||
                  (tab.id === 'translation' && !meeting.translation_text);

                return (
                  <button
                    key={tab.id}
                    onClick={() => !isDisabled && setActiveTab(tab.id)}
                    disabled={isDisabled}
                    className={clsx(
                      'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200',
                      activeTab === tab.id
                        ? 'bg-white text-dark shadow-sm'
                        : isDisabled
                        ? 'cursor-not-allowed text-gray-400'
                        : 'text-muted hover:text-dark'
                    )}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="card p-6">
          {activeTab === 'transcription' && (
            <TranscriptionView
              transcription={meeting.transcription_text}
              language={meeting.language}
              duration={meeting.audio_duration}
            />
          )}

          {activeTab === 'summary' && meeting.summary_json && (
            <SummaryView
              summary={meeting.summary_json.summary}
              keyDecisions={meeting.summary_json.key_decisions}
              actionItems={meeting.summary_json.action_items}
              participants={meeting.summary_json.participants}
            />
          )}

          {activeTab === 'summary' && !meeting.summary_json && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-gray-100 text-muted">
                <Brain className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-medium text-dark">No summary yet</h3>
              <p className="mt-1 text-sm text-muted">
                Generate a summary to extract key insights from your meeting.
              </p>
            </div>
          )}

          {activeTab === 'translation' && meeting.translation_text && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                {meeting.target_language && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-50 px-3 py-1 text-xs font-medium text-purple-700">
                    <Languages className="h-3 w-3" />
                    Translated to {LANGUAGES[meeting.target_language] || meeting.target_language.toUpperCase()}
                  </span>
                )}
              </div>
              <div className="max-h-[600px] overflow-y-auto rounded-xl border border-border bg-white p-6">
                <div className="prose prose-sm max-w-none">
                  {meeting.translation_text.split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-3 text-sm leading-relaxed text-dark last:mb-0">
                      {paragraph || '\u00A0'}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'translation' && !meeting.translation_text && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-gray-100 text-muted">
                <Languages className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-medium text-dark">No translation yet</h3>
              <p className="mt-1 text-sm text-muted">
                {meeting.target_language
                  ? 'Translation will be generated when you create a summary.'
                  : 'Set a target language when uploading to get an automatic translation.'}
              </p>
            </div>
          )}

          {/* Empty state when no content at all */}
          {!meeting.transcription_text && !meeting.summary_json && !meeting.translation_text && !canTranscribe && isInProgress && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary-600" />
              <h3 className="text-lg font-medium text-dark">
                {meeting.status === 'transcribing'
                  ? 'Transcribing your meeting...'
                  : 'Generating summary...'}
              </h3>
              <p className="mt-1 text-sm text-muted">
                This may take a few minutes depending on the audio length.
              </p>
            </div>
          )}

          {!meeting.transcription_text && !meeting.summary_json && !meeting.translation_text && isFailed && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-red-50 text-error">
                <XCircle className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-medium text-dark">Processing Failed</h3>
              <p className="mt-1 text-sm text-muted">
                An error occurred while processing your meeting. Please try again.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
