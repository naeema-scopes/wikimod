/**
 * React hook for managing analysis state.
 */

import { useState, useCallback } from "react";
import type { AnalysisResponse } from "../types";
import { analyzeUrl, getAnalysis } from "../api/client";

interface UseAnalysisReturn {
  analysis: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
  submitUrl: (url: string) => Promise<void>;
  loadAnalysis: (id: string) => Promise<void>;
  reset: () => void;
}

export function useAnalysis(): UseAnalysisReturn {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitUrl = useCallback(async (url: string) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const result = await analyzeUrl(url);
      setAnalysis(result);
    } catch (err: any) {
      if (err.response?.status === 422) {
        setError("Please enter a valid Wikipedia URL.");
      } else if (err.response?.status === 429) {
        setError("Rate limit exceeded. Please wait a moment and try again.");
      } else if (err.response?.status === 404) {
        setError(
          err.response?.data?.detail || "Talk page not found for this article."
        );
      } else {
        setError("An error occurred while analyzing the page. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadAnalysis = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await getAnalysis(id);
      setAnalysis(result);
    } catch (err: any) {
      setError("Could not load the analysis. It may have been deleted.");
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setAnalysis(null);
    setError(null);
    setLoading(false);
  }, []);

  return { analysis, loading, error, submitUrl, loadAnalysis, reset };
}
