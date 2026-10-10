// Types mirroring the backend contract (see API_CONTRACT.md / backend/openapi.json).
// Field names are snake_case to match the JSON exactly.

export type Difficulty = 'beginner' | 'intermediate' | 'advanced';
export type SourceType = 'document' | 'inferred';
export type Mastery = 'strong' | 'developing' | 'weak' | 'unassessed';
export type OptionId = 'A' | 'B' | 'C' | 'D';

export interface ApiConcept {
  id: string;
  name: string;
  description: string;
  difficulty: Difficulty;
  prerequisites: string[];
  source_type: SourceType;
  descendant_count: number;
  level: number;
}

export interface ApiEdge {
  id: string;
  source: string;
  target: string;
  relationship: 'prerequisite';
}

export interface ProcessingStatus {
  status: 'completed';
  processing_mode: 'direct' | 'chunked';
  page_count: number;
  estimated_tokens: number;
  chunk_count: number;
  concept_count: number;
  ai_requests_used: number;
  quiz_status: 'pending' | 'ready';
  warnings: string[];
}

export interface AnalyzeResponse {
  session_id: string;
  document_name: string;
  concepts: ApiConcept[];
  edges: ApiEdge[];
  topological_order: string[];
  processing_status: ProcessingStatus;
  expires_at: string;
}

export interface GraphResponse {
  session_id: string;
  document_name: string;
  concepts: ApiConcept[];
  edges: ApiEdge[];
  topological_order: string[];
}

export interface ApiQuizQuestion {
  id: string;
  concept_id: string;
  concept_name: string;
  question: string;
  options: { id: OptionId; text: string }[];
}

export interface QuizResponse {
  session_id: string;
  total_questions: number;
  assessed_concept_ids: string[];
  submitted: boolean;
  questions: ApiQuizQuestion[];
}

export interface AnswerSubmission {
  question_id: string;
  selected_option_id: OptionId;
}

export interface QuestionResult {
  question_id: string;
  concept_id: string;
  question: string;
  selected_option_id: OptionId | null;
  correct_option_id: OptionId;
  is_correct: boolean;
  explanation: string;
}

export interface ConceptScore {
  concept_id: string;
  concept_name: string;
  correct: number;
  total: number;
  score: number | null;
  mastery: Mastery;
}

export interface LearningGap {
  concept_id: string;
  concept_name: string;
  score: number;
  mastery: 'weak' | 'developing';
  descendant_count: number;
  downstream_concept_ids: string[];
  priority: number;
  reason: string;
}

export interface Recommendation {
  rank: number;
  concept_id: string;
  concept_name: string;
  action: 'review' | 'verify';
  score: number | null;
  mastery: Mastery;
  descendant_count: number;
  priority: number | null;
  reason: string;
}

export interface LearningPathStep {
  step: number;
  concept_id: string;
  concept_name: string;
  action: 'review' | 'verify';
  mastery: Mastery;
  score: number | null;
  priority: number | null;
  prerequisites_in_path: string[];
  reason: string;
}

export interface AssessmentResults {
  session_id: string;
  submitted_at: string;
  overall_score: number;
  total_correct: number;
  total_questions: number;
  unanswered_count: number;
  concept_scores: ConceptScore[];
  question_results: QuestionResult[];
  learning_gaps: LearningGap[];
  recommendations: Recommendation[];
  learning_path: { total_steps: number; summary: string; steps: LearningPathStep[] };
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> | null };
}
