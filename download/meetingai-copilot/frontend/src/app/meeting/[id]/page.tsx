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
  Copy,
  Download,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { useToast } from '@/components/Toast';
import { usePolling } from '@/hooks/usePolling';
import Navbar from '@/components/Navbar';
import LoadingSpinner from '@/components/LoadingSpinner';
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

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string; progress?: number }> = {
  uploaded: { label: 'Uploaded', color: 'text-gray-600', bgColor: 'bg-gray-100', progress: 0 },
  transcribing: { label: 'Transcribing', color: 'text-amber-700', bgColor: 'bg-amber-100', progress: 40 },
  transcribed: { label: 'Transcribed', color: 'text-blue-700', bgColor: 'bg-blue-100', progress: 60 },
  summarizing: { label: 'Summarizing', color: 'text-purple-700', bgColor: 'bg-purple-100', progress: 80 },
  completed: { label: 'Completed', color: 'text-emerald-700', bgColor: 'bg-emerald-100', progress: 100 },
  failed: { label: 'Failed', color: 'text-red-700', bgColor: 'bg-red-100', progress: 0 },
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

const TRANSLATE_LANGUAGES = [
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
  { value: 'de', label: 'German' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ar', label: 'Arabic' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'it', label: 'Italian' },
  { value: 'ko', label: 'Korean' },
];

type TabId = 'transcription' | 'summary' | 'translation';

export default function MeetingDetailPage() {
  const router = useRouter();
  const params = useParams();
  const meetingId = params.id as string;
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [meeting, setMeeting] = useState<MeetingDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabId>('transcription');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState('');
  const [translateLanguage, setTranslateLanguage] = useState('fr');
  const [showTranslateDropdown, setShowTranslateDropdown] = useState(false);

  const fetchMeeting = useCallback(async () => {
    try {
      setError('');
      const data = await apiClient.getMeeting(meetingId);
      setMeeting(data as unknown as MeetingDetailData);
    } catch (err) {
      if (!meeting) {
        setError(err instanceof Error ? err.message : 'Failed to load meeting.');
      }
    } finally {
      setLoading(false);
    }
  }, [meetingId, meeting]);

  // Initial fetch
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      fetchMeeting();
    }
  }, [user, authLoading, router, fetchMeeting]);

  // Auto-poll when meeting is processing
  const isInProgress =
    meeting?.status === 'transcribing' || meeting?.status === 'summarizing';

  usePolling(fetchMeeting, {
    interval: 5000,
    enabled: isInProgress,
    stopWhen: (data) => {
      const m = data as unknown as MeetingDetailData;
      return m?.status === 'completed' || m?.status === 'failed';
    },
  });

  const handleTranscribe = async () => {
    try {
      setActionLoading('transcribe');
      setActionError('');
      await apiClient.transcribeMeeting(meetingId);
      toast.success('Transcription started');
      await fetchMeeting();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Transcription failed.';
      setActionError(msg);
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSummarize = async () => {
    try {
      setActionLoading('summarize');
      setActionError('');
      await apiClient.summarizeMeeting(meetingId);
      toast.success('Summary generation started');
      await fetchMeeting();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Summary generation failed.';
      setActionError(msg);
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleTranslate = async () => {
    try {
      setActionLoading('translate');
      setActionError('');
      setShowTranslateDropdown(false);
      await apiClient.translateMeeting(meetingId, translateLanguage);
      toast.success(`Translation to ${LANGUAGES[translateLanguage]} started`);
      await fetchMeeting();
      setActiveTab('translation');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Translation failed.';
      setActionError(msg);
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCopyText = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard`);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const handleDownloadText = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('File downloaded');
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

  const formatFileSize = (filename: string | null) => {
    // We don't have file size from API, just show filename
    return filename;
  };

  if (authLoading || loading) {
    return <LoadingSpinner size="lg" className="min-h-screen" text="Loading meeting..." />;
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
  const canTranscribe = meeting.status === 'uploaded';
  const canSummarize = meeting.status === 'transcribed';
  const isCompleted = meeting.status === 'completed';
  const isFailed = meeting.status === 'failed';

  const tabs: { id: TabId; label: string; icon: React.ReactNode; available: boolean }[] = [
    {
      id: 'transcription',
      label: 'Transcription',
      icon: <FileText className="h-4 w-4" />,
      available: !!meeting.transcription_text,
    },
    {
      id: 'summary',
      label: 'Summary',
      icon: <Brain className="h-4 w-4" />,
      available: !!meeting.summary_json,
    },
    {
      id: 'translation',
      label: 'Translation',
      icon: <Languages className="h-4 w-4" />,
      available: !!meeting.translation_text,
    },
  ];

  // Build export text
  const getExportText = () => {
    let text = `Meeting: ${meeting.title}\n`;
    text += `Date: ${formatDate(meeting.created_at)}\n`;
    text += `Status: ${statusConfig.label}\n`;
    if (meeting.audio_duration) text += `Duration: ${formatDuration(meeting.audio_duration)}\n`;
    if (meeting.language) text += `Language: ${LANGUAGES[meeting.language] || meeting.language}\n`;
    text += '\n--- TRANSCRIPTION ---\n\n';
    text += meeting.transcription_text || '(No transcription available)';
    if (meeting.summary_json) {
      text += '\n\n--- SUMMARY ---\n\n';
      text += meeting.summary_json.summary || '';
      if (meeting.summary_json.key_decisions?.length) {
        text += '\n\nKey Decisions:\n';
        meeting.summary_json.key_decisions.forEach((d) => (text += `• ${d}\n`));
      }
      if (meeting.summary_json.action_items?.length) {
        text += '\nAction Items:\n';
        meeting.summary_json.action_items.forEach((a) => (text += `• ${a}\n`));
      }
    }
    if (meeting.translation_text) {
      text += '\n\n--- TRANSLATION ---\n\n';
      text += meeting.translation_text;
    }
    return text;
  };

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

              {/* Status + Progress */}
              <div className="mt-3 flex flex-wrap items-center gap-3">
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

                {isInProgress && statusConfig.progress !== undefined && (
                  <div className="flex items-center gap-2">
                    <div className="progress-bar w-24">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${statusConfig.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted">{statusConfig.progress}%</span>
                  </div>
                )}
              </div>

              {/* Metadata pills */}
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {meeting.audio_filename && (
                  <span className="badge bg-gray-100 text-muted">
                    <FileAudio className="h-3 w-3" />
                    {formatFileSize(meeting.audio_filename)}
                  </span>
                )}
                {meeting.language && (
                  <span className="badge bg-emerald-50 text-success">
                    <Globe className="h-3 w-3" />
                    {LANGUAGES[meeting.language] || meeting.language.toUpperCase()}
                  </span>
                )}
                {meeting.audio_duration && (
                  <span className="badge bg-primary-50 text-primary-700">
                    <Clock className="h-3 w-3" />
                    {formatDuration(meeting.audio_duration)}
                  </span>
                )}
                <span className="badge bg-gray-100 text-muted">
                  {formatDate(meeting.created_at)}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-shrink-0 flex-wrap gap-2">
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

              {/* Translate button with dropdown */}
              {(isCompleted || meeting.status === 'transcribed') && (
                <div className="relative">
                  <button
                    onClick={() => setShowTranslateDropdown(!showTranslateDropdown)}
                    disabled={actionLoading !== null}
                    className="btn-secondary inline-flex items-center gap-2"
                  >
                    {actionLoading === 'translate' ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Translating...
                      </>
                    ) : (
                      <>
                        <Languages className="h-4 w-4" />
                        Translate
                      </>
                    )}
                  </button>
                  {showTranslateDropdown && (
                    <div className="absolute right-0 top-full mt-2 z-10 w-56 card p-3 shadow-lg animate-scale-in">
                      <label className="mb-2 block text-xs font-medium text-muted">
                        Target language
                      </label>
                      <select
                        value={translateLanguage}
                        onChange={(e) => setTranslateLanguage(e.target.value)}
                        className="input-field mb-3 py-1.5 text-sm"
                      >
                        {TRANSLATE_LANGUAGES.map((lang) => (
                          <option key={lang.value} value={lang.value}>
                            {lang.label}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={handleTranslate}
                        className="btn-primary w-full py-2 text-sm"
                      >
                        Start Translation
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Export buttons */}
              {isCompleted && (
                <div className="flex gap-1.5">
                  <button
                    onClick={() => handleCopyText(getExportText(), 'Meeting content')}
                    className="btn-ghost inline-flex items-center gap-1.5 px-3 py-2"
                    title="Copy all content"
                  >
                    <Copy className="h-4 w-4" />
                    <span className="hidden sm:inline">Copy</span>
                  </button>
                  <button
                    onClick={() =>
                      handleDownloadText(
                        getExportText(),
                        `${meeting.title.replace(/[^a-z0-9]/gi, '_')}_meeting.txt`
                      )
                    }
                    className="btn-ghost inline-flex items-center gap-1.5 px-3 py-2"
                    title="Download as text"
                  >
                    <Download className="h-4 w-4" />
                    <span className="hidden sm:inline">Export</span>
                  </button>
                </div>
              )}

              {isCompleted && !canTranscribe && !canSummarize && (
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
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => tab.available && setActiveTab(tab.id)}
                  disabled={!tab.available}
                  className={clsx(
                    'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200',
                    activeTab === tab.id
                      ? 'bg-white text-dark shadow-sm'
                      : !tab.available
                      ? 'cursor-not-allowed text-gray-400'
                      : 'text-muted hover:text-dark'
                  )}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
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
                  <span className="badge bg-purple-50 text-purple-700">
                    <Languages className="h-3 w-3" />
                    Translated to{' '}
                    {LANGUAGES[meeting.target_language] || meeting.target_language.toUpperCase()}
                  </span>
                )}
                <div className="ml-auto flex gap-2">
                  <button
                    onClick={() =>
                      handleCopyText(meeting.translation_text!, 'Translation')
                    }
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:bg-gray-50 hover:text-dark"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Copy
                  </button>
                  <button
                    onClick={() =>
                      handleDownloadText(
                        meeting.translation_text!,
                        `${meeting.title.replace(/[^a-z0-9]/gi, '_')}_translation.txt`
                      )
                    }
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:bg-gray-50 hover:text-dark"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download
                  </button>
                </div>
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
                Use the &ldquo;Translate&rdquo; button above to generate a translation of the
                transcription.
              </p>
            </div>
          )}

          {/* Empty state when no content at all */}
          {!meeting.transcription_text &&
            !meeting.summary_json &&
            !meeting.translation_text &&
            !canTranscribe &&
            isInProgress && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-6">
                  <div className="h-20 w-20 rounded-full border-4 border-primary-100 border-t-primary-500 animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Brain className="h-8 w-8 text-primary-500" />
                  </div>
                </div>
                <h3 className="text-lg font-medium text-dark">
                  {meeting.status === 'transcribing'
                    ? 'Transcribing your meeting...'
                    : 'Generating summary...'}
                </h3>
                <p className="mt-1 text-sm text-muted">
                  This may take a few minutes depending on the audio length.
                  <br />
                  The page will auto-refresh when complete.
                </p>
                <div className="mt-4 flex items-center gap-2 text-xs text-muted">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Auto-refreshing every 5 seconds
                </div>
              </div>
            )}

          {!meeting.transcription_text &&
            !meeting.summary_json &&
            !meeting.translation_text &&
            isFailed && (
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
