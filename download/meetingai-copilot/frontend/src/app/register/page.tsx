'use client';

import React, { useState, FormEvent, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FileAudio,
  Loader2,
  Eye,
  EyeOff,
  Shield,
  Zap,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import clsx from 'clsx';

function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 1) return { score, label: 'Weak', color: 'bg-error' };
  if (score <= 2) return { score, label: 'Fair', color: 'bg-warning' };
  if (score <= 3) return { score, label: 'Good', color: 'bg-blue-500' };
  return { score, label: 'Strong', color: 'bg-success' };
}

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);
  const passwordTooShort = password.length > 0 && password.length < 8;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);

    try {
      await register(email, password, fullName);
      router.push('/dashboard');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left: Illustration / Brand */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-gradient-to-br from-accent-600 via-accent-700 to-primary-700 overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute top-20 right-20 h-64 w-64 rounded-full bg-white/5 blur-xl" />
        <div className="absolute bottom-10 left-10 h-96 w-96 rounded-full bg-primary-500/10 blur-2xl" />
        <div className="absolute top-1/3 right-1/3 h-32 w-32 rounded-full bg-white/5 blur-lg" />

        <div className="relative flex flex-col justify-center px-16 py-20">
          {/* Logo */}
          <Link href="/" className="mb-12 flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <FileAudio className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">
              Meeting<span className="text-accent-300">AI</span>
            </span>
          </Link>

          {/* Headline */}
          <h1 className="text-3xl font-bold text-white xl:text-4xl">
            Start your journey to
            <br />
            smarter meetings
          </h1>
          <p className="mt-4 max-w-md text-lg text-accent-100">
            Create your free account and start transcribing, summarizing, and translating meetings
            in minutes.
          </p>

          {/* Benefits */}
          <div className="mt-10 space-y-4">
            {[
              { icon: Zap, text: '5 free meetings per month' },
              { icon: Shield, text: 'No credit card required' },
              { icon: CheckCircle, text: 'Cancel anytime' },
            ].map((item) => (
              <div key={item.text} className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10">
                  <item.icon className="h-4 w-4 text-accent-300" />
                </div>
                <span className="text-sm font-medium text-accent-50">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Form */}
      <div className="flex w-full flex-col justify-center px-4 py-12 sm:px-6 lg:w-1/2 lg:px-16 xl:px-20">
        <div className="mx-auto w-full max-w-md">
          {/* Mobile logo */}
          <div className="mb-8 text-center lg:hidden">
            <Link href="/" className="inline-flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-accent-600">
                <FileAudio className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-dark">
                Meeting<span className="gradient-text">AI</span>
              </span>
            </Link>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-dark">Create your account</h2>
            <p className="mt-2 text-sm text-muted">
              Get started with MeetingAI Copilot for free.
            </p>
          </div>

          {/* Social login buttons */}
          <div className="mb-6 grid grid-cols-2 gap-3">
            <button
              type="button"
              className="btn-secondary justify-center gap-2 py-2.5"
              onClick={() => {}}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Google
            </button>
            <button
              type="button"
              className="btn-secondary justify-center gap-2 py-2.5"
              onClick={() => {}}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="#00A4EF">
                <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z" />
              </svg>
              Microsoft
            </button>
          </div>

          {/* Divider */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-gray-50 px-4 text-muted">or continue with email</span>
            </div>
          </div>

          {/* Form card */}
          <div className="card p-6">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Error Message */}
              {error && (
                <div className="animate-fade-in flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-red-100">
                    <span className="text-xs font-bold">!</span>
                  </div>
                  <span>{error}</span>
                </div>
              )}

              {/* Full Name */}
              <div>
                <label htmlFor="fullName" className="mb-1.5 block text-sm font-medium text-dark">
                  Full name
                </label>
                <input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoComplete="name"
                  placeholder="John Doe"
                  className="input-field"
                />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-dark">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                  className="input-field"
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-dark">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    className={clsx(
                      'input-field pr-10',
                      passwordTooShort && 'border-error focus:border-error focus:ring-error'
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-dark"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* Password strength indicator */}
                {password.length > 0 && (
                  <div className="mt-2">
                    <div className="flex gap-1.5">
                      {[1, 2, 3, 4, 5].map((level) => (
                        <div
                          key={level}
                          className={clsx(
                            'h-1.5 flex-1 rounded-full transition-all duration-300',
                            passwordStrength.score >= level
                              ? passwordStrength.color
                              : 'bg-gray-200'
                          )}
                        />
                      ))}
                    </div>
                    <p
                      className={clsx(
                        'mt-1.5 text-xs font-medium',
                        passwordStrength.score <= 1 && 'text-error',
                        passwordStrength.score === 2 && 'text-warning',
                        passwordStrength.score === 3 && 'text-blue-600',
                        passwordStrength.score >= 4 && 'text-success'
                      )}
                    >
                      {passwordStrength.label}
                    </p>
                  </div>
                )}

                {passwordTooShort && (
                  <p className="mt-1.5 text-xs text-error">
                    Password must be at least 8 characters
                  </p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !fullName || !email || !password || passwordTooShort}
                className="btn-primary w-full py-2.5"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  'Create Account'
                )}
              </button>

              {/* Terms */}
              <p className="text-center text-xs text-muted">
                By creating an account, you agree to our{' '}
                <a href="#" className="text-primary-600 hover:underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-primary-600 hover:underline">
                  Privacy Policy
                </a>
              </p>
            </form>
          </div>

          {/* Login Link */}
          <p className="mt-6 text-center text-sm text-muted">
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-semibold text-primary-600 hover:text-primary-700"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
