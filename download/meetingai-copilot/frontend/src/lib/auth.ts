const TOKEN_KEY = 'meetingai_token';
const REFRESH_TOKEN_KEY = 'meetingai_refresh_token';
const TOKEN_EXPIRY_KEY = 'meetingai_token_expiry';

export function saveToken(token: string, expiresIn?: number): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
    if (expiresIn) {
      const expiryTime = Date.now() + expiresIn * 1000;
      localStorage.setItem(TOKEN_EXPIRY_KEY, String(expiryTime));
    }
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function saveRefreshToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }
}

export function getRefreshToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }
  return null;
}

export function getTokenExpiry(): number | null {
  if (typeof window !== 'undefined') {
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    return expiry ? parseInt(expiry, 10) : null;
  }
  return null;
}

export function isTokenExpiringSoon(thresholdMs: number = 5 * 60 * 1000): boolean {
  const expiry = getTokenExpiry();
  if (!expiry) return false;
  return Date.now() + thresholdMs >= expiry;
}
