"use client";

import { useId, useState } from "react";
import { Alert, Box, LinearProgress, Stack, Typography } from "@mui/material";

import api from "@/lib/api";
import type { UploadResponse } from "@/types/document";

interface UploadZoneProps {
  onUploadComplete?: (results: UploadResponse[]) => void;
}

const MAX_UPLOAD_SIZE_BYTES = 5_242_880;

export default function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const inputId = useId();
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const validateFiles = (files: File[]): File[] => {
    const errors: string[] = [];
    const validFiles: File[] = [];

    for (const file of files) {
      if (file.type !== "text/plain") {
        errors.push(`${file.name}: only .txt files are allowed`);
        continue;
      }

      if (file.size > MAX_UPLOAD_SIZE_BYTES) {
        errors.push(`${file.name}: file is larger than 5MB`);
        continue;
      }

      validFiles.push(file);
    }

    setValidationErrors(errors);
    return validFiles;
  };

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) {
      return;
    }

    const validFiles = validateFiles(files);
    if (validFiles.length === 0) {
      return;
    }

    setError(null);
    setUploadProgress(0);

    const formData = new FormData();
    for (const file of validFiles) {
      formData.append("files", file);
    }

    try {
      const response = await api.post<UploadResponse[]>("/documents/upload", formData, {
        onUploadProgress: (event) => {
          if (!event.total) {
            setUploadProgress(null);
            return;
          }

          const progress = Math.round((event.loaded * 100) / event.total);
          setUploadProgress(progress);
        },
      });

      setUploadProgress(100);
      onUploadComplete?.(response.data);
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err
          ? "Upload failed. Please try again."
          : "Unexpected error while uploading files.";
      setError(message);
      setUploadProgress(null);
    }
  };

  const handleInputChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files ? Array.from(event.target.files) : [];
    await uploadFiles(files);
    event.target.value = "";
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    await uploadFiles(files);
  };

  return (
    <Stack spacing={2}>
      <Box
        component="label"
        htmlFor={inputId}
        sx={{
          border: "2px dashed",
          borderColor: "primary.main",
          borderRadius: 2,
          p: 4,
          textAlign: "center",
          cursor: "pointer",
          display: "block",
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <Typography>Drag & drop .txt files here, or click to browse</Typography>

        <input
          id={inputId}
          type="file"
          multiple
          accept=".txt"
          style={{
            position: "absolute",
            width: 1,
            height: 1,
            padding: 0,
            margin: -1,
            overflow: "hidden",
            clip: "rect(0, 0, 0, 0)",
            border: 0,
          }}
          onChange={handleInputChange}
        />
      </Box>

      {uploadProgress !== null ? <LinearProgress variant="determinate" value={uploadProgress} /> : null}

      {validationErrors.map((msg) => (
        <Alert key={msg} severity="warning">
          {msg}
        </Alert>
      ))}

      {error ? <Alert severity="error">{error}</Alert> : null}
    </Stack>
  );
}
