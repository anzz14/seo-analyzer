"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {
  Alert,
  AppBar,
  Box,
  Button,
  CircularProgress,
  Container,
  Grid,
  IconButton,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

import JobProgressBar from "@/components/features/dashboard/JobProgressBar";
import FinalizeButton from "@/components/features/detail/FinalizeButton";
import KeywordsTable from "@/components/features/detail/KeywordsTable";
import MetricsPanel from "@/components/features/detail/MetricsPanel";
import SummaryEditor from "@/components/features/detail/SummaryEditor";
import ExportButtons from "@/components/features/export/ExportButtons";
import { useAuth } from "@/context/AuthContext";
import { useDocumentDetail } from "@/hooks/useDocumentDetail";
import api from "@/lib/api";

export default function DocumentDetailPage() {
  const auth = useAuth();
  const router = useRouter();
  const params = useParams();
  const [isRetrying, setIsRetrying] = useState(false);

  const documentId = useMemo(() => {
    const raw = params?.id;
    if (Array.isArray(raw)) {
      return raw[0] ?? "";
    }
    return raw ?? "";
  }, [params]);

  const { document, job, result, isLoading, error, refetch } = useDocumentDetail(documentId);

  useEffect(() => {
    if (!auth || auth.isLoading) {
      return;
    }

    if (!auth.user) {
      router.replace("/login");
    }
  }, [auth, router]);

  if (!auth || auth.isLoading || isLoading) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!auth.user) {
    return null;
  }

  const handleRetry = async () => {
    if (!job?.id) {
      return;
    }

    setIsRetrying(true);
    try {
      await api.post(`/jobs/${job.id}/retry`);
      await refetch();
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ gap: 1 }}>
          <IconButton color="inherit" onClick={() => router.back()} aria-label="Go back">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {document?.original_filename ?? "Document"}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack spacing={3}>
          {error ? <Alert severity="error">{error}</Alert> : null}

          {job?.status === "processing" && job.id ? (
            <Box sx={{ width: "100%" }}>
              <JobProgressBar jobId={job.id} />
            </Box>
          ) : null}

          {job?.status === "failed" ? (
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={handleRetry} disabled={isRetrying}>
                  Retry
                </Button>
              }
            >
              {job.error_message ?? "Analysis failed"}
            </Alert>
          ) : null}

          {!result && job?.status === "completed" ? (
            <Alert severity="warning">Analysis complete but no result found — retry</Alert>
          ) : null}

          {result ? (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 8 }}>
                <Stack spacing={3}>
                  <MetricsPanel
                    wordCount={result.word_count ?? 0}
                    readabilityScore={result.readability_score ?? 0}
                  />
                  <SummaryEditor result={result} documentId={documentId} onSaved={() => void refetch()} />
                  <FinalizeButton result={result} documentId={documentId} onFinalized={() => void refetch()} />
                  {result.is_finalized ? <ExportButtons documentId={documentId} isFinalized /> : null}
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <KeywordsTable keywords={result.primary_keywords ?? []} />
              </Grid>
            </Grid>
          ) : null}
        </Stack>
      </Container>
    </Box>
  );
}
