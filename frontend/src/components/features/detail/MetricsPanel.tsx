"use client";

import { Card, CardContent, Grid, LinearProgress, Typography } from "@mui/material";

interface MetricsPanelProps {
  wordCount: number;
  readabilityScore: number;
}

function getReadabilityLabel(score: number): string {
  if (score >= 90) {
    return "Very Easy";
  }
  if (score >= 70) {
    return "Easy";
  }
  if (score >= 50) {
    return "Fairly Easy";
  }
  if (score >= 30) {
    return "Difficult";
  }
  return "Very Difficult";
}

export default function MetricsPanel({ wordCount, readabilityScore }: MetricsPanelProps) {
  const boundedScore = Math.max(0, Math.min(100, readabilityScore));

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Word Count
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700 }}>
              {wordCount.toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Readability Score
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700 }}>
              {boundedScore.toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {getReadabilityLabel(boundedScore)}
            </Typography>
            <LinearProgress variant="determinate" value={boundedScore} />
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
