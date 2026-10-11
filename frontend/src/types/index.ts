export interface Concept {
  id: string;
  title: string;
  description: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswerIndex: number;
}

export interface AssessmentResult {
  score: number;
  totalQuestions: number;
  passedConceptIds: string[];
}

export interface LearningRecommendation {
  id: string;
  title: string;
  reason: string;
}

// Defines the steps for app navigation
export type AppStep = 'landing' | 'upload' | 'processing' | 'graph' | 'quiz' | 'roadmap';

// Global state interface
export interface AppState {
  sessionId: string | null;
  concepts: Concept[];
  results: AssessmentResult | null;
  currentStep: AppStep;
}

export type NodeStatus = 'mastered' | 'gap' | 'prerequisite' | 'unassessed';

export interface ConceptNode {
  id: string;
  label: string;
  status: NodeStatus;
  description: string;
}

export interface ConceptEdge {
  id: string;
  source: string;
  target: string;
}

export interface GraphData {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
}