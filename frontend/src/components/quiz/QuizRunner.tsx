import React, { useEffect, useRef, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ApiError, getQuiz, getResults, submitQuiz } from '../../api/client';
import type { ApiQuizQuestion, OptionId } from '../../api/types';

// Questions come from GET /api/quiz/{session_id} (generated from the uploaded document on first call).
// Correct answers never reach the browser: answers are graded by POST /api/quiz/{session_id}/submit.
export const QuizRunner: React.FC = () => {
  const { setStep, analysis, setIsQuizCompleted, results, setResults } = useApp();
  const [questions, setQuestions] = useState<ApiQuizQuestion[] | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, OptionId>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0); // bump to retry loading
  const loadedFor = useRef<string | null>(null); // StrictMode runs effects twice in dev; fetch once

  const sessionId = analysis?.session_id;

  useEffect(() => {
    if (!sessionId || results) return;
    const key = `${sessionId}:${attempt}`;
    if (loadedFor.current === key) return;
    loadedFor.current = key;

    setError(null);
    getQuiz(sessionId)
      .then((quiz) => {
        if (quiz.submitted) {
          // Already graded (e.g. after a reload of this screen): show the saved results.
          return getResults(sessionId).then((saved) => {
            setResults(saved);
            setIsQuizCompleted(true);
          });
        }
        setQuestions(quiz.questions);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : 'Could not load the quiz.');
      });
  }, [sessionId, results, attempt, setResults, setIsQuizCompleted]);

  const handleSubmit = async () => {
    if (!sessionId || !questions) return;
    setSubmitting(true);
    setError(null);
    try {
      const graded = await submitQuiz(
        sessionId,
        questions
          .filter((q) => answers[q.id])
          .map((q) => ({ question_id: q.id, selected_option_id: answers[q.id] })),
      );
      setResults(graded);
      setIsQuizCompleted(true);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.code === 'already_submitted') {
        const saved = await getResults(sessionId);
        setResults(saved);
        setIsQuizCompleted(true);
      } else {
        setError(err instanceof ApiError ? err.message : 'Could not submit your answers.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!analysis) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center border rounded-xl bg-white shadow-sm my-10">
        <p className="text-gray-600 mb-4">Upload a document first to generate a quiz.</p>
        <button onClick={() => setStep('upload')} className="bg-blue-600 text-white px-6 py-2.5 rounded-lg">
          Upload a Document
        </button>
      </div>
    );
  }

  if (results) {
    const pct = Math.round(results.overall_score * 100);
    return (
      <div className="max-w-xl mx-auto p-6 text-center border rounded-xl bg-white shadow-sm my-10">
        <h2 className="text-2xl font-bold mb-2">Assessment Complete!</h2>
        <p className="text-gray-600 mb-2">
          You scored <strong>{results.total_correct}</strong> out of <strong>{results.total_questions}</strong> ({pct}%).
        </p>
        <p className="text-gray-600 mb-4">
          {results.learning_gaps.length
            ? `We found ${results.learning_gaps.length} potential knowledge gap${results.learning_gaps.length > 1 ? 's' : ''}.`
            : 'No knowledge gaps detected in the assessed concepts.'}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => setStep('graph')}
            className="border border-gray-300 text-gray-700 px-6 py-2.5 rounded-lg hover:bg-gray-100 font-medium transition"
          >
            View Graph
          </button>
          <button
            onClick={() => setStep('roadmap')}
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 font-medium transition"
          >
            View Learning Roadmap &rarr;
          </button>
        </div>
      </div>
    );
  }

  if (error && !questions) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center border rounded-xl bg-white shadow-sm my-10">
        <h2 className="text-xl font-bold mb-2">Couldn't load the quiz</h2>
        <p className="text-red-700 mb-4">{error}</p>
        <button onClick={() => setAttempt((a) => a + 1)} className="bg-blue-600 text-white px-6 py-2.5 rounded-lg">
          Try Again
        </button>
      </div>
    );
  }

  if (!questions) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center border rounded-xl bg-white shadow-sm my-10">
        <h2 className="text-xl font-bold mb-2">Preparing your diagnostic quiz...</h2>
        <p className="text-gray-600">Generating questions from {analysis.document_name}. This can take up to a minute.</p>
      </div>
    );
  }

  const currentQ = questions[currentIndex];
  const selected = answers[currentQ.id] ?? null;
  const isLast = currentIndex + 1 === questions.length;

  const handleNext = () => {
    if (isLast) {
      void handleSubmit();
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 border rounded-xl bg-white shadow-sm my-8">
      <div className="flex justify-between items-center mb-4 pb-2 border-b">
        <span className="text-xs font-semibold px-2.5 py-1 bg-blue-100 text-blue-800 rounded uppercase">
          Gap Check: {currentQ.concept_name}
        </span>
        <span className="text-sm text-gray-500">
          Question {currentIndex + 1} of {questions.length}
        </span>
      </div>

      <h3 className="text-lg font-bold text-gray-900 mb-4">{currentQ.question}</h3>

      <div className="space-y-3 mb-6">
        {currentQ.options.map((option) => (
          <button
            key={option.id}
            onClick={() => setAnswers((prev) => ({ ...prev, [currentQ.id]: option.id }))}
            className={`w-full text-left p-3.5 rounded-lg border transition font-medium text-sm ${
              selected === option.id
                ? 'border-blue-600 bg-blue-50 text-blue-900'
                : 'border-gray-200 hover:bg-gray-50 text-gray-700'
            }`}
          >
            {option.id}. {option.text}
          </button>
        ))}
      </div>

      {error && <p className="text-red-700 text-sm mb-3">{error}</p>}

      <div className="flex gap-3">
        {currentIndex > 0 && (
          <button
            onClick={() => setCurrentIndex((prev) => prev - 1)}
            disabled={submitting}
            className="py-2.5 px-5 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50"
          >
            Back
          </button>
        )}
        <button
          onClick={handleNext}
          disabled={selected === null || submitting}
          className={`flex-1 py-2.5 rounded-lg text-white font-medium transition ${
            selected !== null && !submitting
              ? 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              : 'bg-gray-300 cursor-not-allowed'
          }`}
        >
          {submitting ? 'Grading...' : isLast ? 'Submit Quiz' : 'Next Question'}
        </button>
      </div>
    </div>
  );
};

export default QuizRunner;
