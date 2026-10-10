import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/layout/Header'; // Developer 1's component

export default function App() {
  const { currentStep } = useApp();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      <Header />
      
      <main className="flex-1 p-6 container mx-auto">
        {currentStep === 'upload' && <div>[ Upload Screen Placeholder ]</div>}
        {currentStep === 'graph' && <div>[ Knowledge Graph View Placeholder ]</div>}
        {currentStep === 'quiz' && <div>[ Quiz Screen Placeholder ]</div>}
        {currentStep === 'results' && <div>[ Results Screen Placeholder ]</div>}
      </main>
    </div>
  );
}