"use client";

import { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
} from "@mui/material";

import type { KeywordMetric } from "@/types/document";

type SortKey = "keyword" | "count" | "density";
type SortDirection = "asc" | "desc";

interface KeywordsTableProps {
  keywords: Array<{ keyword: string; count: number; density: number }>;
}

function compareValues(a: KeywordMetric, b: KeywordMetric, key: SortKey, direction: SortDirection): number {
  let value = 0;

  if (key === "keyword") {
    value = a.keyword.localeCompare(b.keyword);
  }
  if (key === "count") {
    value = a.count - b.count;
  }
  if (key === "density") {
    value = a.density - b.density;
  }

  return direction === "asc" ? value : -value;
}

export default function KeywordsTable({ keywords }: KeywordsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("count");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const rows = useMemo(() => {
    return [...keywords].sort((a, b) => compareValues(a, b, sortKey, sortDirection)).slice(0, 10);
  }, [keywords, sortDirection, sortKey]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setSortKey(key);
    setSortDirection(key === "count" ? "desc" : "asc");
  };

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>
              <TableSortLabel
                active={sortKey === "keyword"}
                direction={sortKey === "keyword" ? sortDirection : "asc"}
                onClick={() => handleSort("keyword")}
              >
                Keyword
              </TableSortLabel>
            </TableCell>
            <TableCell align="right">
              <TableSortLabel
                active={sortKey === "count"}
                direction={sortKey === "count" ? sortDirection : "desc"}
                onClick={() => handleSort("count")}
              >
                Count
              </TableSortLabel>
            </TableCell>
            <TableCell align="right">
              <TableSortLabel
                active={sortKey === "density"}
                direction={sortKey === "density" ? sortDirection : "desc"}
                onClick={() => handleSort("density")}
              >
                Density (%)
              </TableSortLabel>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.keyword} hover>
              <TableCell>{row.keyword}</TableCell>
              <TableCell align="right">{row.count}</TableCell>
              <TableCell align="right">{row.density.toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
