import React from 'react';
import { useApp } from '../../context/AppContext';

interface ActionStep {
  id: number;
  topic: string;
  type: 'Video' | 'Article' | 'Exercise';
  title: string;
  duration: string;
  link: string;
}

const mockRoadmapSteps: ActionStep[] = [
  {
    id: 1,
    topic: 'Eigenvalues & Eigenvectors',
    type: 'Video',
    title: '3Blue1Brown: Essence of Linear Algebra (Ch. 14)',
    duration: '17 mins',
    link: 'https://youtube.com',
  },
  {
    id: 2,
    topic: 'Eigenvalues & Eigenvectors',
    type: 'Exercise',
    title: 'Practice: Computing Determinants & Characteristic Polynomials',
    duration: '25 mins',
    link: '#',
  },
  {
    id: 3,
    topic: 'Principal Component Analysis (PCA)',
    type: 'Article',
    title: 'A Step-by-Step Intuitive Guide to PCA',
    duration: '12 mins',
    link: '#',
  },
];

export const RoadmapView: React.FC = () => {
  const { setStep } = useApp();

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Your Gap Fix Roadmap</h2>
          <p className="text-gray-600 text-sm">Personalized sequence to eliminate your identified knowledge gaps.</p>
        </div>
        <button
          onClick={() => setStep('upload')}
          className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-100 font-medium transition text-sm"
        >
          &larr; Analyze Another File
        </button>
      </div>

      <div className="space-y-4">
        {mockRoadmapSteps.map((step, index) => (
          <div key={step.id} className="p-5 bg-white border rounded-xl shadow-sm flex items-start gap-4">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">
              {index + 1}
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                  {step.topic}
                </span>
                <span className="text-xs text-gray-400">&bull; {step.duration}</span>
              </div>
              <h3 className="font-semibold text-gray-900 text-base">{step.title}</h3>
            </div>
            <a
              href={step.link}
              target="_blank"
              rel="noreferrer"
              className="bg-blue-600 text-white text-xs px-3.5 py-2 rounded-md font-medium hover:bg-blue-700 transition"
            >
              Start {step.type}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RoadmapView;