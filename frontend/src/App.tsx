import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/layout/Header';
import { FileUploader } from './components/upload/FileUploader';
import { ProcessingState } from './components/upload/ProcessingState';
import { KnowledgeGraph } from './components/graph/KnowledgeGraph';
import { QuizRunner } from './components/quiz/QuizRunner';
import { RoadmapView } from './components/roadmap/RoadmapView';

export default function App() {
  const appContext = useApp();
  const { currentStep } = appContext;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      <Header currentStep={currentStep as any} />

      <main className="flex-1 p-6 container mx-auto">
        {currentStep === 'upload' && <FileUploader {...(appContext as any)} />}
        {currentStep === 'processing' && <ProcessingState {...(appContext as any)} />}
        {currentStep === 'graph' && <KnowledgeGraph {...(appContext as any)} />}
        {currentStep === 'quiz' && <QuizRunner {...(appContext as any)} />}
        {currentStep === 'roadmap' && <RoadmapView {...(appContext as any)} />}
      </main>
    </div>
  );
}