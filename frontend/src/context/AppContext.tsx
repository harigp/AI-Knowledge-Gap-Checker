import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AppStep } from '../types';
import type { AnalyzeResponse, AssessmentResults } from '../api/types';

interface AppContextType {
  currentStep: AppStep;
  setStep: (step: AppStep) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  // Result of POST /api/analyze; analysis.session_id is used by the quiz/results calls.
  analysis: AnalyzeResponse | null;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
  isQuizCompleted: boolean;
  setIsQuizCompleted: (completed: boolean) => void;
  // Result of POST /api/quiz/{session_id}/submit: scores, gaps, recommendations, learning path.
  results: AssessmentResults | null;
  setResults: (results: AssessmentResults | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [currentStep, setCurrentStep] = useState<AppStep>('landing');
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [isQuizCompleted, setIsQuizCompleted] = useState<boolean>(false);
  const [results, setResults] = useState<AssessmentResults | null>(null);

  return (
    <AppContext.Provider
      value={{
        currentStep,
        setStep: setCurrentStep,
        file,
        setFile,
        analysis,
        setAnalysis,
        isQuizCompleted,
        setIsQuizCompleted,
        results,
        setResults,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
