"use client";

import { useMemo, useState } from "react";
import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";

import api from "@/lib/api";
import type { ExtractedResultResponse } from "@/types/document";

interface FinalizeButtonProps {
  result: ExtractedResultResponse | null | undefined;
  documentId: string;
  onFinalized: () => void;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

export default function FinalizeButton({ result, documentId, onFinalized }: FinalizeButtonProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const disabled = useMemo(() => {
    return !result || result.is_finalized || !result.auto_summary;
  }, [result]);

  if (result?.is_finalized) {
    return <Chip color="success" label={`✓ Finalized ${formatDate(result.finalized_at)}`} />;
  }

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      await api.post(`/documents/${documentId}/finalize`);
      setIsDialogOpen(false);
      onFinalized();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Button
        variant="contained"
        color="success"
        disabled={disabled || isSubmitting}
        onClick={() => setIsDialogOpen(true)}
      >
        Finalize
      </Button>

      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)}>
        <DialogTitle>Finalize Result</DialogTitle>
        <DialogContent>
          <Typography>Are you sure? This cannot be undone.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsDialogOpen(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button color="success" variant="contained" onClick={handleConfirm} disabled={isSubmitting}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
