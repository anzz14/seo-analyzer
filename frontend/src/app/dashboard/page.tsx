"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import LogoutIcon from "@mui/icons-material/Logout";
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

import DocumentTable from "@/components/features/dashboard/DocumentTable";
import FilterBar from "@/components/features/dashboard/FilterBar";
import UploadZone from "@/components/features/upload/UploadZone";
import { useAuth } from "@/context/AuthContext";
import { useDocuments } from "@/hooks/useDocuments";
import { useDocumentStore } from "@/store/documentStore";

export default function DashboardPage() {
  const auth = useAuth();
  const router = useRouter();
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const documents = useDocumentStore((state) => state.documents);
  const isLoading = useDocumentStore((state) => state.isLoading);
  const { refetch } = useDocuments();

  useEffect(() => {
    if (!auth || auth.isLoading) {
      return;
    }

    if (!auth.user) {
      router.replace("/login");
    }
  }, [auth, router]);

  if (!auth || auth.isLoading) {
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

  const handleUploadComplete = async () => {
    setIsUploadOpen(false);
    await refetch();
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              SEO Analyzer
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {auth.user.email}
            </Typography>
          </Box>

          <IconButton color="inherit" aria-label="Logout" onClick={auth.logout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack spacing={3}>
          <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", gap: 2 }}>
            <Typography variant="h5">My Documents</Typography>
            <Button variant="contained" onClick={() => setIsUploadOpen(true)}>
              Upload Files
            </Button>
          </Stack>

          <FilterBar />

          <DocumentTable documents={documents} isLoading={isLoading} onRetrySuccess={refetch} />
        </Stack>
      </Container>

      <Dialog
        open={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Upload Files</DialogTitle>
        <DialogContent>
          <UploadZone onUploadComplete={handleUploadComplete} />
        </DialogContent>
      </Dialog>
    </Box>
  );
}
