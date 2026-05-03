'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  FileAudio,
  ArrowUpDown,
  X,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  BarChart3,
  Globe,
  Brain,
  Languages,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, Meeting } from '@/lib/api';
import { useToast } from '@/components/Toast';
import Navbar from '@/components/Navbar';
import AudioUpload from '@/components/AudioUpload';
import MeetingCard from '@/components/MeetingCard';
import LoadingSpinner from '@/components/LoadingSpinner';
import clsx from 'clsx';

const ITEMS_PER_PAGE = 10;

type SortField = 'date' | 'title' | 'status';
type SortDirection = 'asc' | 'desc';
type StatusFilter = 'all' | 'uploaded' | 'transcribing' | 'transcribed' | 'summarizing' | 'completed' | 'failed';

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const fetchMeetings = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiClient.getMeetings(0, 200);
      setMeetings(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load meetings.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      fetchMeetings();
    }
  }, [user, authLoading, router, fetchMeetings]);

  const handleDeleteMeeting = (id: string) => {
    setMeetings((prev) => prev.filter((m) => m.id !== id));
    toast.success('Meeting deleted successfully');
  };

  const handleUploadSuccess = () => {
    setShowUploadModal(false);
    fetchMeetings();
    toast.success('Meeting uploaded successfully');
  };

  // Stats
  const stats = useMemo(() => {
    const total = meetings.length;
    const transcribed = meetings.filter((m) =>
      ['transcribed', 'summarizing', 'completed'].includes(m.status)
    ).length;
    const summarized = meetings.filter((m) => m.status === 'completed').length;
    const translated = meetings.filter((m) => m.translation_text).length;
    return { total, transcribed, summarized, translated };
  }, [meetings]);

  // Filtering, sorting, pagination
  const filteredMeetings = useMemo(() => {
    let result = meetings;

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (m) =>
          m.title.toLowerCase().includes(q) ||
          m.audio_filename?.toLowerCase().includes(q)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter((m) => m.status === statusFilter);
    }

    // Sort
    result = [...result].sort((a, b) => {
      const dir = sortDirection === 'asc' ? 1 : -1;
      if (sortField === 'date') {
        return dir * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      }
      if (sortField === 'title') {
        return dir * a.title.localeCompare(b.title);
      }
      if (sortField === 'status') {
        return dir * a.status.localeCompare(b.status);
      }
      return 0;
    });

    return result;
  }, [meetings, searchQuery, statusFilter, sortField, sortDirection]);

  const totalPages = Math.ceil(filteredMeetings.length / ITEMS_PER_PAGE);
  const paginatedMeetings = filteredMeetings.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter, sortField, sortDirection]);

  // Recent activity (last 5 meetings by updated_at)
  const recentActivity = useMemo(() => {
    return [...meetings]
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 5);
  }, [meetings]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (authLoading) {
    return <LoadingSpinner size="lg" className="min-h-screen" text="Loading..." />;
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-dark">Dashboard</h1>
            <p className="mt-1 text-sm text-muted">
              Manage your meetings and upload new recordings
            </p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary inline-flex items-center gap-2 self-start"
          >
            <Plus className="h-4 w-4" />
            New Meeting
          </button>
        </div>

        {/* Stats Cards */}
        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            {
              label: 'Total Meetings',
              value: stats.total,
              icon: FileAudio,
              color: 'bg-primary-50 text-primary-600',
              iconBg: 'bg-primary-100',
            },
            {
              label: 'Transcribed',
              value: stats.transcribed,
              icon: CheckCircle,
              color: 'bg-emerald-50 text-success',
              iconBg: 'bg-emerald-100',
            },
            {
              label: 'Summarized',
              value: stats.summarized,
              icon: Brain,
              color: 'bg-purple-50 text-purple-600',
              iconBg: 'bg-purple-100',
            },
            {
              label: 'Translated',
              value: stats.translated,
              icon: Languages,
              color: 'bg-amber-50 text-warning',
              iconBg: 'bg-amber-100',
            },
          ].map((stat) => (
            <div key={stat.label} className={clsx('card p-4 sm:p-5')}>
              <div className="flex items-center gap-3">
                <div
                  className={clsx(
                    'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl',
                    stat.iconBg
                  )}
                >
                  <stat.icon className={clsx('h-5 w-5', stat.color.split(' ')[1])} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-dark">{stat.value}</p>
                  <p className="text-xs text-muted">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Main content grid */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left: Meeting list */}
          <div className="lg:col-span-2">
            {/* Search + Filter bar */}
            <div className="mb-4 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search meetings..."
                  className="input-field pl-10"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-dark"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  'btn-secondary gap-2',
                  showFilters && 'border-primary-300 bg-primary-50 text-primary-600'
                )}
              >
                <SlidersHorizontal className="h-4 w-4" />
                <span className="hidden sm:inline">Filter</span>
              </button>
            </div>

            {/* Filters panel */}
            {showFilters && (
              <div className="mb-4 card p-4 animate-slide-down">
                <div className="flex flex-wrap gap-4">
                  {/* Status filter */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-muted">Status</label>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                      className="input-field py-1.5 text-sm"
                    >
                      <option value="all">All statuses</option>
                      <option value="uploaded">Uploaded</option>
                      <option value="transcribing">Transcribing</option>
                      <option value="transcribed">Transcribed</option>
                      <option value="summarizing">Summarizing</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                    </select>
                  </div>

                  {/* Sort field */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-muted">Sort by</label>
                    <div className="flex gap-1.5">
                      {[
                        { field: 'date' as SortField, label: 'Date' },
                        { field: 'title' as SortField, label: 'Title' },
                        { field: 'status' as SortField, label: 'Status' },
                      ].map((s) => (
                        <button
                          key={s.field}
                          onClick={() => toggleSort(s.field)}
                          className={clsx(
                            'inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
                            sortField === s.field
                              ? 'border-primary-300 bg-primary-50 text-primary-600'
                              : 'border-border text-muted hover:text-dark'
                          )}
                        >
                          {s.label}
                          {sortField === s.field && (
                            <ArrowUpDown className="h-3 w-3" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Meeting List */}
            <div className="space-y-3">
              {loading ? (
                <LoadingSpinner size="lg" text="Loading meetings..." className="py-16" />
              ) : paginatedMeetings.length > 0 ? (
                <>
                  {paginatedMeetings.map((meeting) => (
                    <MeetingCard
                      key={meeting.id}
                      meeting={meeting}
                      onDelete={handleDeleteMeeting}
                    />
                  ))}
                </>
              ) : searchQuery || statusFilter !== 'all' ? (
                <div className="py-16 text-center">
                  <Search className="mx-auto mb-3 h-10 w-10 text-muted/40" />
                  <p className="text-sm text-muted">
                    No meetings found matching your filters
                  </p>
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setStatusFilter('all');
                    }}
                    className="mt-3 text-sm font-medium text-primary-600 hover:text-primary-700"
                  >
                    Clear filters
                  </button>
                </div>
              ) : meetings.length === 0 ? (
                /* Empty state */
                <div className="py-20 text-center">
                  <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary-50">
                    <FileAudio className="h-10 w-10 text-primary-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-dark">No meetings yet</h3>
                  <p className="mt-2 max-w-sm mx-auto text-sm text-muted">
                    Upload your first meeting recording to get started with AI-powered
                    transcription and summaries.
                  </p>
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="btn-primary mt-6 inline-flex items-center gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Upload Meeting
                  </button>
                </div>
              ) : null}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-muted">
                  Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}–
                  {Math.min(currentPage * ITEMS_PER_PAGE, filteredMeetings.length)} of{' '}
                  {filteredMeetings.length}
                </p>
                <div className="flex gap-1">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="btn-secondary p-2 disabled:opacity-40"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                    .map((p, i, arr) => (
                      <React.Fragment key={p}>
                        {i > 0 && arr[i - 1] !== p - 1 && (
                          <span className="flex items-center px-1 text-muted">…</span>
                        )}
                        <button
                          onClick={() => setCurrentPage(p)}
                          className={clsx(
                            'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                            currentPage === p
                              ? 'bg-primary-600 text-white'
                              : 'text-muted hover:bg-gray-100'
                          )}
                        >
                          {p}
                        </button>
                      </React.Fragment>
                    ))}
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="btn-secondary p-2 disabled:opacity-40"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right sidebar: Recent Activity */}
          <div className="lg:col-span-1">
            <div className="card p-5 sticky top-20">
              <h3 className="text-sm font-semibold text-dark mb-4 flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted" />
                Recent Activity
              </h3>
              {recentActivity.length === 0 ? (
                <p className="text-sm text-muted py-8 text-center">No activity yet</p>
              ) : (
                <div className="space-y-0">
                  {recentActivity.map((meeting, i) => {
                    const statusIcon = {
                      uploaded: <Clock className="h-3.5 w-3.5 text-gray-400" />,
                      transcribing: <Loader2 className="h-3.5 w-3.5 text-amber-500 animate-spin" />,
                      transcribed: <FileAudio className="h-3.5 w-3.5 text-blue-500" />,
                      summarizing: <Loader2 className="h-3.5 w-3.5 text-purple-500 animate-spin" />,
                      completed: <CheckCircle className="h-3.5 w-3.5 text-success" />,
                      failed: <AlertCircle className="h-3.5 w-3.5 text-error" />,
                    }[meeting.status];

                    const timeAgo = (() => {
                      const diff = Date.now() - new Date(meeting.updated_at).getTime();
                      const mins = Math.floor(diff / 60000);
                      if (mins < 1) return 'Just now';
                      if (mins < 60) return `${mins}m ago`;
                      const hrs = Math.floor(mins / 60);
                      if (hrs < 24) return `${hrs}h ago`;
                      const days = Math.floor(hrs / 24);
                      return `${days}d ago`;
                    })();

                    return (
                      <button
                        key={meeting.id}
                        onClick={() => router.push(`/meeting/${meeting.id}`)}
                        className="flex w-full items-start gap-3 py-3 border-b border-border last:border-0 text-left hover:bg-gray-50 -mx-2 px-2 rounded-lg transition-colors"
                      >
                        <div className="mt-0.5 flex-shrink-0">{statusIcon}</div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-dark">
                            {meeting.title}
                          </p>
                          <p className="text-xs text-muted capitalize">
                            {meeting.status} · {timeAgo}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-dark/50 backdrop-blur-sm animate-fade-in"
            onClick={() => setShowUploadModal(false)}
          />

          {/* Modal */}
          <div className="relative w-full max-w-lg card p-6 animate-scale-in shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-dark">Upload Meeting Recording</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="rounded-lg p-1.5 text-muted hover:bg-gray-100 hover:text-dark"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <AudioUpload onSuccess={handleUploadSuccess} />
          </div>
        </div>
      )}
    </div>
  );
}
