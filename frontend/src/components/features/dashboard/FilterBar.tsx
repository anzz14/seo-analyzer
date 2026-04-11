"use client";

import { useEffect, useMemo, useState } from "react";
import SearchIcon from "@mui/icons-material/Search";
import {
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material";

import { useDocumentStore } from "@/store/documentStore";

type SortOption = "newest" | "oldest" | "filename_asc";

const SORT_MAP: Record<SortOption, { sortBy: string; sortOrder: string }> = {
  newest: { sortBy: "created_at", sortOrder: "desc" },
  oldest: { sortBy: "created_at", sortOrder: "asc" },
  filename_asc: { sortBy: "original_filename", sortOrder: "asc" },
};

function getSortOption(sortBy: string, sortOrder: string): SortOption {
  if (sortBy === "created_at" && sortOrder === "asc") {
    return "oldest";
  }
  if (sortBy === "original_filename" && sortOrder === "asc") {
    return "filename_asc";
  }
  return "newest";
}

export default function FilterBar() {
  const filters = useDocumentStore((state) => state.filters);
  const setFilters = useDocumentStore((state) => state.setFilters);

  const [searchInput, setSearchInput] = useState(filters.search);

  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchInput !== filters.search) {
        setFilters({ search: searchInput });
      }
    }, 300);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [filters.search, searchInput, setFilters]);

  const selectedSort = useMemo(
    () => getSortOption(filters.sortBy, filters.sortOrder),
    [filters.sortBy, filters.sortOrder],
  );

  return (
    <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
      <TextField
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
        placeholder="Search documents"
        size="small"
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
      />

      <FormControl size="small" sx={{ minWidth: 180 }}>
        <InputLabel id="status-filter-label">Status</InputLabel>
        <Select
          labelId="status-filter-label"
          label="Status"
          value={filters.status}
          onChange={(event) => setFilters({ status: event.target.value })}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="queued">Queued</MenuItem>
          <MenuItem value="processing">Processing</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
          <MenuItem value="failed">Failed</MenuItem>
          <MenuItem value="finalized">Finalized</MenuItem>
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 200 }}>
        <InputLabel id="sort-filter-label">Sort</InputLabel>
        <Select
          labelId="sort-filter-label"
          label="Sort"
          value={selectedSort}
          onChange={(event) => {
            const value = event.target.value as SortOption;
            const mapped = SORT_MAP[value];
            setFilters({ sortBy: mapped.sortBy, sortOrder: mapped.sortOrder });
          }}
        >
          <MenuItem value="newest">Newest first</MenuItem>
          <MenuItem value="oldest">Oldest first</MenuItem>
          <MenuItem value="filename_asc">Filename A-Z</MenuItem>
        </Select>
      </FormControl>
    </Stack>
  );
}
