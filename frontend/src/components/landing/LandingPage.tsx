import React from 'react';
import {
  ArrowRight,
  Clock,
  Compass,
  GraduationCap,
  HelpCircle,
  ListOrdered,
  MessageSquareText,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from 'lucide-react';
import { Logo } from '../common/Logo';

interface LandingPageProps {
  onGetStarted: () => void;
}

const STEPS = [
  { icon: Upload, title: 'Upload your notes', text: 'Drop in a lecture PDF, syllabus, or study guide.' },
  { icon: Network, title: 'See your knowledge map', text: 'We map the key concepts and what each one builds on.' },
  { icon: HelpCircle, title: 'Take a quick check-in', text: 'About a dozen short questions. No grades, no pressure.' },
  { icon: Compass, title: 'Get your roadmap', text: 'A study order that starts with the foundations you need most.' },
];

const BENEFITS = [
  {
    icon: Search,
    title: 'Finds the root cause',
    text: "Struggling with a topic often means a shaky foundation underneath it. We trace prerequisites so you fix the real problem.",
  },
  {
    icon: MessageSquareText,
    title: 'Explains every suggestion',
    text: 'Each recommendation says why: your actual answers and which later topics depend on it.',
  },
  {
    icon: ListOrdered,
    title: 'Study in the right order',
    text: "Foundations first, then what builds on them, so every session moves you forward.",
  },
];

// Small illustrative concept map for the hero (static example, not user data).
const ExampleMap: React.FC = () => (
  <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-indigo-950/40 backdrop-blur-xl">
    <div className="mb-3 flex items-center justify-between text-xs">
      <span className="font-semibold uppercase tracking-wider text-indigo-400">Example knowledge map</span>
      <span className="text-slate-500">Intro to Calculus</span>
    </div>
    <svg viewBox="0 0 320 200" className="w-full" role="img" aria-label="Example map where a weak Functions concept affects Limits and Derivatives">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4f566b" />
        </marker>
      </defs>
      <g stroke="#4f566b" strokeWidth="1.5" fill="none" markerEnd="url(#arrow)">
        <line x1="92" y1="40" x2="134" y2="88" />
        <line x1="92" y1="160" x2="134" y2="112" />
        <line x1="206" y1="100" x2="234" y2="52" />
        <line x1="206" y1="100" x2="234" y2="148" />
      </g>
      {/* Mastered */}
      <g>
        <rect x="8" y="22" width="88" height="36" rx="10" fill="rgba(16,185,129,0.12)" stroke="#10b981" />
        <text x="52" y="45" textAnchor="middle" fontSize="12" fill="#6ee7b7">Algebra</text>
        <rect x="8" y="142" width="88" height="36" rx="10" fill="rgba(16,185,129,0.12)" stroke="#10b981" />
        <text x="52" y="165" textAnchor="middle" fontSize="12" fill="#6ee7b7">Graphing</text>
      </g>
      {/* The gap */}
      <rect x="128" y="78" width="80" height="44" rx="12" fill="none" stroke="#f43f5e" strokeOpacity="0.5" className="animate-pulse motion-reduce:animate-none" />
      <rect x="134" y="82" width="68" height="36" rx="10" fill="rgba(244,63,94,0.15)" stroke="#f43f5e" />
      <text x="168" y="105" textAnchor="middle" fontSize="12" fill="#fda4af">Functions</text>
      {/* Affected downstream */}
      <rect x="232" y="22" width="80" height="36" rx="10" fill="rgba(39,44,59,0.8)" stroke="#3d4356" />
      <text x="272" y="45" textAnchor="middle" fontSize="12" fill="#9aa1b5">Limits</text>
      <rect x="232" y="142" width="80" height="36" rx="10" fill="rgba(39,44,59,0.8)" stroke="#3d4356" />
      <text x="272" y="165" textAnchor="middle" fontSize="12" fill="#9aa1b5">Derivatives</text>
    </svg>
    <p className="mt-3 text-xs leading-relaxed text-slate-400">
      <span className="font-semibold text-rose-300">Functions</span> is the gap: review it first and{' '}
      <span className="text-slate-300">Limits</span> and <span className="text-slate-300">Derivatives</span> get easier too.
    </p>
  </div>
);

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const scrollToHowItWorks = () =>
    document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Soft violet-blue glow */}
      <div aria-hidden="true" className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-indigo-600/20 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute top-[560px] -right-40 h-[360px] w-[360px] rounded-full bg-purple-600/10 blur-3xl" />

      {/* Top bar */}
      <header className="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={scrollToHowItWorks}
            className="hidden rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-900 hover:text-white sm:block"
          >
            How it works
          </button>
          <button
            type="button"
            onClick={onGetStarted}
            className="rounded-lg border border-indigo-500/40 bg-indigo-500/15 px-4 py-2 text-sm font-semibold text-indigo-200 transition hover:bg-indigo-500/25"
          >
            Get started
          </button>
        </div>
      </header>

      <main className="relative">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-10 md:grid-cols-2 md:pt-16">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
              <GraduationCap className="h-3.5 w-3.5" />
              Made for students who feel stuck
            </div>
            <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
              Lost in class?{' '}
              <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-300 bg-clip-text text-transparent">
                Let's find the missing piece.
              </span>
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-300">
              Everyone has knowledge gaps, and they're easier to fix than you think. Upload your lecture notes and
              Kno(w)Hol(e) maps the concepts, asks a few friendly questions, and shows you exactly which foundations to
              review first.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={onGetStarted}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:brightness-110 active:scale-[0.99]"
              >
                Find my knowledge gaps
                <ArrowRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={scrollToHowItWorks}
                className="inline-flex items-center justify-center rounded-xl border border-slate-700 px-6 py-3.5 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
              >
                See how it works
              </button>
            </div>

            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400">
              <li className="flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5 text-indigo-400" /> Free, no sign-up</li>
              <li className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5 text-indigo-400" /> About 5 minutes</li>
              <li className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-indigo-400" /> Your PDF isn't stored</li>
            </ul>
          </div>

          <ExampleMap />
        </section>

        {/* How it works */}
        <section id="how-it-works" className="scroll-mt-6 border-t border-slate-900 bg-slate-950/60 py-20">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">How it works</h2>
            <p className="mx-auto mt-3 max-w-xl text-center text-sm text-slate-400">
              Four steps from "I don't get it" to a plan you can actually follow.
            </p>
            <ol className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map(({ icon: Icon, title, text }, i) => (
                <li key={title} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-indigo-500/20 bg-indigo-600/10 text-indigo-400">
                      <Icon className="h-5 w-5" />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Step {i + 1}</span>
                  </div>
                  <h3 className="mt-4 font-semibold text-white">{title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Why it helps */}
        <section className="py-20">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">Study smarter, not longer</h2>
            <div className="mt-12 grid gap-5 md:grid-cols-3">
              {BENEFITS.map(({ icon: Icon, title, text }) => (
                <div key={title} className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 to-slate-950 p-6">
                  <Icon className="h-6 w-6 text-indigo-400" />
                  <h3 className="mt-4 font-semibold text-white">{title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Closing call to action */}
        <section className="px-6 pb-24">
          <div className="mx-auto max-w-4xl rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/80 via-slate-900 to-slate-950 p-10 text-center shadow-2xl shadow-indigo-950/50">
            <h2 className="text-2xl font-bold text-white sm:text-3xl">Every expert started with gaps.</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm text-slate-300">
              Asking for help is how learning works. Let's figure out where to start.
            </p>
            <button
              type="button"
              onClick={onGetStarted}
              className="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-semibold text-indigo-700 shadow-lg transition hover:bg-indigo-50"
            >
              Upload my notes
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </section>
      </main>

      <footer className="relative border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        Kno(w)Hol(e) · Made at HackRU 2026
      </footer>
    </div>
  );
};

export default LandingPage;
