import React from 'react';
import { Network } from 'lucide-react'; // 1. Import icon

interface HeaderProps {
  currentStep?: 'upload' | 'graph' | 'quiz' | 'results';
}

export const Header: React.FC<HeaderProps> = ({ currentStep = 'upload' }) => {
  return (
    <header className="bg-white border-b border-slate-200 py-4 px-8 flex items-center justify-between">
      {/* Left: Branding */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-600 rounded-lg text-white">
          <Network className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-indigo-600 text-lg">ConceptGraph AI</h1>
          <p className="text-xs text-slate-500">Discover What You Don't Know</p>
        </div>
      </div>

      {/* Right: Workflow Steps */}
      <div className="flex gap-2 text-xs font-medium">
        <span className={currentStep === 'upload' ? 'text-indigo-600 font-bold' : 'text-slate-400'}>1. Upload</span>
        <span className={currentStep === 'graph' ? 'text-indigo-600 font-bold' : 'text-slate-400'}>2. Graph</span>
        <span className={currentStep === 'quiz' ? 'text-indigo-600 font-bold' : 'text-slate-400'}>3. Quiz</span>
        <span className={currentStep === 'results' ? 'text-indigo-600 font-bold' : 'text-slate-400'}>4. Roadmap</span>
      </div>
    </header>
  );
};