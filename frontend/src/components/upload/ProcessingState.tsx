import React, { useEffect, useState } from 'react';
import { useApp } from '../../context/AppContext';

export const ProcessingState: React.FC = () => {
  const { file, setStep } = useApp();
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Extracting text content...');

  useEffect(() => {
    const timer1 = setTimeout(() => {
      setProgress(35);
      setStatusMessage('Identifying key concepts & topics...');
    }, 1200);

    const timer2 = setTimeout(() => {
      setProgress(70);
      setStatusMessage('Building knowledge graph relationships...');
    }, 2500);

    const timer3 = setTimeout(() => {
      setProgress(100);
      setStatusMessage('Analysis complete!');
    }, 3800);

    const timer4 = setTimeout(() => {
      setStep('graph');
    }, 4500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [setStep]);

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