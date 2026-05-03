'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Loader2, Search, FileAudio } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, Meeting } from '@/lib/api';
import Navbar from '@/components/Navbar';
import AudioUpload from '@/components/AudioUpload';
import MeetingCard from '@/components/MeetingCard';

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUpload, setShowUpload] = useState(false);

  const fetchMeetings = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiClient.getMeetings(0, 100);
      setMeetings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meetings.');
    } finally {
      setLoading(false);
    }
  }, []);

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
  };

  const filteredMeetings = meetings.filter((meeting) =>
    meeting.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
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
            onClick={() => setShowUpload(!showUpload)}
            className="btn-primary inline-flex items-center gap-2 self-start"
          >
            <Plus className="h-4 w-4" />
            New Meeting
          </button>
        </div>

        {/* Upload Section */}
        {showUpload && (
          <div className="mb-8 card p-6 animate-fade-in">
            <h2 className="mb-4 text-lg font-semibold text-dark">Upload Meeting Recording</h2>
            <AudioUpload />
          </div>
        )}

        {/* Search */}
        {meetings.length > 0 && (
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search meetings..."
                className="input-field pl-10"
              />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Meeting List */}
        <div className="space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          ) : filteredMeetings.length > 0 ? (
            <>
              {filteredMeetings.map((meeting) => (
                <MeetingCard
                  key={meeting.id}
                  meeting={meeting}
                  onDelete={handleDeleteMeeting}
                />
              ))}
            </>
          ) : searchQuery ? (
            <div className="py-16 text-center">
              <p className="text-sm text-muted">No meetings found matching &quot;{searchQuery}&quot;</p>
            </div>
          ) : meetings.length === 0 ? (
            <div className="py-16 text-center">
              <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-xl bg-gray-100 text-muted">
                <FileAudio className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-medium text-dark">No meetings yet</h3>
              <p className="mt-1 text-sm text-muted">
                Upload your first meeting recording to get started.
              </p>
              <button
                onClick={() => setShowUpload(true)}
                className="btn-primary mt-4 inline-flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Upload Meeting
              </button>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
