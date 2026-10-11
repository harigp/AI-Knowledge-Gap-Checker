import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';

export const FileUploader: React.FC = () => {
  const { setFile, setStep } = useApp();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const allowedTypes = ['.pdf']; // backend accepts text-based PDFs only (max 10 MB, 50 pages)

  const validateAndSetFile = (file: File) => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(extension)) {
      setError(`Invalid file type. Please upload ${allowedTypes.join(', ')}`);
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleAnalyze = () => {
    if (selectedFile) {
      setFile(selectedFile);
      setStep('processing');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '40px auto', padding: '20px', textAlign: 'center' }}>
      <h2>Upload Syllabus or Study Notes</h2>
      <p>Upload a PDF to analyze knowledge gaps.</p>

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: dragActive ? '2px dashed #7457f6' : '2px dashed #cbd0de',
          borderRadius: '8px',
          padding: '40px',
          cursor: 'pointer',
          backgroundColor: dragActive ? '#f3f2ff' : '#ffffff',
          margin: '20px 0',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        <p>{selectedFile ? `Selected: ${selectedFile.name}` : 'Drag & drop your file here, or click to browse'}</p>
        <small style={{ color: '#6b7287' }}>Supported format: PDF with selectable text (max 10 MB, 50 pages)</small>
      </div>

      {error && <p style={{ color: 'red', marginBottom: '15px' }}>{error}</p>}

      <button
        onClick={handleAnalyze}
        disabled={!selectedFile}
        style={{
          padding: '10px 24px',
          fontSize: '16px',
          backgroundColor: selectedFile ? '#5f3ded' : '#cbd0de',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          cursor: selectedFile ? 'pointer' : 'not-allowed',
        }}
      >
        Analyze Knowledge Gaps
      </button>
    </div>
  );
};
