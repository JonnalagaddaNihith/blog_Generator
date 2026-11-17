"use client";

import type { FormEvent } from "react";
import { Company } from "@/lib/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Edit, Loader2, Trash2 } from "lucide-react";

export interface CompanyFormData {
  name: string;
  description: string;
  website: string;
}

interface Props {
  company: Company;
  editing: boolean;
  formData: CompanyFormData;
  saving: boolean;
  error: string | null;
  onEdit: () => void;
  onCancelEdit: () => void;
  onFormChange: (data: CompanyFormData) => void;
  onSubmit: (e: FormEvent) => void;
  onDelete: () => void;
}

export function CompanyDetailCard({
  company,
  editing,
  formData,
  saving,
  error,
  onEdit,
  onCancelEdit,
  onFormChange,
  onSubmit,
  onDelete,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{editing ? "Edit Company" : company.name}</CardTitle>
            <CardDescription>
              {editing ? "Update company information" : "Company details and associated projects"}
            </CardDescription>
          </div>
          {!editing && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={onEdit}>
                <Edit className="mr-2 h-4 w-4" /> Edit
              </Button>
              <Button variant="outline" size="sm" onClick={onDelete}>
                <Trash2 className="mr-2 h-4 w-4 text-destructive" /> Delete
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {editing ? (
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Company Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => onFormChange({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                placeholder="https://yourcompany.com"
                value={formData.website}
                onChange={(e) => onFormChange({ ...formData, website: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Brief description of your company..."
                rows={4}
                value={formData.description}
                onChange={(e) => onFormChange({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={onCancelEdit} disabled={saving}>
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
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            {company.website && (
              <div>
                <Label className="text-muted-foreground">Website</Label>
                <p className="mt-1">
                  <a href={company.website} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                    {company.website}
                  </a>
                </p>
              </div>
            )}

            {company.description && (
              <div>
                <Label className="text-muted-foreground">Description</Label>
                <p className="mt-1 text-sm">{company.description}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              <div>
                <Label className="text-muted-foreground">Created</Label>
                <p className="mt-1 text-sm">{new Date(company.created_at).toLocaleDateString()}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Last Updated</Label>
                <p className="mt-1 text-sm">
                  {company.updated_at ? new Date(company.updated_at).toLocaleDateString() : "Never"}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
