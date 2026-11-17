"use client";

import type { FormEvent } from "react";
import { ProjectFormData, ProjectFormFields } from "@/components/projects/ProjectFormFields";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Loader2, Plus } from "lucide-react";

interface Props {
  open: boolean;
  companyName: string;
  formData: ProjectFormData;
  creating: boolean;
  onOpenChange: (open: boolean) => void;
  onFormChange: (data: ProjectFormData) => void;
  onSubmit: (e: FormEvent) => void;
}

export function NewProjectDialog({
  open,
  companyName,
  formData,
  creating,
  onOpenChange,
  onFormChange,
  onSubmit,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Project</DialogTitle>
          <DialogDescription>
            Create a blog project for &quot;{companyName}&quot;
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <ProjectFormFields value={formData} onChange={onFormChange} idPrefix="create_" />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={creating}>
              Cancel
            </Button>
            <Button type="submit" disabled={creating}>
              {creating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Starting...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" /> Create & Start
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
