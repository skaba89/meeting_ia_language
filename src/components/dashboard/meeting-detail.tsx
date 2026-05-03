"use client";

import { useState } from "react";
import { meetingsApi, type MeetingOut } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";

interface MeetingDetailProps {
  meeting: MeetingOut;
  onBack: () => void;
  onUpdate: (meeting: MeetingOut) => void;
  onDelete: (id: string) => void;
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { label: string; className: string }> = {
    uploaded: { label: "Uploaded", className: "bg-slate-100 text-slate-700" },
    transcribing: { label: "Transcribing...", className: "bg-amber-100 text-amber-700 animate-pulse" },
    transcribed: { label: "Transcribed", className: "bg-blue-100 text-blue-700" },
    summarizing: { label: "Summarizing...", className: "bg-purple-100 text-purple-700 animate-pulse" },
    completed: { label: "Completed", className: "bg-emerald-100 text-emerald-700" },
    error: { label: "Error", className: "bg-red-100 text-red-700" },
  };
  const v = variants[status] || { label: status, className: "bg-slate-100 text-slate-700" };
  return <Badge className={v.className} variant="secondary">{v.label}</Badge>;
}

export function MeetingDetail({ meeting, onBack, onUpdate, onDelete }: MeetingDetailProps) {
  const [loading, setLoading] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [targetLang, setTargetLang] = useState("fr");

  const handleTranscribe = async () => {
    setLoading(true);
    try {
      const result = await meetingsApi.transcribe(meeting.id);
      onUpdate(result);
      toast.success("Transcription complete!");
    } catch (error: any) {
      toast.error(error.message || "Transcription failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async (lang?: string) => {
    setTranslating(true);
    try {
      const result = await meetingsApi.summarize(meeting.id, lang);
      onUpdate(result);
      toast.success(lang ? `Summary with translation to ${lang.toUpperCase()} complete!` : "Summary complete!");
    } catch (error: any) {
      toast.error(error.message || "Summary failed");
    } finally {
      setTranslating(false);
    }
  };

  const canTranscribe = meeting.status === "uploaded" || meeting.status === "error";
  const canSummarize = meeting.status === "transcribed";
  const isProcessing = meeting.status === "transcribing" || meeting.status === "summarizing";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="text-lg font-semibold truncate">{meeting.title}</h1>
            <StatusBadge status={meeting.status} />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Action Bar */}
        <Card className="border-0 bg-white shadow-sm">
          <CardContent className="flex flex-wrap items-center gap-3 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
              {meeting.audio_filename}
              {meeting.language && (
                <Badge variant="outline" className="text-xs">{meeting.language.toUpperCase()}</Badge>
              )}
            </div>

            <div className="flex-1" />

            {canTranscribe && (
              <Button onClick={handleTranscribe} disabled={loading}>
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                {loading ? "Transcribing..." : "Transcribe"}
              </Button>
            )}

            {canSummarize && (
              <>
                <Button onClick={() => handleSummarize()} disabled={translating}>
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {translating ? "Summarizing..." : "Summarize"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleSummarize(targetLang)}
                  disabled={translating}
                >
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                  Summarize + Translate
                  <select
                    className="ml-2 bg-transparent border-0 text-sm font-medium cursor-pointer"
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value)}
                  >
                    <option value="fr">FR</option>
                    <option value="en">EN</option>
                    <option value="es">ES</option>
                    <option value="de">DE</option>
                    <option value="ja">JA</option>
                    <option value="zh">ZH</option>
                  </select>
                </Button>
              </>
            )}

            {isProcessing && (
              <div className="flex items-center gap-2 text-sm text-amber-600">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-amber-600 border-t-transparent" />
                Processing...
              </div>
            )}

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Meeting</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete &quot;{meeting.title}&quot; and its audio file. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => onDelete(meeting.id)} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </CardContent>
        </Card>

        {/* Content Tabs */}
        <Tabs defaultValue="transcription" className="space-y-4">
          <TabsList className="bg-white shadow-sm">
            <TabsTrigger value="transcription">Transcription</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            {meeting.translation && (
              <TabsTrigger value="translation">Translation ({meeting.translation_lang?.toUpperCase()})</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="transcription">
            <Card className="border-0 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Transcription</CardTitle>
              </CardHeader>
              <CardContent>
                {meeting.transcription ? (
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{meeting.transcription}</p>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <svg className="h-10 w-10 mx-auto mb-3 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <p>No transcription yet. Click &quot;Transcribe&quot; to generate one.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="summary">
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="border-0 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-blue-500" />
                    Decisions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {meeting.summary_decisions ? (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{meeting.summary_decisions}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">No decisions extracted yet.</p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-0 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                    Action Items
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {meeting.summary_actions ? (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{meeting.summary_actions}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">No action items extracted yet.</p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-0 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {meeting.summary_overview ? (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{meeting.summary_overview}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">No summary overview yet.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {meeting.translation && (
            <TabsContent value="translation">
              <Card className="border-0 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                    </svg>
                    Translation — {meeting.translation_lang?.toUpperCase()}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{meeting.translation}</p>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  );
}
