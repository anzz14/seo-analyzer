import { Chip } from "@mui/material";

type Status = "queued" | "processing" | "completed" | "failed" | "finalized";

interface StatusBadgeProps {
  status: Status;
}

const STATUS_CONFIG: Record<Status, { color: "default" | "info" | "success" | "error" | "primary"; label: string }> = {
  queued: {
    color: "default",
    label: "Queued",
  },
  processing: {
    color: "info",
    label: "Processing",
  },
  completed: {
    color: "success",
    label: "Completed",
  },
  failed: {
    color: "error",
    label: "Failed",
  },
  finalized: {
    color: "primary",
    label: "Finalized",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const { color, label } = STATUS_CONFIG[status];

  return <Chip size="small" color={color} label={label} />;
}
