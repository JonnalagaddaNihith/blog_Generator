"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const TONE_OPTIONS = [
  { value: "Professional yet engaging", label: "Professional & Engaging" },
  { value: "Technical and authoritative", label: "Technical & Authoritative" },
  { value: "Casual and conversational", label: "Casual & Conversational" },
  { value: "Persuasive and marketing-focused", label: "Persuasive & Marketing" },
] as const;

export interface ProjectFormData {
  topic: string;
  target_word_count: number;
  audience: string;
  tone: string;
}

interface Props {
  value: ProjectFormData;
  onChange: (value: ProjectFormData) => void;
  idPrefix?: string;
}

export function ProjectFormFields({ value, onChange, idPrefix = "" }: Props) {
  const id = (name: string) => `${idPrefix}${name}`;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor={id("topic")}>Blog Topic / Working Title *</Label>
        <Input
          id={id("topic")}
          placeholder="e.g., Building Multi-Agent AI Workflows with LangGraph and Python"
          value={value.topic}
          onChange={(e) => onChange({ ...value, topic: e.target.value })}
          required
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={id("word_count")}>Target Word Count</Label>
          <Input
            id={id("word_count")}
            type="number"
            step="10"
            min="300"
            max="10000"
            value={value.target_word_count}
            onChange={(e) => onChange({ ...value, target_word_count: parseInt(e.target.value)})}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor={id("tone")}>Content Tone</Label>
          <Select
            value={value.tone}
            onValueChange={(val) => onChange({ ...value, tone: val })}
          >
            <SelectTrigger id={id("tone")}>
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
      </div>

      <div className="space-y-2">
        <Label htmlFor={id("audience")}>Target Audience</Label>
        <Input
          id={id("audience")}
          placeholder="e.g., Software Engineers, CTOs, Founders"
          value={value.audience}
          onChange={(e) => onChange({ ...value, audience: e.target.value })}
        />
      </div>
    </div>
  );
}
