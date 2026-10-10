import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/layout/Header';
import { FileUploader } from './components/upload/FileUploader';
import { ProcessingState } from './components/upload/ProcessingState';
import { KnowledgeGraph } from './components/graph/KnowledgeGraph';

export default function App() {
  const { currentStep } = useApp();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      <Header />

      <main className="flex-1 p-6 container mx-auto">
        {currentStep === 'upload' && <FileUploader />}
        {currentStep === 'processing' && <ProcessingState />}
        {currentStep === 'graph' && <KnowledgeGraph />}
        {currentStep === 'quiz' && <div>[ Quiz Screen Placeholder ]</div>}
        {currentStep === 'roadmap' && <div>[ Roadmap Screen Placeholder ]</div>}
      </main>
    </div>
  );
}