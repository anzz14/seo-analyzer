"use client";

import { Box, LinearProgress, Typography } from "@mui/material";

import { useProgressStore } from "@/store/progressStore";

interface JobProgressBarProps {
  jobId: string;
}

export default function JobProgressBar({ jobId }: JobProgressBarProps) {
  const progressEvent = useProgressStore((state) => state.progress[jobId]);

  if (!progressEvent || progressEvent.stage !== "processing") {
    return null;
  }

  const boundedValue = Math.max(0, Math.min(100, progressEvent.percentage));

  return (
    <Box sx={{ minWidth: 180 }}>
      <LinearProgress variant="determinate" value={boundedValue} />
      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
        {progressEvent.message}
      </Typography>
    </Box>
  );
}