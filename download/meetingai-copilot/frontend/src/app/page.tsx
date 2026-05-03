import Link from 'next/link';
import { FileAudio, Brain, Globe, ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
              <FileAudio className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-dark">MeetingAI</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-dark hover:bg-gray-100"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="btn-primary"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(79,70,229,0.15),rgba(255,255,255,0))]" />
        <div className="mx-auto max-w-6xl px-4 pb-24 pt-20 sm:px-6 sm:pb-32 sm:pt-28 lg:px-8">
          <div className="text-center">
            <div className="mb-6 inline-flex items-center rounded-full border border-primary-200 bg-primary-50 px-4 py-1.5 text-sm font-medium text-primary-700">
              <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-primary-500" />
              Powered by AI
            </div>
            <h1 className="text-balance text-4xl font-extrabold tracking-tight text-dark sm:text-5xl lg:text-6xl">
              <span className="bg-gradient-to-r from-primary-600 via-primary-500 to-indigo-400 bg-clip-text text-transparent">
                MeetingAI Copilot
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-balance text-lg text-muted sm:text-xl">
              Transform your meetings into actionable insights with AI. Transcribe, summarize, and
              translate your meeting recordings effortlessly.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="btn-primary inline-flex items-center gap-2 px-6 py-3 text-base"
              >
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="btn-secondary inline-flex items-center gap-2 px-6 py-3 text-base"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-t border-border bg-gray-50 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Everything you need for smarter meetings
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              From audio to actionable insights in minutes, not hours.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1: Audio Transcription */}
            <div className="card p-8 transition-shadow duration-300 hover:shadow-md">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                <FileAudio className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-dark">Audio Transcription</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Upload your meeting recordings and get accurate transcriptions powered by
                state-of-the-art AI models. Supports MP3, WAV, M4A, and WebM formats.
              </p>
            </div>

            {/* Feature 2: Smart Summaries */}
            <div className="card p-8 transition-shadow duration-300 hover:shadow-md">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-success">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-dark">Smart Summaries</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Get executive summaries, key decisions, and action items extracted automatically.
                Never miss an important point from your meetings again.
              </p>
            </div>

            {/* Feature 3: Multi-language */}
            <div className="card p-8 transition-shadow duration-300 hover:shadow-md">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-amber-100 text-warning">
                <Globe className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-dark">Multi-language</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Translate transcriptions and summaries into 10+ languages. Break down language
                barriers and make meetings accessible to global teams.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to transform your meetings?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-primary-100">
            Join thousands of professionals who save hours every week with AI-powered meeting
            intelligence.
          </p>
          <div className="mt-8">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-base font-semibold text-primary-600 shadow-sm transition-all duration-200 hover:bg-primary-50"
            >
              Start for Free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-white py-8">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary-600">
                <FileAudio className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="text-sm font-semibold text-dark">MeetingAI Copilot</span>
            </div>
            <p className="text-sm text-muted">
              &copy; {new Date().getFullYear()} MeetingAI Copilot. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
