import React from 'react';
import { Network, Upload, HelpCircle, Compass, CheckCircle2 } from 'lucide-react';

interface HeaderProps {
  currentStep: 'upload' | 'graph' | 'quiz' | 'roadmap';
  onNavigate?: (step: 'upload' | 'graph' | 'quiz' | 'roadmap') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentStep, onNavigate }) => {
  const steps = [
    { id: 'upload', label: '1. Upload Notes', icon: Upload },
    { id: 'graph', label: '2. Knowledge Map', icon: Network },
    { id: 'quiz', label: '3. Diagnostic Quiz', icon: HelpCircle },
    { id: 'roadmap', label: '4. Action Roadmap', icon: Compass },
  ] as const;

  const getStepIndex = (step: string) => steps.findIndex((s) => s.id === step);
  const activeIdx = getStepIndex(currentStep);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
        
        {/* Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">Kno(w)Hol(e)</span>
              <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-medium tracking-wide text-indigo-400">
              </span>
            </div>
            <p className="text-xs text-slate-400">Discover What You Don't Know</p>
          </div>
        </div>

        {/* Workflow Stepper */}
        <nav className="hidden items-center gap-1 md:flex">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = idx < activeIdx;
            const isCurrent = idx === activeIdx;

            return (
              <React.Fragment key={step.id}>
                <button
                  type="button"
                  disabled={!onNavigate || idx > activeIdx}
                  onClick={() => onNavigate?.(step.id)}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                    isCurrent
                      ? 'border border-indigo-500/40 bg-indigo-500/15 text-indigo-300 shadow-sm'
                      : isCompleted
                      ? 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                      : 'cursor-not-allowed text-slate-600'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <Icon className="h-3.5 w-3.5" />
                  )}
                  <span>{step.label}</span>
                </button>

                {idx < steps.length - 1 && (
                  <span className="mx-1 text-slate-700">/</span>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      </div>
    </header>
  );
};