import type {
  AnalyzeResponse,
  AnswerSubmission,
  ApiErrorBody,
  AssessmentResults,
  GraphResponse,
  QuizResponse,
} from './types';

// Override with VITE_API_BASE_URL in frontend/.env.local (e.g. the Render URL in production).
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

/** Error thrown for any non-2xx response. `code` matches the backend's error.code (see API_CONTRACT.md). */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 120_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch (err) {
    if (controller.signal.aborted) {
      throw new ApiError(0, 'timeout', 'The server took too long to respond. Please try again.');
    }
    throw new ApiError(0, 'network_error', `Cannot reach the backend at ${API_BASE_URL}. Is it running?`);
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      res.status,
      body?.error?.code ?? 'http_error',
      body?.error?.message ?? `Request failed with status ${res.status}.`,
      body?.error?.details ?? null,
    );
  }
  return (await res.json()) as T;
}

/** Upload a PDF and build its concept graph. Can take up to ~60 s. */
export function analyzeDocument(file: File): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('file', file);
  return request<AnalyzeResponse>('/api/analyze', { method: 'POST', body: form });
}

export function getGraph(sessionId: string): Promise<GraphResponse> {
  return request<GraphResponse>(`/api/graph/${encodeURIComponent(sessionId)}`);
}

/** First call generates the quiz (can take up to ~60 s); later calls are instant. */
export function getQuiz(sessionId: string): Promise<QuizResponse> {
  return request<QuizResponse>(`/api/quiz/${encodeURIComponent(sessionId)}`);
}

export function submitQuiz(sessionId: string, answers: AnswerSubmission[]): Promise<AssessmentResults> {
  return request<AssessmentResults>(`/api/quiz/${encodeURIComponent(sessionId)}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  });
}

export function getResults(sessionId: string): Promise<AssessmentResults> {
  return request<AssessmentResults>(`/api/results/${encodeURIComponent(sessionId)}`);
}
