'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  FileAudio,
  Brain,
  Globe,
  ArrowRight,
  CheckCircle,
  ChevronDown,
  Sparkles,
  Shield,
  Zap,
  Users,
  BarChart3,
  Clock,
  Star,
  Menu,
  X,
} from 'lucide-react';
import clsx from 'clsx';

/* ─── Intersection Observer Hook for scroll animations ─── */
function useInView(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, inView };
}

/* ─── Animated section wrapper ─── */
function AnimatedSection({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, inView } = useInView();
  return (
    <div
      ref={ref}
      className={clsx(
        'transition-all duration-700',
        inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8',
        className
      )}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ─── Navbar ─── */
function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      className={clsx(
        'sticky top-0 z-50 transition-all duration-300',
        scrolled
          ? 'border-b border-border bg-white/90 backdrop-blur-xl shadow-sm'
          : 'bg-transparent'
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-accent-600 shadow-glow">
            <FileAudio className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold text-dark">
            Meeting<span className="gradient-text">AI</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm font-medium text-muted hover:text-dark transition-colors">
            Features
          </a>
          <a href="#pricing" className="text-sm font-medium text-muted hover:text-dark transition-colors">
            Pricing
          </a>
          <a href="#faq" className="text-sm font-medium text-muted hover:text-dark transition-colors">
            FAQ
          </a>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 text-sm font-medium text-dark hover:bg-gray-100 transition-colors"
          >
            Sign In
          </Link>
          <Link href="/register" className="btn-primary">
            Get Started Free
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="rounded-lg p-2 text-muted hover:bg-gray-100 md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="animate-slide-down border-t border-border bg-white px-4 pb-6 pt-4 md:hidden">
          <div className="flex flex-col gap-4">
            <a
              href="#features"
              onClick={() => setMobileOpen(false)}
              className="text-sm font-medium text-muted hover:text-dark"
            >
              Features
            </a>
            <a
              href="#pricing"
              onClick={() => setMobileOpen(false)}
              className="text-sm font-medium text-muted hover:text-dark"
            >
              Pricing
            </a>
            <a
              href="#faq"
              onClick={() => setMobileOpen(false)}
              className="text-sm font-medium text-muted hover:text-dark"
            >
              FAQ
            </a>
            <hr className="border-border" />
            <Link href="/login" className="text-sm font-medium text-dark">
              Sign In
            </Link>
            <Link href="/register" className="btn-primary w-full justify-center">
              Get Started Free
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

/* ─── Hero ─── */
function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-primary-400/20 via-accent-400/10 to-transparent blur-3xl -z-10" />
      <div className="absolute top-20 -right-20 h-[400px] w-[400px] rounded-full bg-gradient-to-bl from-primary-300/15 to-transparent blur-3xl -z-10" />
      <div className="absolute -bottom-20 -left-20 h-[300px] w-[300px] rounded-full bg-gradient-to-tr from-accent-300/10 to-transparent blur-3xl -z-10" />

      <div className="mx-auto max-w-6xl px-4 pb-24 pt-20 sm:px-6 sm:pb-32 sm:pt-28 lg:px-8">
        <div className="text-center">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center rounded-full border border-primary-200 bg-primary-50 px-4 py-1.5 text-sm font-medium text-primary-700 animate-bounce-in">
            <Sparkles className="mr-2 h-4 w-4" />
            Powered by Advanced AI
          </div>

          {/* Heading */}
          <h1 className="text-balance text-4xl font-extrabold tracking-tight text-dark sm:text-5xl lg:text-7xl">
            Transform meetings
            <br />
            into{' '}
            <span className="bg-gradient-to-r from-primary-600 via-primary-500 to-accent-500 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient-x">
              actionable insights
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-balance text-lg text-muted sm:text-xl">
            Upload your meeting recordings and let AI transcribe, summarize, and translate them.
            Save hours every week and never miss an important decision again.
          </p>

          {/* CTA buttons */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-base shadow-glow hover:shadow-glow-lg"
            >
              Get Started Free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="btn-secondary inline-flex items-center gap-2 px-8 py-3.5 text-base"
            >
              Sign In
            </Link>
          </div>

          {/* Social proof */}
          <div className="mt-12 flex flex-col items-center gap-4">
            <div className="flex -space-x-2">
              {['bg-primary-500', 'bg-accent-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500'].map(
                (bg, i) => (
                  <div
                    key={i}
                    className={clsx(
                      'flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-xs font-bold text-white',
                      bg
                    )}
                  >
                    {String.fromCharCode(65 + i)}
                  </div>
                )
              )}
            </div>
            <p className="text-sm text-muted">
              Trusted by <span className="font-semibold text-dark">2,500+</span> professionals worldwide
            </p>
          </div>

          {/* Floating stats */}
          <div className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-8">
            {[
              { label: 'Meetings processed', value: '50K+' },
              { label: 'Hours saved', value: '12K+' },
              { label: 'Languages', value: '10+' },
              { label: 'Uptime', value: '99.9%' },
            ].map((stat, i) => (
              <AnimatedSection key={stat.label} delay={i * 100}>
                <div className="card p-4 sm:p-6 text-center">
                  <div className="text-2xl font-extrabold gradient-text sm:text-3xl">{stat.value}</div>
                  <div className="mt-1 text-xs text-muted sm:text-sm">{stat.label}</div>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Features ─── */
function FeaturesSection() {
  const features = [
    {
      icon: FileAudio,
      title: 'Audio Transcription',
      description:
        'Upload MP3, WAV, M4A, or WebM recordings and get accurate transcriptions powered by state-of-the-art AI models.',
      color: 'bg-primary-100 text-primary-600',
    },
    {
      icon: Brain,
      title: 'Smart Summaries',
      description:
        'Get executive summaries, key decisions, and action items extracted automatically. Never miss an important point again.',
      color: 'bg-emerald-100 text-success',
    },
    {
      icon: Globe,
      title: 'Multi-language Translation',
      description:
        'Translate transcriptions and summaries into 10+ languages. Break down language barriers for global teams.',
      color: 'bg-amber-100 text-warning',
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description:
        'Process hour-long meetings in minutes. Our AI pipeline is optimized for speed without compromising accuracy.',
      color: 'bg-purple-100 text-purple-600',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description:
        'Your data is encrypted at rest and in transit. SOC 2 compliant infrastructure with strict access controls.',
      color: 'bg-rose-100 text-rose-600',
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description:
        'Share meeting insights with your team. Export to multiple formats and integrate with your existing tools.',
      color: 'bg-teal-100 text-teal-600',
    },
  ];

  return (
    <section id="features" className="border-t border-border bg-gray-50 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <AnimatedSection>
          <div className="text-center">
            <div className="mb-4 inline-flex items-center rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 uppercase tracking-wider">
              Features
            </div>
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Everything you need for smarter meetings
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              From audio to actionable insights in minutes, not hours.
            </p>
          </div>
        </AnimatedSection>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => (
            <AnimatedSection key={feature.title} delay={i * 80}>
              <div className="card-hover p-8 h-full">
                <div
                  className={clsx(
                    'mb-4 flex h-12 w-12 items-center justify-center rounded-xl',
                    feature.color
                  )}
                >
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-dark">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{feature.description}</p>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── How It Works ─── */
function HowItWorksSection() {
  const steps = [
    {
      step: '01',
      title: 'Upload your recording',
      description: 'Drag and drop your audio file or browse to upload. Supports MP3, WAV, M4A, and WebM.',
      icon: FileAudio,
    },
    {
      step: '02',
      title: 'AI processes your meeting',
      description: 'Our AI transcribes the audio, extracts key points, and generates an executive summary.',
      icon: Brain,
    },
    {
      step: '03',
      title: 'Review and share insights',
      description: 'Access your transcription, summary, and translation. Export or share with your team.',
      icon: BarChart3,
    },
  ];

  return (
    <section className="py-20 sm:py-28 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <AnimatedSection>
          <div className="text-center">
            <div className="mb-4 inline-flex items-center rounded-full border border-accent-200 bg-accent-50 px-3 py-1 text-xs font-semibold text-accent-700 uppercase tracking-wider">
              How it works
            </div>
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Three steps to meeting intelligence
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              It only takes a few minutes to go from raw audio to structured insights.
            </p>
          </div>
        </AnimatedSection>

        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {steps.map((step, i) => (
            <AnimatedSection key={step.step} delay={i * 150}>
              <div className="relative text-center">
                {/* Connector line */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] border-t-2 border-dashed border-primary-200" />
                )}
                <div className="relative mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-50 to-accent-50 border border-primary-100">
                  <step.icon className="h-10 w-10 text-primary-600" />
                  <span className="absolute -top-2 -right-2 flex h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">
                    {step.step}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-dark">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{step.description}</p>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Testimonials ─── */
function TestimonialsSection() {
  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'VP of Engineering',
      company: 'TechScale',
      quote:
        'MeetingAI saves our team at least 5 hours per week. The action items extraction is incredibly accurate — we never miss a follow-up.',
      avatar: 'SC',
      color: 'bg-primary-500',
    },
    {
      name: 'Marcus Johnson',
      role: 'Product Manager',
      company: 'InnovateCo',
      quote:
        'The multi-language translation has been a game-changer for our distributed team. We can now share meeting summaries across all our offices.',
      avatar: 'MJ',
      color: 'bg-accent-500',
    },
    {
      name: 'Elena Rodriguez',
      role: 'CEO',
      company: 'StartupFlow',
      quote:
        'I used to spend hours writing meeting notes. Now I just upload the recording and get a perfect summary. The ROI is incredible.',
      avatar: 'ER',
      color: 'bg-emerald-500',
    },
  ];

  return (
    <section className="border-t border-border bg-gray-50 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <AnimatedSection>
          <div className="text-center">
            <div className="mb-4 inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 uppercase tracking-wider">
              Testimonials
            </div>
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Loved by teams worldwide
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              See how professionals are saving time and staying aligned.
            </p>
          </div>
        </AnimatedSection>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t, i) => (
            <AnimatedSection key={t.name} delay={i * 100}>
              <div className="card-hover p-6 h-full flex flex-col">
                {/* Stars */}
                <div className="mb-4 flex gap-1">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <blockquote className="flex-1 text-sm leading-relaxed text-dark">
                  &ldquo;{t.quote}&rdquo;
                </blockquote>
                <div className="mt-6 flex items-center gap-3 border-t border-border pt-4">
                  <div
                    className={clsx(
                      'flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white',
                      t.color
                    )}
                  >
                    {t.avatar}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-dark">{t.name}</div>
                    <div className="text-xs text-muted">
                      {t.role}, {t.company}
                    </div>
                  </div>
                </div>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Pricing ─── */
function PricingSection() {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started',
      features: [
        '5 meetings per month',
        'Audio transcription',
        'Basic summaries',
        'English only',
        'Email support',
      ],
      cta: 'Get Started Free',
      href: '/register',
      highlight: false,
    },
    {
      name: 'Pro',
      price: '$19',
      period: '/month',
      description: 'For professionals and teams',
      features: [
        'Unlimited meetings',
        'Advanced AI transcription',
        'Executive summaries + action items',
        '10+ languages translation',
        'Priority processing',
        'Export to PDF/DOCX',
        'Team sharing',
        'Priority support',
      ],
      cta: 'Start Pro Trial',
      href: '/register',
      highlight: true,
    },
  ];

  return (
    <section id="pricing" className="py-20 sm:py-28 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <AnimatedSection>
          <div className="text-center">
            <div className="mb-4 inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 uppercase tracking-wider">
              Pricing
            </div>
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Simple, transparent pricing
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              Start for free. Upgrade when you need more power.
            </p>
          </div>
        </AnimatedSection>

        <div className="mt-16 grid gap-8 lg:grid-cols-2 max-w-4xl mx-auto">
          {plans.map((plan, i) => (
            <AnimatedSection key={plan.name} delay={i * 100}>
              <div
                className={clsx(
                  'relative rounded-2xl p-8 h-full flex flex-col',
                  plan.highlight
                    ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white shadow-glow-lg border-0'
                    : 'card'
                )}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-accent-500 px-4 py-1 text-xs font-bold text-white">
                    Most Popular
                  </div>
                )}
                <div className="mb-6">
                  <h3
                    className={clsx(
                      'text-lg font-semibold',
                      plan.highlight ? 'text-white' : 'text-dark'
                    )}
                  >
                    {plan.name}
                  </h3>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span
                      className={clsx(
                        'text-4xl font-extrabold',
                        plan.highlight ? 'text-white' : 'text-dark'
                      )}
                    >
                      {plan.price}
                    </span>
                    <span
                      className={clsx(
                        'text-sm',
                        plan.highlight ? 'text-primary-200' : 'text-muted'
                      )}
                    >
                      {plan.period}
                    </span>
                  </div>
                  <p
                    className={clsx(
                      'mt-2 text-sm',
                      plan.highlight ? 'text-primary-100' : 'text-muted'
                    )}
                  >
                    {plan.description}
                  </p>
                </div>

                <ul className="mb-8 flex-1 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle
                        className={clsx(
                          'h-4 w-4 flex-shrink-0',
                          plan.highlight ? 'text-accent-300' : 'text-success'
                        )}
                      />
                      <span
                        className={clsx(
                          'text-sm',
                          plan.highlight ? 'text-primary-50' : 'text-dark'
                        )}
                      >
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={clsx(
                    'inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition-all duration-200',
                    plan.highlight
                      ? 'bg-white text-primary-600 hover:bg-primary-50 shadow-md'
                      : 'btn-primary w-full'
                  )}
                >
                  {plan.cta}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── FAQ ─── */
function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left"
      >
        <span className="text-sm font-semibold text-dark sm:text-base">{question}</span>
        <ChevronDown
          className={clsx(
            'h-5 w-5 flex-shrink-0 text-muted transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>
      <div
        className={clsx(
          'overflow-hidden transition-all duration-300',
          open ? 'max-h-96 pb-5' : 'max-h-0'
        )}
      >
        <p className="text-sm leading-relaxed text-muted">{answer}</p>
      </div>
    </div>
  );
}

function FAQSection() {
  const faqs = [
    {
      question: 'What audio formats are supported?',
      answer:
        'We support all major audio formats including MP3, WAV, M4A, and WebM. Files up to 500MB can be uploaded. For larger files, please contact our support team.',
    },
    {
      question: 'How accurate is the transcription?',
      answer:
        'Our AI models achieve 95%+ accuracy on clear audio. Accuracy may vary depending on audio quality, background noise, and the number of speakers.',
    },
    {
      question: 'How many languages are supported for translation?',
      answer:
        'We currently support translation into 10+ languages including English, Spanish, French, German, Chinese, Japanese, Arabic, Portuguese, Italian, and Korean.',
    },
    {
      question: 'Is my meeting data secure?',
      answer:
        'Absolutely. All data is encrypted at rest and in transit. We are SOC 2 compliant and never share your data with third parties. You can also delete your data at any time.',
    },
    {
      question: 'Can I cancel my Pro subscription anytime?',
      answer:
        'Yes, you can cancel your Pro subscription at any time. You will continue to have access to Pro features until the end of your billing period. No hidden fees.',
    },
    {
      question: 'How long does processing take?',
      answer:
        'Most meetings are processed within minutes. A typical 1-hour meeting takes about 3-5 minutes to transcribe and summarize. Pro users get priority processing.',
    },
  ];

  return (
    <section id="faq" className="border-t border-border bg-gray-50 py-20 sm:py-28">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <AnimatedSection>
          <div className="text-center">
            <div className="mb-4 inline-flex items-center rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 uppercase tracking-wider">
              FAQ
            </div>
            <h2 className="text-3xl font-bold text-dark sm:text-4xl">
              Frequently asked questions
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
              Everything you need to know about MeetingAI Copilot.
            </p>
          </div>
        </AnimatedSection>

        <AnimatedSection delay={200}>
          <div className="mt-12">
            {faqs.map((faq) => (
              <FAQItem key={faq.question} question={faq.question} answer={faq.answer} />
            ))}
          </div>
        </AnimatedSection>
      </div>
    </section>
  );
}

/* ─── CTA ─── */
function CTASection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 py-20 sm:py-28">
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 h-[400px] w-[400px] rounded-full bg-white/5 blur-3xl -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 h-[300px] w-[300px] rounded-full bg-accent-500/10 blur-3xl translate-x-1/2 translate-y-1/2" />

      <div className="relative mx-auto max-w-6xl px-4 text-center sm:px-6 lg:px-8">
        <AnimatedSection>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            Ready to transform your meetings?
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-primary-100">
            Join thousands of professionals who save hours every week with AI-powered meeting
            intelligence.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-primary-600 shadow-lg transition-all duration-200 hover:bg-primary-50 hover:shadow-xl"
            >
              Start for Free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-8 py-3.5 text-base font-semibold text-white transition-all duration-200 hover:bg-white/10"
            >
              View Pricing
            </Link>
          </div>
        </AnimatedSection>
      </div>
    </section>
  );
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer className="border-t border-border bg-white py-12">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary-600 to-accent-600">
                <FileAudio className="h-4 w-4 text-white" />
              </div>
              <span className="text-lg font-bold text-dark">
                Meeting<span className="gradient-text">AI</span>
              </span>
            </Link>
            <p className="mt-3 text-sm text-muted leading-relaxed">
              Transform your meetings into actionable insights with AI-powered transcription,
              summarization, and translation.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-sm font-semibold text-dark">Product</h4>
            <ul className="mt-3 space-y-2">
              {['Features', 'Pricing', 'Integrations', 'Changelog'].map((item) => (
                <li key={item}>
                  <a href="#" className="text-sm text-muted hover:text-dark transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-sm font-semibold text-dark">Company</h4>
            <ul className="mt-3 space-y-2">
              {['About', 'Blog', 'Careers', 'Contact'].map((item) => (
                <li key={item}>
                  <a href="#" className="text-sm text-muted hover:text-dark transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-sm font-semibold text-dark">Legal</h4>
            <ul className="mt-3 space-y-2">
              {['Privacy Policy', 'Terms of Service', 'Cookie Policy', 'GDPR'].map((item) => (
                <li key={item}>
                  <a href="#" className="text-sm text-muted hover:text-dark transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-sm text-muted">
            &copy; {new Date().getFullYear()} MeetingAI Copilot. All rights reserved.
          </p>
          <div className="flex gap-6">
            {['Twitter', 'LinkedIn', 'GitHub'].map((social) => (
              <a
                key={social}
                href="#"
                className="text-sm text-muted hover:text-dark transition-colors"
              >
                {social}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ─── Main Page ─── */
export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      <LandingNav />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <TestimonialsSection />
      <PricingSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </div>
  );
}
