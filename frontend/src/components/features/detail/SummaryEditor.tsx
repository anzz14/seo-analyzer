"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Snackbar, Stack, TextField } from "@mui/material";

import api from "@/lib/api";
import type { ExtractedResultResponse } from "@/types/document";

interface SummaryEditorProps {
  result: ExtractedResultResponse;
  documentId: string;
  onSaved: () => void;
}

export default function SummaryEditor({ result, documentId, onSaved }: SummaryEditorProps) {
  const [value, setValue] = useState("");
  const [initialValue, setInitialValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({
    open: false,
    message: "",
    severity: "success",
  });

  useEffect(() => {
    const baseSummary = result.user_edited_summary ?? result.auto_summary ?? "";
    setValue(baseSummary);
    setInitialValue(baseSummary);
  }, [result.auto_summary, result.user_edited_summary]);

  const isDirty = useMemo(() => value !== initialValue, [initialValue, value]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.patch(`/documents/${documentId}/result`, {
        user_edited_summary: value,
      });
      setInitialValue(value);
      setSnackbar({ open: true, message: "Draft saved", severity: "success" });
      onSaved();
    } catch {
      setSnackbar({ open: true, message: "Failed to save draft", severity: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Stack spacing={2}>
      <TextField
        multiline
        rows={6}
        fullWidth
        value={value}
        disabled={result.is_finalized}
        onChange={(event) => setValue(event.target.value)}
      />

      <Button
        variant="contained"
        onClick={handleSave}
        disabled={result.is_finalized || !isDirty || isSaving}
      >
        Save Draft
      </Button>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={2500}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
      >
        <Alert severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Stack>
  );
}
