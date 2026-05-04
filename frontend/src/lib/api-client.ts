/**
 * API client for communicating with the MeetingAI Copilot FastAPI backend.
 * Handles authentication tokens, error responses, and API routing.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

function getApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("meetingai_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = getApiUrl(path);
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    // Handle both FastAPI HTTPException format {detail: "..."} and custom format {error: {message: "..."}}
    const message = error.detail || error.error?.message || error.message || `API Error: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

// ── Auth Types ──────────────────────────────────────────────────────

export interface UserOut {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

// ── Meeting Types ───────────────────────────────────────────────────

export interface MeetingOut {
  id: string;
  title: string;
  audio_filename: string;
  status: string;
  language: string | null;
  transcription: string | null;
  summary_decisions: string | null;
  summary_actions: string | null;
  summary_overview: string | null;
  translation: string | null;
  translation_lang: string | null;
  audio_duration_sec: number | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingListOut {
  id: string;
  title: string;
  audio_filename: string;
  status: string;
  language: string | null;
  audio_duration_sec: number | null;
  created_at: string;
}

// ── Auth API ────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, name: string, password: string) =>
    apiRequest<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password }),
    }),

  login: (email: string, password: string) =>
    apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
};

// ── Meetings API ────────────────────────────────────────────────────

export const meetingsApi = {
  list: () => apiRequest<MeetingListOut[]>("/meetings/"),

  get: (id: string) => apiRequest<MeetingOut>(`/meetings/${id}`),

  upload: async (file: File, title: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);

    const token = typeof window !== "undefined" ? localStorage.getItem("meetingai_token") : null;
    const url = getApiUrl("/meetings/upload");

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }

    return response.json() as Promise<MeetingOut>;
  },

  transcribe: (meetingId: string) =>
    apiRequest<MeetingOut>("/meetings/transcribe", {
      method: "POST",
      body: JSON.stringify({ meeting_id: meetingId }),
    }),

  summarize: (meetingId: string, targetLang?: string) =>
    apiRequest<MeetingOut>("/meetings/summary", {
      method: "POST",
      body: JSON.stringify({ meeting_id: meetingId, target_lang: targetLang || null }),
    }),

  update: (id: string, data: { title?: string }) =>
    apiRequest<MeetingOut>(`/meetings/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiRequest<{ message: string }>(`/meetings/${id}`, {
      method: "DELETE",
    }),
};
