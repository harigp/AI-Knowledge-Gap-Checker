import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AppStep } from '../types';
import type { AnalyzeResponse } from '../api/types';

interface AppContextType {
  currentStep: Step;
  setStep: (step: Step) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  // Result of POST /api/analyze; analysis.session_id is used by the quiz/results calls.
  analysis: AnalyzeResponse | null;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);

  return (
    <AppContext.Provider value={{ currentStep, setStep, file, setFile, analysis, setAnalysis }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
