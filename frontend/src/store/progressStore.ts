import { create } from "zustand";

interface JobProgressEvent {
  stage: string;
  percentage: number;
  message: string;
}

interface ProgressStoreState {
  progress: Record<string, JobProgressEvent>;
  updateJobProgress: (jobId: string, event: JobProgressEvent) => void;
  clearJobProgress: (jobId: string) => void;
}

export const useProgressStore = create<ProgressStoreState>((set) => ({
  progress: {},
  updateJobProgress: (jobId, event) =>
    set((state) => ({
      progress: {
        ...state.progress,
        [jobId]: event,
      },
    })),
  clearJobProgress: (jobId) =>
    set((state) => {
      const nextProgress = { ...state.progress };
      delete nextProgress[jobId];
      return { progress: nextProgress };
    }),
}));
