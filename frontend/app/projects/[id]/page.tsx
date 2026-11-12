"use client";

import { useState, use } from "react";
import { useWorkflowPolling } from "@/hooks/useWorkflowPolling";
import { resumeWorkflow } from "@/lib/api";
import { PipelineStepper } from "@/components/workflow/PipelineStepper";
import { OutlineReviewCard } from "@/components/workflow/OutlineReviewCard";
import { FinalReviewTabs } from "@/components/workflow/FinalReviewTabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ProjectWorkflowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const projectId = Number(id);
  const { status, loading, error, refresh } = useWorkflowPolling(projectId);
  const [submitting, setSubmitting] = useState(false);

  if (loading && !status) {
    return (
      <div className="container mx-auto max-w-5xl space-y-4 py-8">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="container mx-auto max-w-5xl py-8">
        <Alert variant="destructive">
          <AlertDescription>{error || "Workflow not found"}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleResume = async (payload: Parameters<typeof resumeWorkflow>[1]) => {
    setSubmitting(true);
    try {
      await resumeWorkflow(projectId, payload);
      await refresh();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-5xl space-y-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Project #{projectId} Studio</h1>
      </div>

      <PipelineStepper
        currentStage={status.current_stage}
        isWaitingApproval={status.is_waiting_approval}
        isComplete={status.is_complete}
      />

      {status.current_stage === "blog_strategy_approval" && status.is_waiting_approval && (
        <OutlineReviewCard
          strategy={status.outline?.strategy}
          initialOutline={status.outline?.outline || []}
          submitting={submitting}
          onApprove={(updated_outline) => handleResume({ action: "approve", updated_outline })}
          onRegenerate={() => handleResume({ action: "regenerate", regenerate_section: "outline" })}
        />
      )}

      {(status.current_stage === "final_approval" || status.is_complete) && (
        <FinalReviewTabs
          status={status}
          submitting={submitting}
          onApproveFinal={() => handleResume({ action: "approve" })}
          onRegenerateSection={(regenerate_section) =>
            handleResume({ action: "regenerate", regenerate_section })
          }
        />
      )}
    </div>
  );
}