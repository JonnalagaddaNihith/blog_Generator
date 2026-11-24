"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export interface CompanyFormData {
  name: string;
  description: string;
  website: string;
}

interface Props {
  value: CompanyFormData;
  onChange: (value: CompanyFormData) => void;
  idPrefix?: string;
}

export function CompanyFormFields({ value, onChange, idPrefix = "" }: Props) {
  const id = (name: string) => `${idPrefix}${name}`;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor={id("name")}>Company Name *</Label>
        <Input
          id={id("name")}
          placeholder="e.g., Acme Corporation"
          value={value.name}
          onChange={(e) => onChange({ ...value, name: e.target.value })}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor={id("website")}>Website</Label>
        <Input
          id={id("website")}
          placeholder="https://yourcompany.com"
          value={value.website}
          onChange={(e) => onChange({ ...value, website: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor={id("description")}>Description</Label>
        <Textarea
          id={id("description")}
          placeholder="Brief description of your company, products, or services..."
          rows={4}
          value={value.description}
          onChange={(e) => onChange({ ...value, description: e.target.value })}
        />
      </div>
    </div>
  );
}
