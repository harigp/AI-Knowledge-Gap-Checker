import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, HelpCircle, Loader2 } from 'lucide-react';

export interface QuizQuestion {
  id: string;
  concept_id: string;
  question: string;
  options: string[];
}

interface QuizRunnerProps {
  questions: QuizQuestion[];
  onSubmit: (answers: Record<string, string>) => Promise<void> | void;
  isSubmitting?: boolean;
}

export const QuizRunner: React.FC<QuizRunnerProps> = ({
  questions,
  onSubmit,
  isSubmitting = false,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

  const currentQ = questions[currentIndex];
  const progressPercent = ((currentIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentIndex === questions.length - 1;
  const totalAnswered = Object.keys(selectedAnswers).length;

  const handleSelectOption = (option: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [currentQ.id]: option,
    }));
  };

  const handleNext = () => {
    if (!isLastQuestion) setCurrentIndex((i) => i + 1);
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1);
  };

  if (!questions || questions.length === 0) {
    return (
      <div className="text-center py-16 text-slate-400">
        No assessment questions available.
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      {/* Quiz Progress Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
            Diagnostic Assessment
          </span>
          <h2 className="text-xl font-bold text-white">
            Question {currentIndex + 1} of {questions.length}
          </h2>
        </div>
        <div className="text-right">
          <span className="text-xs font-medium text-slate-400">
            {totalAnswered} of {questions.length} answered
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Question Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl backdrop-blur-md">
        <div className="mb-6 flex items-start gap-3">
          <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            <HelpCircle className="h-4 w-4" />
          </div>
          <p className="text-lg font-medium leading-snug text-slate-100">
            {currentQ.question}
          </p>
        </div>

        {/* Option Radio Cards */}
        <div className="space-y-3">
          {currentQ.options.map((option, idx) => {
            const isSelected = selectedAnswers[currentQ.id] === option;
            const letter = String.fromCharCode(65 + idx);

            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectOption(option)}
                className={`flex w-full items-center gap-4 rounded-xl border p-4 text-left transition-all ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-500/15 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-500'
                    : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/60'
                }`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition-all ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {letter}
                </div>
                <span className={`text-sm ${isSelected ? 'font-medium text-white' : 'text-slate-300'}`}>
                  {option}
                </span>
              </button>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div className="mt-8 flex items-center justify-between border-t border-slate-800/80 pt-6">
          <button
            type="button"
            disabled={currentIndex === 0 || isSubmitting}
            onClick={handlePrev}
            className="flex items-center gap-2 rounded-xl border border-slate-800 px-4 py-2.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="h-4 w-4" />
            Previous
          </button>

          {isLastQuestion ? (
            <button
              type="button"
              disabled={isSubmitting || totalAnswered < questions.length}
              onClick={() => onSubmit(selectedAnswers)}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-teal-500/20 hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing Gaps...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  Submit Assessment
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500"
            >
              Next
              <ArrowRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
