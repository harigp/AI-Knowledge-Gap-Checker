import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Concept, AssessmentResult, AppStep } from '../types';

interface AppContextType {
  sessionId: string | null;
  concepts: Concept[];
  results: AssessmentResult | null;
  currentStep: AppStep;
  setSessionId: (id: string | null) => void;
  setConcepts: (concepts: Concept[]) => void;
  setResults: (results: AssessmentResult | null) => void;
  setCurrentStep: (step: AppStep) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [results, setResults] = useState<AssessmentResult | null>(null);
  const [currentStep, setCurrentStep] = useState<AppStep>('upload');

  return (
    <AppContext.Provider
      value={{
        sessionId,
        concepts,
        results,
        currentStep,
        setSessionId,
        setConcepts,
        setResults,
        setCurrentStep,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};