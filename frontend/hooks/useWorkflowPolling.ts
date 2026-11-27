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
    // Defer initial refresh to avoid setState in effect body
    const timer = setTimeout(() => {
      refresh();
    }, 0);

    // Stop polling if paused for human approval or completely finished
    if (status?.is_waiting_approval || status?.is_complete) {
      return () => clearTimeout(timer);
    }

    const intervalTimer = setInterval(refresh, intervalMs);
    return () => {
      clearTimeout(timer);
      clearInterval(intervalTimer);
    };
  }, [refresh, intervalMs, status?.is_waiting_approval, status?.is_complete]);

  return { status, loading, error, refresh };
}