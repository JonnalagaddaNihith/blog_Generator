"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { createCompany } from "@/lib/api";
import type { Company } from "@/lib/types";
import { CompanyFormFields, type CompanyFormData } from "./CompanyFormFields";

const EMPTY_FORM: CompanyFormData = { name: "", description: "", website: "" };

interface Props {
  trigger: ReactNode;
  onCreated: (company: Company) => void;
}

export function CreateCompanyDialog({ trigger, onCreated }: Props) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState<CompanyFormData>(EMPTY_FORM);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setCreating(true);
    try {
      const created = await createCompany(formData);
      setFormData(EMPTY_FORM);
      setOpen(false);
      onCreated(created);
    } catch (err) {
      console.error("Failed to create company:", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Company</DialogTitle>
          <DialogDescription>Add your company to manage blog projects</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <CompanyFormFields value={formData} onChange={setFormData} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={creating}>
              {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Create"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
