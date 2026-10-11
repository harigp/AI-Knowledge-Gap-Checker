import React from 'react';
import { useApp } from '../../context/AppContext';
import type { LearningPathStep } from '../../api/types';

// Steps come from results.learning_path (POST /api/quiz/{session_id}/submit): concepts needing review,
// ordered so prerequisites come first, each with an explanation built from the student's actual scores.
// The backend doesn't recommend specific resources, so each step links to searches for that concept.

const searchLinks = (concept: string) => {
  const q = encodeURIComponent(`${concept} explained`);
  return [
    { label: 'Find Videos', href: `https://www.youtube.com/results?search_query=${q}` },
    { label: 'Find Articles', href: `https://www.google.com/search?q=${q}` },
  ];
};

const masteryBadge = (step: LearningPathStep) => {
  if (step.action === 'verify') return { text: 'Not assessed: check first', cls: 'bg-blue-100 text-blue-800' };
  if (step.mastery === 'weak') return { text: 'Weak', cls: 'bg-red-100 text-red-800' };
  return { text: 'Developing', cls: 'bg-amber-100 text-amber-800' };
};

export const RoadmapView: React.FC = () => {
  const { setStep, results, analysis, setFile, setAnalysis, setResults, setIsQuizCompleted } = useApp();

  const startOver = () => {
    setFile(null);
    setAnalysis(null);
    setResults(null);
    setIsQuizCompleted(false);
    setStep('upload');
  };

  const header = (
    <div className="flex justify-between items-center mb-6 border-b pb-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Your Gap Fix Roadmap</h2>
        <p className="text-gray-600 text-sm">
          {analysis ? `${analysis.document_name} · ` : ''}Personalized sequence to eliminate your identified knowledge gaps.
        </p>
      </div>
      <button
        onClick={startOver}
        className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-100 font-medium transition text-sm"
      >
        &larr; Analyze Another File
      </button>
    </div>
  );

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        {header}
        <div className="p-6 bg-white border rounded-xl shadow-sm text-center">
          <p className="text-gray-600 mb-4">Take the diagnostic quiz to generate your personalized roadmap.</p>
          <button
            onClick={() => setStep(analysis ? 'quiz' : 'upload')}
            className="bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 font-medium transition"
          >
            {analysis ? 'Take Assessment Quiz →' : 'Upload a Document'}
          </button>
        </div>
      </div>
    );
  }

  const { learning_path: path } = results;
  const names = new Map(path.steps.map((s) => [s.concept_id, s.concept_name]));

  return (
    <div className="max-w-4xl mx-auto p-6">
      {header}

      <div className="p-4 mb-6 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-900">
        <p>
          Quiz score: <strong>{results.total_correct}/{results.total_questions}</strong> (
          {Math.round(results.overall_score * 100)}%). {path.summary}
        </p>
      </div>

      {path.steps.length === 0 ? (
        <div className="p-6 bg-white border rounded-xl shadow-sm text-center">
          <p className="text-gray-700 mb-4">Nothing to review — no knowledge gaps were found in the assessed concepts.</p>
          <button
            onClick={() => setStep('graph')}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-100 font-medium transition text-sm"
          >
            Back to Graph
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {path.steps.map((step) => {
            const badge = masteryBadge(step);
            return (
              <div key={step.concept_id} className="p-5 bg-white border rounded-xl shadow-sm flex items-start gap-4">
                <span className="flex items-center justify-center w-8 h-8 shrink-0 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">
                  {step.step}
                </span>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 text-base">{step.concept_name}</h3>
                    <span className={`text-xs font-semibold uppercase px-2 py-0.5 rounded ${badge.cls}`}>{badge.text}</span>
                    {step.score !== null && (
                      <span className="text-xs text-gray-500">&bull; Score {Math.round(step.score * 100)}%</span>
                    )}
                    {step.priority !== null && (
                      <span className="text-xs text-gray-500">&bull; Priority {step.priority}</span>
                    )}
                  </div>
                  {step.prerequisites_in_path.length > 0 && (
                    <p className="text-xs text-gray-500 mb-1">
                      Builds on: {step.prerequisites_in_path.map((id) => names.get(id) ?? id).join(', ')}
                    </p>
                  )}
                  <p className="text-sm text-gray-700">{step.reason}</p>
                </div>
                {/* Inline styles keep the links spaced even when Tailwind classes aren't processed. */}
                <div className="flex flex-col gap-2 shrink-0" style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                  {searchLinks(step.concept_name).map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-blue-600 text-white text-xs px-3.5 py-2 rounded-md font-medium hover:bg-blue-700 transition text-center"
                      style={{ display: 'inline-block' }}
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RoadmapView;
