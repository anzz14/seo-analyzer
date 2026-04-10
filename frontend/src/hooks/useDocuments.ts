import { useCallback, useEffect, useRef } from "react";

import api from "@/lib/api";
import { useDocumentStore } from "@/store/documentStore";
import type { DocumentResponse } from "@/types/document";

interface DocumentsListResponse {
  items: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export function useDocuments() {
  const filters = useDocumentStore((state) => state.filters);
  const page = useDocumentStore((state) => state.page);
  const pageSize = useDocumentStore((state) => state.pageSize);
  const setDocuments = useDocumentStore((state) => state.setDocuments);
  const setLoading = useDocumentStore((state) => state.setLoading);
  const setError = useDocumentStore((state) => state.setError);

  const refetch = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    try {
      const response = await api.get<DocumentsListResponse>("/documents", {
        params: {
          page,
          page_size: pageSize,
          search: filters.search,
          status: filters.status,
          sort_by: filters.sortBy,
          sort_order: filters.sortOrder,
        },
      });

      setDocuments(response.data.items, response.data.total);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch documents";
      setError(message);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [filters, page, pageSize, setDocuments, setError, setLoading]);

  const refetchRef = useRef(refetch);

  useEffect(() => {
    refetchRef.current = refetch;
  }, [refetch]);

  useEffect(() => {
    void refetchRef.current();

    const intervalId = setInterval(() => {
      void refetchRef.current(false);
    }, 5000);

    return () => {
      clearInterval(intervalId);
    };
  }, [filters, page]);

  return { refetch };
}
