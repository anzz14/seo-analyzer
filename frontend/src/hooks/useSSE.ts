import { useEffect } from "react";

import { useDocuments } from "@/hooks/useDocuments";
import { useProgressStore } from "@/store/progressStore";

interface ProgressEventPayload {
  stage: string;
  percentage: number;
  message?: string;
}

const TERMINAL_STAGES = new Set(["job_completed", "job_failed"]);

export function useSSE(jobId: string | null) {
  const updateJobProgress = useProgressStore((state) => state.updateJobProgress);
  const { refetch } = useDocuments({ enablePolling: false });

  useEffect(() => {
    if (!jobId || typeof window === "undefined") {
      return;
    }

    const token = localStorage.getItem("seo_jwt");
    if (!token) {
      return;
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const streamUrl = `${baseUrl}/jobs/${jobId}/progress/stream?token=${encodeURIComponent(token)}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as ProgressEventPayload;
        const normalizedStage = TERMINAL_STAGES.has(parsed.stage) ? parsed.stage : "processing";
        const normalized = {
          stage: normalizedStage,
          percentage: parsed.percentage,
          message: parsed.message ?? "",
        };

        updateJobProgress(jobId, normalized);

        if (TERMINAL_STAGES.has(parsed.stage)) {
          eventSource.close();
          void refetch(false);
        }
      } catch {
        // Ignore malformed SSE payloads.
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId, refetch, updateJobProgress]);
}
