import type { VariantProps } from "class-variance-authority";
import type { WorkflowStatusResponse } from "@/lib/types";
import { badgeVariants } from "@/components/ui/badge";

export function getProjectStatusBadge(
  status: WorkflowStatusResponse | undefined
): { label: string; variant: NonNullable<VariantProps<typeof badgeVariants>["variant"]> } {
  if (!status) {
    return { label: "Loading...", variant: "secondary" };
  }

  if (status.is_complete) {
    return { label: "Completed", variant: "default" };
  }

  if (status.is_waiting_approval) {
    return { label: "Waiting Approval", variant: "secondary" };
  }

  if (status.outline?.outline && status.outline.outline.length > 0) {
    if (status.blog_content) {
      return { label: "Generated", variant: "secondary" };
    }
    return { label: "Outline Ready", variant: "outline" };
  }

  return { label: "Draft", variant: "secondary" };
}

export function isProjectCompleted(status: WorkflowStatusResponse | undefined): boolean {
  return status?.is_complete === true && status?.approval_status === "approved";
}
