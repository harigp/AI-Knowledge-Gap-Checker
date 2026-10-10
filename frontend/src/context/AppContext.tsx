import React, { createContext, useContext, useState, ReactNode } from 'react';
<<<<<<< HEAD
import { AppStep } from '../types';
import type { AnalyzeResponse } from '../api/types';
=======

type Step = 'upload' | 'processing' | 'graph' | 'quiz' | 'roadmap';
>>>>>>> 7a21436 (update)

interface AppContextType {
  currentStep: Step;
  setStep: (step: Step) => void;
  file: File | null;
  setFile: (file: File | null) => void;
<<<<<<< HEAD
  // Result of POST /api/analyze; analysis.session_id is used by the quiz/results calls.
  analysis: AnalyzeResponse | null;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
=======
  isQuizCompleted: boolean;
  setIsQuizCompleted: (completed: boolean) => void;
>>>>>>> 7a21436 (update)
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
<<<<<<< HEAD
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);

  return (
    <AppContext.Provider value={{ currentStep, setStep, file, setFile, analysis, setAnalysis }}>
=======
  const [isQuizCompleted, setIsQuizCompleted] = useState<boolean>(false);

  return (
    <AppContext.Provider 
      value={{ 
        currentStep, 
        setStep: setCurrentStep, 
        file, 
        setFile, 
        isQuizCompleted, 
        setIsQuizCompleted 
      }}
    >
>>>>>>> 7a21436 (update)
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
