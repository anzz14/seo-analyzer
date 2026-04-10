"use client";

import Link from "next/link";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  Box,
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

import StatusBadge from "./StatusBadge";

type Status = "queued" | "processing" | "completed" | "failed" | "finalized";

interface DocumentTableProps {
  documents: DocumentResponse[];
  isLoading: boolean;
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

export default function DocumentTable({ documents, isLoading }: DocumentTableProps) {
  const page = useDocumentStore((state) => state.page);
  const total = useDocumentStore((state) => state.total);
  const pageSize = useDocumentStore((state) => state.pageSize);
  const setPage = useDocumentStore((state) => state.setPage);

  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const showSkeletons = isLoading && documents.length === 0;

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
                    <TableCell align="right">
                      <Skeleton variant="circular" width={28} height={28} sx={{ ml: "auto" }} />
                    </TableCell>
                  </TableRow>
                ))
              : documents.map((document) => (
                  <TableRow key={document.id} hover>
                    <TableCell>{document.original_filename}</TableCell>
                    <TableCell>{formatTimestamp(document.upload_timestamp)}</TableCell>
                    <TableCell>{formatFileSize(document.file_size)}</TableCell>
                    <TableCell>
                      <StatusBadge status={normalizeStatus(document.latest_job?.status ?? "queued")} />
                    </TableCell>
                    <TableCell align="right">
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
                ))}
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
