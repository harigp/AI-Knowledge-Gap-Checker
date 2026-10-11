import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, Loader2, Sparkles, AlertCircle } from 'lucide-react';

interface FileUploaderProps {
  onAnalyze: (file: File) => Promise<void> | void;
  isProcessing?: boolean;
}

const PROCESSING_STEPS = [
  'Extracting text from PDF...',
  'Gemini analyzing concepts & definitions...',
  'Mapping prerequisite dependencies...',
  'Generating diagnostic questions...',
];

export const FileUploader: React.FC<FileUploaderProps> = ({ onAnalyze, isProcessing = false }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stepIdx, setStepIdx] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File | undefined) => {
    setError(null);
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      setError('Please upload a valid PDF document.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;
    setError(null);

    // Simulate animated step transitions during backend processing
    const interval = setInterval(() => {
      setStepIdx((prev) => (prev < PROCESSING_STEPS.length - 1 ? prev + 1 : prev));
    }, 1800);

    try {
      await onAnalyze(selectedFile);
    } catch (err: any) {
      setError(err?.message || 'Failed to process document.');
    } finally {
      clearInterval(interval);
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl">
      {/* Title Header */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
          Prerequisite-Aware Gap Detection
        </div>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          Discover Your Learning Gaps
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Upload your lecture notes or study guide. We'll identify your missing foundational concepts.
        </p>
      </div>

      {/* Main Upload Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl">
        {isProcessing ? (
          /* Processing State */
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="relative mb-6">
              <div className="h-20 w-20 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center text-indigo-400">
                <Loader2 className="h-8 w-8 animate-pulse" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-white">Analyzing Your Course Material</h3>
            <p className="mt-2 text-sm text-indigo-400 animate-pulse font-medium">
              {PROCESSING_STEPS[stepIdx]}
            </p>
            <div className="mt-6 flex gap-2">
              {PROCESSING_STEPS.map((_, i) => (
                <div
                  key={i}
                  className={`h-1.5 w-8 rounded-full transition-all duration-500 ${
                    i <= stepIdx ? 'bg-indigo-500' : 'bg-slate-800'
                  }`}
                />
              ))}
            </div>
          </div>
        ) : (
          /* Normal File Dropzone */
          <>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-all cursor-pointer ${
                isDragOver
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-slate-700 bg-slate-950/40 hover:border-indigo-500/50 hover:bg-slate-900/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => handleFileChange(e.target.files?.[0])}
              />

              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
                <UploadCloud className="h-7 w-7" />
              </div>

              <p className="mt-4 text-sm font-medium text-white">
                Drag and drop your PDF here, or <span className="text-indigo-400 underline">browse</span>
              </p>
              <p className="mt-1 text-xs text-slate-400">Text-based PDF notes up to 10 MB</p>
            </div>

            {error && (
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-2.5 text-xs text-rose-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {selectedFile && (
              <div className="mt-4 flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950/60 p-3.5">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-indigo-400" />
                  <div className="text-left">
                    <p className="text-sm font-medium text-white truncate max-w-xs">{selectedFile.name}</p>
                    <p className="text-xs text-slate-400">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              </div>
            )}

            <button
              type="button"
              disabled={!selectedFile}
              onClick={startAnalysis}
              className={`mt-6 w-full rounded-xl py-3.5 text-sm font-semibold tracking-wide text-white transition-all shadow-lg ${
                selectedFile
                  ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:brightness-110 active:scale-[0.99] shadow-indigo-500/25'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              Analyze My Knowledge Map
            </button>
          </>
        )}
      </div>
    </div>
  );
};