import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/layout/Header';
import { FileUploader } from './components/upload/FileUploader';
import { ProcessingState } from './components/upload/ProcessingState';
import { KnowledgeGraph } from './components/graph/KnowledgeGraph';
import { QuizContainer } from './components/quiz/QuizContainer';
import { RoadmapView } from './components/roadmap/RoadmapView';

export default function App() {
  const { currentStep, setFile, setStep } = useApp();

  // The processing screen sends the stored file to POST /api/analyze.
  const handleAnalyze = (file: File) => {
    setFile(file);
    setStep('processing');
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      <Header currentStep={currentStep === 'processing' ? 'upload' : currentStep} onNavigate={setStep} />

      <main className="flex-1 p-6 container mx-auto">
        {currentStep === 'upload' && <FileUploader onAnalyze={handleAnalyze} />}
        {currentStep === 'processing' && <ProcessingState />}
        {currentStep === 'graph' && <KnowledgeGraph />}
        {currentStep === 'quiz' && <QuizContainer />}
        {currentStep === 'roadmap' && <RoadmapView />}
      </main>
    </div>
  );
}