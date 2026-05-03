"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { meetingsApi, type MeetingListOut, type MeetingOut } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { MeetingDetail } from "./meeting-detail";
import { AudioUpload } from "@/components/upload/audio-upload";
import { toast } from "sonner";

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { label: string; className: string }> = {
    uploaded: { label: "Uploaded", className: "bg-slate-100 text-slate-700" },
    transcribing: { label: "Transcribing", className: "bg-amber-100 text-amber-700 animate-pulse" },
    transcribed: { label: "Transcribed", className: "bg-blue-100 text-blue-700" },
    summarizing: { label: "Summarizing", className: "bg-purple-100 text-purple-700 animate-pulse" },
    completed: { label: "Completed", className: "bg-emerald-100 text-emerald-700" },
    error: { label: "Error", className: "bg-red-100 text-red-700" },
  };
  const v = variants[status] || { label: status, className: "bg-slate-100 text-slate-700" };
  return <Badge className={v.className} variant="secondary">{v.label}</Badge>;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Dashboard() {
  const { user, logout } = useAuthStore();
  const [meetings, setMeetings] = useState<MeetingListOut[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchMeetings = useCallback(async () => {
    try {
      const data = await meetingsApi.list();
      setMeetings(data);
    } catch (error: any) {
      toast.error("Failed to load meetings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings, refreshKey]);

  const handleUploadSuccess = () => {
    setRefreshKey((k) => k + 1);
  };

  const handleMeetingUpdated = (updated: MeetingOut) => {
    setSelectedMeeting(updated);
    setRefreshKey((k) => k + 1);
  };

  const handleBackToList = () => {
    setSelectedMeeting(null);
    setRefreshKey((k) => k + 1);
  };

  const handleDelete = async (id: string) => {
    try {
      await meetingsApi.delete(id);
      toast.success("Meeting deleted");
      setSelectedMeeting(null);
      setRefreshKey((k) => k + 1);
    } catch (error: any) {
      toast.error(error.message || "Failed to delete meeting");
    }
  };

  // Detail view for selected meeting
  if (selectedMeeting) {
    return (
      <MeetingDetail
        meeting={selectedMeeting}
        onBack={handleBackToList}
        onUpdate={handleMeetingUpdated}
        onDelete={handleDelete}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center">
              <svg className="h-5 w-5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h1 className="text-lg font-semibold tracking-tight">MeetingAI Copilot</h1>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {user?.name || user?.email}
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Upload Section */}
        <AudioUpload onUploadSuccess={handleUploadSuccess} />

        {/* Meetings List */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Your Meetings</h2>
            <Button variant="ghost" size="sm" onClick={() => setRefreshKey((k) => k + 1)}>
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : meetings.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <svg className="h-12 w-12 text-muted-foreground/40 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                <h3 className="text-lg font-medium text-muted-foreground">No meetings yet</h3>
                <p className="text-sm text-muted-foreground mt-1">Upload an audio file to get started</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {meetings.map((meeting) => (
                <Card
                  key={meeting.id}
                  className="cursor-pointer hover:shadow-md transition-shadow border-0 bg-white"
                  onClick={() => setSelectedMeeting({ ...meeting } as MeetingOut)}
                >
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                        <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-medium truncate">{meeting.title}</h3>
                        <p className="text-sm text-muted-foreground truncate">
                          {meeting.audio_filename} • {formatDate(meeting.created_at)}
                        </p>
                      </div>
                    </div>
                    <StatusBadge status={meeting.status} />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
