"use client";

import { useState } from "react";
import Link from "next/link";
import DownloadIcon from "@mui/icons-material/Download";
import ReplayIcon from "@mui/icons-material/Replay";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  Box,
  CircularProgress,
  IconButton,
  Pagination,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { useDocumentStore } from "@/store/documentStore";
import type { DocumentResponse } from "@/types/document";
import { useSSE } from "@/hooks/useSSE";
import { downloadDocumentExport } from "@/components/features/export/ExportButtons";
import api from "@/lib/api";

import JobProgressBar from "./JobProgressBar";
import StatusBadge from "./StatusBadge";

type Status = "queued" | "processing" | "completed" | "failed" | "finalized";

interface DocumentTableProps {
  documents: DocumentResponse[];
  isLoading: boolean;
  onRetrySuccess?: () => Promise<void> | void;
}

interface ProcessingProgressCellProps {
  jobId: string | null;
  status: Status;
}

function ProcessingProgressCell({ jobId, status }: ProcessingProgressCellProps) {
  useSSE(status === "processing" ? jobId : null);

  if (status !== "processing" || !jobId) {
    return null;
  }

  return <JobProgressBar jobId={jobId} />;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function formatFileSize(bytes: number): string {
  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }

  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

function normalizeStatus(status: string | undefined): Status {
  if (
    status === "queued" ||
    status === "processing" ||
    status === "completed" ||
    status === "failed" ||
    status === "finalized"
  ) {
    return status;
  }

  return "queued";
}

export default function DocumentTable({ documents, isLoading, onRetrySuccess }: DocumentTableProps) {
  const page = useDocumentStore((state) => state.page);
  const total = useDocumentStore((state) => state.total);
  const pageSize = useDocumentStore((state) => state.pageSize);
  const setPage = useDocumentStore((state) => state.setPage);
  const [retryingJobId, setRetryingJobId] = useState<string | null>(null);

  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const showSkeletons = isLoading && documents.length === 0;

  const handleRetry = async (jobId: string) => {
    setRetryingJobId(jobId);
    try {
      await api.post(`/jobs/${jobId}/retry`);
      if (onRetrySuccess) {
        await onRetrySuccess();
      }
    } finally {
      setRetryingJobId(null);
    }
  };

  return (
    <Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Filename</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {showSkeletons
              ? Array.from({ length: 5 }).map((_, index) => (
                  <TableRow key={`skeleton-${index}`}>
                    <TableCell>
                      <Skeleton variant="text" width="80%" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" width="70%" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" width="45%" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="rounded" width={90} height={24} />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" width="75%" />
                    </TableCell>
                    <TableCell align="right">
                      <Skeleton variant="circular" width={28} height={28} sx={{ ml: "auto" }} />
                    </TableCell>
                  </TableRow>
                ))
              : documents.map((document) => {
                  const status = normalizeStatus(document.latest_job?.status ?? "queued");
                  const jobId = document.latest_job?.id ?? null;

                  return (
                  <TableRow key={document.id} hover>
                    <TableCell>{document.original_filename}</TableCell>
                    <TableCell>{formatTimestamp(document.upload_timestamp)}</TableCell>
                    <TableCell>{formatFileSize(document.file_size)}</TableCell>
                    <TableCell>
                      <StatusBadge status={status} />
                    </TableCell>
                    <TableCell>
                      {status === "processing" ? (
                        <ProcessingProgressCell jobId={jobId} status={status} />
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {status === "finalized" ? (
                        <IconButton
                          aria-label={`Export ${document.original_filename}`}
                          size="small"
                          onClick={() => {
                            void downloadDocumentExport(document.id, "csv");
                          }}
                        >
                          <DownloadIcon fontSize="small" />
                        </IconButton>
                      ) : null}
                      {status === "failed" && jobId ? (
                        <IconButton
                          aria-label={`Retry ${document.original_filename}`}
                          size="small"
                          disabled={retryingJobId === jobId}
                          onClick={() => {
                            void handleRetry(jobId);
                          }}
                        >
                          {retryingJobId === jobId ? (
                            <CircularProgress size={16} />
                          ) : (
                            <ReplayIcon fontSize="small" />
                          )}
                        </IconButton>
                      ) : null}
                      <IconButton
                        aria-label={`View ${document.original_filename}`}
                        component={Link}
                        href={`/documents/${document.id}`}
                        size="small"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );})}
          </TableBody>
        </Table>
      </TableContainer>

      {!showSkeletons && documents.length === 0 ? (
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          No documents found.
        </Typography>
      ) : null}

      <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
        <Pagination
          color="primary"
          count={pageCount}
          page={page}
          onChange={(_, value) => setPage(value)}
        />
      </Box>
    </Box>
  );
}
