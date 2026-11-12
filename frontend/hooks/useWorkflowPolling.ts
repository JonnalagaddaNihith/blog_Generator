"use client";

import { useState, useEffect, useCallback } from "react";
import { getWorkflowStatus } from "@/lib/api";
import { WorkflowStatusResponse } from "@/lib/types";

export function useWorkflowPolling(projectId: number, intervalMs = 2500) {
  const [status, setStatus] = useState<WorkflowStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getWorkflowStatus(projectId);
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error fetching status");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    refresh();

    // Stop polling if paused for human approval or completely finished
    if (status?.is_waiting_approval || status?.is_complete) {
      return;
    }

    const timer = setInterval(refresh, intervalMs);
    return () => clearInterval(timer);
  }, [refresh, intervalMs, status?.is_waiting_approval, status?.is_complete]);

  return { status, loading, error, refresh };
}