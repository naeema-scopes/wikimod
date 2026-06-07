/**
 * API client for WikiMod backend.
 */

import axios from "axios";
import type {
  AnalysisResponse,
  HistoryEntry,
  ModelMetrics,
  ModelLimitations,
} from "../types";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000,
});

export async function analyzeUrl(
  wikipediaUrl: string
): Promise<AnalysisResponse> {
  const response = await api.post<AnalysisResponse>("/analyze", {
    wikipedia_url: wikipediaUrl,
  });
  return response.data;
}

export async function getAnalysis(id: string): Promise<AnalysisResponse> {
  const response = await api.get<AnalysisResponse>(`/analyze/${id}`);
  return response.data;
}

export async function getHistory(limit = 50): Promise<HistoryEntry[]> {
  const response = await api.get<HistoryEntry[]>("/history", {
    params: { limit },
  });
  return response.data;
}

export async function getPageHistory(
  pageTitle: string
): Promise<HistoryEntry[]> {
  const response = await api.get<HistoryEntry[]>(
    `/history/${encodeURIComponent(pageTitle)}`
  );
  return response.data;
}

export async function getModelMetrics(): Promise<ModelMetrics> {
  const response = await api.get<ModelMetrics>("/model/metrics");
  return response.data;
}

export async function getModelLimitations(): Promise<ModelLimitations> {
  const response = await api.get<ModelLimitations>("/model/limitations");
  return response.data;
}

export default api;
