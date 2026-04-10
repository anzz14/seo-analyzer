import { useCallback, useEffect, useState } from "react";

import api from "@/lib/api";
import { useSSE } from "@/hooks/useSSE";
import type {
  DocumentDetailResponse,
  DocumentResponse,
  ExtractedResultResponse,
  JobResponse,
} from "@/types/document";

interface UseDocumentDetailReturn {
  document: DocumentResponse | null;
  job: JobResponse | null;
  result: ExtractedResultResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useDocumentDetail(documentId: string): UseDocumentDetailReturn {
  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [result, setResult] = useState<ExtractedResultResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get<DocumentDetailResponse>(`/documents/${documentId}`);
      const payload = response.data;

      setDocument(payload);
      setJob(payload.latest_job ?? null);
      setResult(payload.result ?? null);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch document details";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  useSSE(job?.status === "processing" ? job.id : null);

  return {
    document,
    job,
    result,
    isLoading,
    error,
    refetch,
  };
}
