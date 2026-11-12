"use client";

import { useState, Suspense, use, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useWorkflowPolling } from "@/hooks/useWorkflowPolling";
import { resumeWorkflow, getProject, getCompany } from "@/lib/api";
import { Project, Company } from "@/lib/types";
import { PipelineStepper } from "@/components/workflow/PipelineStepper";
import { OutlineReviewCard } from "@/components/workflow/OutlineReviewCard";
import { FinalReviewTabs } from "@/components/workflow/FinalReviewTabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Home, Building2 } from "lucide-react";
import { toast } from "sonner";

function ProjectWorkflowContent({ projectId }: { projectId: number }) {
  const router = useRouter();
  const { status, loading, error, refresh } = useWorkflowPolling(projectId);
  const [submitting, setSubmitting] = useState(false);
  const [project, setProject] = useState<Project | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  useEffect(() => {
    loadProjectAndCompany();
  }, [projectId]);

  const loadProjectAndCompany = async () => {
    try {
      const projectData = await getProject(projectId);
      setProject(projectData);
      if (projectData.company_id) {
        const companyData = await getCompany(projectData.company_id);
        setCompany(companyData);
      }
    } catch (err) {
      console.error("Failed to load project/company:", err);
    }
  };

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
    setWorkflowError(null);
    try {
      await resumeWorkflow(projectId, payload);
      const notifyAndReload = (title: string, description: string) => {
        toast.success(title, { description });
        setTimeout(() => window.location.reload(), 800);
      };
      if (payload.action === "regenerate") {
        const section = payload.regenerate_section || "all";
        notifyAndReload(
          section === "all" ? "Article regenerated" : `${section.replace("_", " ")} regenerated`,
          "Reloading to show the updated content…"
        );
        return;
      }
      if (payload.action === "approve") {
        // Approving the outline runs the whole pipeline (writing, SEO,
        // quality, fact-check) and pauses at the final review gate.
        if (status?.approval_stage === "blog_strategy") {
          notifyAndReload(
            "Article generated",
            "Blog content, SEO, quality & fact-check are ready — reloading…"
          );
          return;
        }
        // Approving the final review completes the workflow.
        if (status?.approval_stage === "final_review") {
          notifyAndReload("Blog finalized", "Reloading to show the final version…");
          return;
        }
      }
      await refresh();
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : "Failed to resume workflow");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-5xl space-y-6 py-8">
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/" className="flex items-center gap-1.5">
                <Home className="h-4 w-4" />
              </Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          {company && (
            <>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link href="/companies">Companies</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link
                    href={`/companies/${company.id}`}
                    className="flex items-center gap-1"
                  >
                    <Building2 className="h-4 w-4" />
                    {company.name}
                  </Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
            </>
          )}
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{project?.topic || `Project #${projectId}`}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">
          {project?.topic || `Project #${projectId}`}
        </h1>
      </div>

      <PipelineStepper
        currentStage={status.current_stage}
        isWaitingApproval={status.is_waiting_approval}
        isComplete={status.is_complete}
      />

      {workflowError && (
        <Alert variant="destructive">
          <AlertDescription>{workflowError}</AlertDescription>
        </Alert>
      )}

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
          onRefresh={refresh}
          projectId={projectId}
        />
      )}
    </div>
  );
}

export default function ProjectWorkflowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const projectId = Number(id);

  return (
    <Suspense fallback={
      <div className="container mx-auto max-w-5xl space-y-4 py-8">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    }>
      <ProjectWorkflowContent projectId={projectId} />
    </Suspense>
  );
}