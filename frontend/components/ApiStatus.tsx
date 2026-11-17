"use client";

import { useEffect, useState } from "react";
import { toApiState, type ApiState } from "@/lib/status";

const LABELS: Record<ApiState, string> = {
  checking: "Checking…",
  online: "Backend and database connected",
  offline: "Backend not reachable",
};

export default function ApiStatus() {
  const [state, setState] = useState<ApiState>("checking");

  useEffect(() => {
    fetch("/api/health/ready")
      .then((r) => setState(toApiState(r.ok)))
      .catch(() => setState(toApiState(false)));
  }, []);

  return (
    <p role="status" className="rounded-full bg-sage px-4 py-2 text-sm text-deep">
      {LABELS[state]}
    </p>
  );
}
