/**
 * TypeScript interfaces matching backend Pydantic schemas.
 */

export interface CommentResponse {
  id: string;
  author: string | null;
  text: string;
  timestamp: string | null;
  toxicity_score: number;
  is_toxic: boolean;
  trigger_words: string[];
  section_title: string | null;
}

export interface HealthScoreResponse {
  score: number;
  total_comments: number;
  toxic_count: number;
  clean_count: number;
  label: string;
}

export interface EscalationDataPoint {
  index: number;
  toxicity_score: number;
  comment_preview: string;
  author: string | null;
}

export interface SectionEscalation {
  section_title: string;
  trend: "escalating" | "stable" | "de-escalating" | "insufficient_data";
  slope: number;
  data_points: EscalationDataPoint[];
}

export interface EscalationReport {
  sections: SectionEscalation[];
  overall_trend: string;
}

export interface AnalysisResponse {
  id: string;
  wikipedia_url: string;
  page_title: string;
  health_score: HealthScoreResponse;
  comments: CommentResponse[];
  escalation: EscalationReport | null;
  scanned_at: string;
}

export interface HistoryEntry {
  id: string;
  wikipedia_url: string;
  page_title: string;
  health_score: number;
  total_comments: number;
  toxic_count: number;
  scanned_at: string;
}

export interface ModelMetrics {
  accuracy: number;
  precision_toxic: number;
  recall_toxic: number;
  f1_toxic: number;
  precision_clean: number;
  recall_clean: number;
  f1_clean: number;
  weighted_f1: number;
  confusion_matrix: number[][];
  training_samples: number;
  note: string;
}

export interface ModelLimitations {
  limitations: string[];
  references: string[];
}
