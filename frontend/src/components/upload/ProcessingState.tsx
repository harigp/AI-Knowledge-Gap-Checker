import React, { useEffect, useRef, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { analyzeDocument, ApiError } from '../../api/client';

// Shown while POST /api/analyze runs (typically 5-30 s). Messages advance on a timer for feedback;
// the step only changes when the backend actually responds.
const STAGES = [
  { at: 0, progress: 10, message: 'Extracting text content...' },
  { at: 2000, progress: 35, message: 'Identifying key concepts & topics...' },
  { at: 6000, progress: 60, message: 'Building knowledge graph relationships...' },
  { at: 15000, progress: 80, message: 'Still working — larger documents take a bit longer...' },
  { at: 35000, progress: 90, message: 'Almost there...' },
];

export const ProcessingState: React.FC = () => {
  const { file, setStep, setAnalysis } = useApp();
  const [progress, setProgress] = useState(STAGES[0].progress);
  const [statusMessage, setStatusMessage] = useState(STAGES[0].message);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false); // StrictMode runs effects twice in dev; upload only once

  useEffect(() => {
    if (!file) {
      setStep('upload');
      return;
    }
    if (started.current) return;
    started.current = true;

    const timers = STAGES.slice(1).map((stage) =>
      setTimeout(() => {
        setProgress(stage.progress);
        setStatusMessage(stage.message);
      }, stage.at),
    );
    const clearTimers = () => timers.forEach(clearTimeout);

    analyzeDocument(file)
      .then((result) => {
        clearTimers();
        setAnalysis(result);
        setProgress(100);
        setStatusMessage(`Analysis complete! Found ${result.concepts.length} concepts.`);
        setTimeout(() => setStep('graph'), 600);
      })
      .catch((err: unknown) => {
        clearTimers();
        setError(err instanceof ApiError ? err.message : 'Something went wrong while analyzing the document.');
      });
  }, [file, setStep, setAnalysis]);

  if (error) {
    return (
      <div style={{ maxWidth: '500px', margin: '60px auto', padding: '20px', textAlign: 'center' }}>
        <h2>Analysis Failed</h2>
        <p style={{ color: '#b91c1c', margin: '16px 0' }}>{error}</p>
        <button
          onClick={() => setStep('upload')}
          style={{ padding: '10px 24px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          Try Another File
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '500px', margin: '60px auto', padding: '20px', textAlign: 'center' }}>
      <h2>Analyzing Document</h2>
      <p style={{ color: '#555' }}>Processing: <strong>{file?.name || 'Uploaded document'}</strong></p>

      <div style={{ width: '100%', backgroundColor: '#e5e7eb', borderRadius: '8px', height: '12px', margin: '24px 0', overflow: 'hidden' }}>
        <div
          style={{
            width: `${progress}%`,
            backgroundColor: '#2563eb',
            height: '100%',
            transition: 'width 0.4s ease-in-out',
          }}
        />
      </div>

      <p style={{ fontStyle: 'italic', color: '#4b5563' }}>{statusMessage}</p>
    </div>
  );
};
