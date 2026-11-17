"use client";

import type { FormEvent } from "react";
import { Project } from "@/lib/types";
import { TONE_OPTIONS } from "@/components/projects/ProjectFormFields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";

export interface ProjectEditFormData {
  target_word_count: number;
  audience: string;
  tone: string;
}

interface Props {
  open: boolean;
  project: Project | null;
  formData: ProjectEditFormData;
  saving: boolean;
  onOpenChange: (open: boolean) => void;
  onFormChange: (data: ProjectEditFormData) => void;
  onSubmit: (e: FormEvent) => void;
}

export function ProjectEditDialog({
  open,
  project,
  formData,
  saving,
  onOpenChange,
  onFormChange,
  onSubmit,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Project</DialogTitle>
          <DialogDescription>
            Update project settings for &quot;{project?.topic}&quot;
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="target_word_count">Target Word Count</Label>
            <Input
              id="target_word_count"
              type="number"
              min="100"
              max="10000"
              value={formData.target_word_count}
              onChange={(e) => onFormChange({ ...formData, target_word_count: parseInt(e.target.value) || 500 })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tone">Content Tone</Label>
            <Select
              value={formData.tone}
              onValueChange={(val) => onFormChange({ ...formData, tone: val })}
            >
              <SelectTrigger id="tone">
                <SelectValue placeholder="Select tone" />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience">Target Audience</Label>
            <Input
              id="audience"
              placeholder="e.g., Software Engineers, CTOs, Founders"
              value={formData.audience}
              onChange={(e) => onFormChange({ ...formData, audience: e.target.value })}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
