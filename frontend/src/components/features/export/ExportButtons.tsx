"use client";

import DownloadIcon from "@mui/icons-material/Download";
import { Button, Stack } from "@mui/material";

import api from "@/lib/api";

type ExportFormat = "json" | "csv";

export async function downloadDocumentExport(documentId: string, format: ExportFormat): Promise<void> {
  let blob: Blob;
  let filename: string;

  if (format === "json") {
    const response = await api.get(`/documents/${documentId}/export?format=json`);
    blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
    filename = `${documentId}.json`;
  } else {
    const response = await api.get(`/documents/${documentId}/export?format=csv`, {
      responseType: "blob",
    });
    blob = response.data as Blob;
    filename = `${documentId}.csv`;
  }

  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

interface ExportButtonsProps {
  documentId: string;
  isFinalized: boolean;
}

export default function ExportButtons({ documentId, isFinalized }: ExportButtonsProps) {
  return (
    <Stack direction="row" gap={1}>
      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        disabled={!isFinalized}
        onClick={() => {
          void downloadDocumentExport(documentId, "json");
        }}
      >
        Export JSON
      </Button>
      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        disabled={!isFinalized}
        onClick={() => {
          void downloadDocumentExport(documentId, "csv");
        }}
      >
        Export CSV
      </Button>
    </Stack>
  );
}