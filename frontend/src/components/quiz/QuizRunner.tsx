import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';

interface Question {
  id: number;
  concept: string;
  questionText: string;
  options: string[];
  correctAnswer: number;
}

const mockQuestions: Question[] = [
  {
    id: 1,
    concept: 'Eigenvalues & Eigenvectors',
    questionText: 'What represents an eigenvector of a square matrix A?',
    options: [
      'A non-zero vector v such that Av = λv for some scalar λ',
      'The determinant of matrix A',
      'The diagonal sum of matrix A',
      'A vector that always yields zero when multiplied by A'
    ],
    correctAnswer: 0,
  },
  {
    id: 2,
    concept: 'Principal Component Analysis (PCA)',
    questionText: 'In PCA, what do the principal components represent?',
    options: [
      'Random linear combinations of features',
      'Orthogonal directions of maximum variance in the data',
      'The inverse of the covariance matrix',
      'The mean values of each feature vector'
    ],
    correctAnswer: 1,
  },
];

export const QuizRunner: React.FC = () => {
  const { setStep } = useApp();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  const currentQ = mockQuestions[currentIndex];

  const handleSelect = (index: number) => {
    setSelectedOption(index);
  };

  const handleNext = () => {
    if (selectedOption === currentQ.correctAnswer) {
      setScore((prev) => prev + 1);
    }

    if (currentIndex + 1 < mockQuestions.length) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOption(null);
    } else {
      setIsCompleted(true);
    }
  };

  if (isCompleted) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center border rounded-xl bg-white shadow-sm my-10">
        <h2 className="text-2xl font-bold mb-2">Assessment Complete!</h2>
        <p className="text-gray-600 mb-4">
          You scored <strong>{score}</strong> out of <strong>{mockQuestions.length}</strong>.
        </p>
        <button
          onClick={() => setStep('roadmap')}
          className="bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 font-medium transition"
        >
          View Learning Roadmap &rarr;
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 border rounded-xl bg-white shadow-sm my-8">
      <div className="flex justify-between items-center mb-4 pb-2 border-b">
        <span className="text-xs font-semibold px-2.5 py-1 bg-blue-100 text-blue-800 rounded uppercase">
          Gap Check: {currentQ.concept}
        </span>
        <span className="text-sm text-gray-500">
          Question {currentIndex + 1} of {mockQuestions.length}
        </span>
      </div>

      <h3 className="text-lg font-bold text-gray-900 mb-4">{currentQ.questionText}</h3>

      <div className="space-y-3 mb-6">
        {currentQ.options.map((option, idx) => (
          <button
            key={idx}
            onClick={() => handleSelect(idx)}
            className={`w-text text-left w-full p-3.5 rounded-lg border transition font-medium text-sm ${
              selectedOption === idx
                ? 'border-blue-600 bg-blue-50 text-blue-900'
                : 'border-gray-200 hover:bg-gray-50 text-gray-700'
            }`}
          >
            {option}
          </button>
        ))}
      </div>

      <button
        onClick={handleNext}
        disabled={selectedOption === null}
        className={`w-full py-2.5 rounded-lg text-white font-medium transition ${
          selectedOption !== null
            ? 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
            : 'bg-gray-300 cursor-not-allowed'
        }`}
      >
        {currentIndex + 1 === mockQuestions.length ? 'Submit Quiz' : 'Next Question'}
      </button>
    </div>
  );
};

export default QuizRunner;