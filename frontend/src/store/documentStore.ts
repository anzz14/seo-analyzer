import { create } from "zustand";

import type { DocumentResponse } from "@/types/document";

interface DocumentFilters {
  search: string;
  status: string;
  sortBy: string;
  sortOrder: string;
}

interface DocumentStoreState {
  documents: DocumentResponse[];
  total: number;
  page: number;
  pageSize: number;
  filters: DocumentFilters;
  isLoading: boolean;
  error: string | null;
  setDocuments: (items: DocumentResponse[], total: number) => void;
  setFilters: (filters: Partial<DocumentFilters>) => void;
  setPage: (page: number) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
}

export const useDocumentStore = create<DocumentStoreState>((set) => ({
  documents: [],
  total: 0,
  page: 1,
  pageSize: 20,
  filters: {
    search: "",
    status: "",
    sortBy: "created_at",
    sortOrder: "desc",
  },
  isLoading: false,
  error: null,
  setDocuments: (items, total) =>
    set({
      documents: items,
      total,
    }),
  setFilters: (filters) =>
    set((state) => ({
      filters: {
        ...state.filters,
        ...filters,
      },
      page: 1,
    })),
  setPage: (page) => set({ page }),
  setLoading: (v) => set({ isLoading: v }),
  setError: (e) => set({ error: e }),
}));
