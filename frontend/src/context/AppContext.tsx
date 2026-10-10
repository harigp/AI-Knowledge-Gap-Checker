import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AppStep } from '../types';

interface AppContextType {
  currentStep: AppStep;
  setStep: (step: AppStep) => void;
  file: File | null;
  setFile: (file: File | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentStep, setStep] = useState<AppStep>('upload');
  const [file, setFile] = useState<File | null>(null);

  return (
    <AppContext.Provider value={{ currentStep, setStep, file, setFile }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};