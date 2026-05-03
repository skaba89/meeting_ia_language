const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiRequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  isFormData?: boolean;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_active: boolean;
}

interface Meeting {
  id: string;
  title: string;
  audio_filename: string | null;
  language: string | null;
  status: 'uploaded' | 'transcribing' | 'transcribed' | 'summarizing' | 'completed' | 'failed';
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

class ApiClient {
  private token: string | null = null;

  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('meetingai_token', token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('meetingai_token');
    }
    return this.token;
  }

  clearToken(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('meetingai_token');
    }
  }

  private async request<T = unknown>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, isFormData = false } = options;

    const requestHeaders: Record<string, string> = { ...headers };

    if (!isFormData) {
      requestHeaders['Content-Type'] = 'application/json';
    }

    const token = this.getToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      method,
      headers: requestHeaders,
    };

    if (body) {
      config.body = isFormData ? (body as FormData) : JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, config);

    if (response.status === 401) {
      this.clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please sign in again.');
    }

    if (response.status === 422) {
      const errorData = await response.json();
      const details = errorData.detail;
      if (Array.isArray(details)) {
        const messages = details.map((d: { msg: string; loc?: string[] }) => {
          const field = d.loc ? d.loc[d.loc.length - 1] : 'field';
          return `${field}: ${d.msg}`;
        });
        throw new Error(messages.join(', '));
      }
      throw new Error(details || 'Validation error');
    }

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
      } catch {
        // Use default error message
      }
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async register(data: RegisterData): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: data,
    });
  }

  async login(data: LoginData): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: data,
    });
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    return response;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async uploadMeeting(formData: FormData): Promise<Meeting> {
    return this.request<Meeting>('/meetings/upload', {
      method: 'POST',
      body: formData,
      isFormData: true,
    });
  }

  async getMeetings(skip: number = 0, limit: number = 20): Promise<Meeting[]> {
    return this.request<Meeting[]>(`/meetings/?skip=${skip}&limit=${limit}`);
  }

  async getMeeting(id: string): Promise<Meeting> {
    return this.request<Meeting>(`/meetings/${id}`);
  }

  async transcribeMeeting(id: string): Promise<Meeting> {
    return this.request<Meeting>(`/meetings/${id}/transcribe`, {
      method: 'POST',
    });
  }

  async summarizeMeeting(id: string): Promise<Meeting> {
    return this.request<Meeting>(`/meetings/${id}/summary`, {
      method: 'POST',
    });
  }

  async deleteMeeting(id: string): Promise<void> {
    return this.request<void>(`/meetings/${id}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();

export type {
  User,
  Meeting,
  LoginResponse,
  RegisterData,
  LoginData,
};
