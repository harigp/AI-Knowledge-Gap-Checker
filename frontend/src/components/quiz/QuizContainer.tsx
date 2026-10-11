import React, { useEffect, useRef, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ApiError, getQuiz, getResults, submitQuiz } from '../../api/client';
import type { ApiQuizQuestion, AssessmentResults, OptionId } from '../../api/types';
import { QuizRunner, type QuizQuestion } from './QuizRunner';

// Loads the quiz from the backend, renders the presentational QuizRunner, and submits answers for grading.
// QuizRunner works with option text; the backend expects option IDs (A-D), so we map between them here.
export const QuizContainer: React.FC = () => {
  const { analysis, setStep, setResults, setIsQuizCompleted } = useApp();
  const [apiQuestions, setApiQuestions] = useState<ApiQuizQuestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const loadedFor = useRef<string | null>(null); // StrictMode runs effects twice in dev; fetch once

  const sessionId = analysis?.session_id;

  const finish = (graded: AssessmentResults) => {
    setResults(graded);
    setIsQuizCompleted(true);
    setStep('roadmap');
  };

  useEffect(() => {
    if (!sessionId) return;
    const key = `${sessionId}:${attempt}`;
    if (loadedFor.current === key) return;
    loadedFor.current = key;

    setError(null);
    getQuiz(sessionId)
      .then(async (quiz) => {
        if (quiz.submitted) {
          finish(await getResults(sessionId));
          return;
        }
        setApiQuestions(quiz.questions);
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Could not load the quiz.'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, attempt]);

  const handleSubmit = async (answers: Record<string, string>) => {
    if (!sessionId || !apiQuestions) return;
    const submission = apiQuestions.flatMap((q) => {
      const chosen = q.options.find((o) => o.text === answers[q.id]);
      return chosen ? [{ question_id: q.id, selected_option_id: chosen.id as OptionId }] : [];
    });
    setSubmitting(true);
    setError(null);
    try {
      finish(await submitQuiz(sessionId, submission));
    } catch (err: unknown) {
      if (err instanceof ApiError && err.code === 'already_submitted') {
        finish(await getResults(sessionId));
      } else {
        setError(err instanceof ApiError ? err.message : 'Could not submit your answers.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!analysis) {
    return (
      <div className="mx-auto max-w-xl text-center py-16">
        <p className="text-slate-400 mb-4">Upload a document first to generate a quiz.</p>
        <button onClick={() => setStep('upload')} className="rounded-lg bg-indigo-600 px-5 py-2.5 text-white">
          Upload a Document
        </button>
      </div>
    );
  }

  if (error && !apiQuestions) {
    return (
      <div className="mx-auto max-w-xl text-center py-16">
        <p className="text-rose-400 mb-4">{error}</p>
        <button onClick={() => setAttempt((a) => a + 1)} className="rounded-lg bg-indigo-600 px-5 py-2.5 text-white">
          Try Again
        </button>
      </div>
    );
  }

  if (!apiQuestions) {
    return (
      <div className="mx-auto max-w-xl text-center py-16">
        <h2 className="text-xl font-bold mb-2">Preparing your diagnostic quiz...</h2>
        <p className="text-slate-400">Generating questions from {analysis.document_name}. This can take up to a minute.</p>
      </div>
    );
  }

  const questions: QuizQuestion[] = apiQuestions.map((q) => ({
    id: q.id,
    concept_id: q.concept_id,
    question: q.question,
    options: q.options.map((o) => o.text),
  }));

  return (
    <>
      {error && <p className="mx-auto max-w-2xl mb-4 text-sm text-rose-400">{error}</p>}
      <QuizRunner questions={questions} onSubmit={handleSubmit} isSubmitting={submitting} />
    </>
  );
};

export default QuizContainer;
