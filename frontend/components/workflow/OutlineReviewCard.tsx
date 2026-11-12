"use client";

import { useState } from "react";
import { OutlineSection } from "@/lib/types";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Check, Plus, Trash2 } from "lucide-react";

interface Props {
  strategy?: string;
  initialOutline: OutlineSection[];
  submitting: boolean;
  onApprove: (updatedOutline: { strategy?: string; outline: OutlineSection[] }) => void;
  onRegenerate: () => void;
}

export function OutlineReviewCard({
  strategy,
  initialOutline,
  submitting,
  onApprove,
  onRegenerate,
}: Props) {
  const [sections, setSections] = useState<OutlineSection[]>(initialOutline);

  const totalWords = sections.reduce((sum, s) => sum + (Number(s.word_count) || 0), 0);

  const updateSection = (index: number, field: keyof OutlineSection, value: string | number) => {
    setSections((prev) =>
      prev.map((sec, i) => (i === index ? { ...sec, [field]: value } : sec))
    );
  };

  const addSection = () => {
    setSections((prev) => [...prev, { section: "New Section", word_count: 200, description: "" }]);
  };

  const removeSection = (index: number) => {
    setSections((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Gate 1: Strategy & Outline Review</CardTitle>
            <CardDescription>
              Edit section headings, descriptions, or word targets before generating the article.
            </CardDescription>
          </div>
          <Badge variant="secondary">Total: {totalWords} words</Badge>
        </div>
        {strategy && (
          <div className="mt-3 rounded-md bg-muted p-3 text-sm text-muted-foreground">
            <strong className="text-foreground">Differentiated Strategy: </strong>
            {strategy}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {sections.map((sec, idx) => (
          <div key={idx} className="space-y-2 rounded-lg border p-4">
            <div className="flex items-center gap-3">
              <Input
                value={sec.section}
                onChange={(e) => updateSection(idx, "section", e.target.value)}
                placeholder="Section Heading"
                className="font-medium"
              />
              <Input
                type="number"
                value={sec.word_count}
                onChange={(e) => updateSection(idx, "word_count", parseInt(e.target.value, 10) || 0)}
                className="w-28"
              />
              <Button variant="ghost" size="icon" onClick={() => removeSection(idx)}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
            <Textarea
              value={sec.description}
              onChange={(e) => updateSection(idx, "description", e.target.value)}
              placeholder="Section coverage notes..."
              rows={2}
            />
          </div>
        ))}

        <Button type="button" variant="outline" size="sm" onClick={addSection}>
          <Plus className="mr-1.5 h-4 w-4" /> Add Section
        </Button>
      </CardContent>

      <CardFooter className="flex justify-between border-t pt-4">
        <Button variant="outline" disabled={submitting} onClick={onRegenerate}>
          <RefreshCw className="mr-2 h-4 w-4" /> Regenerate Outline
        </Button>
        <Button
          disabled={submitting || sections.length === 0}
          onClick={() => onApprove({ strategy, outline: sections })}
        >
          <Check className="mr-2 h-4 w-4" /> Approve & Write Blog
        </Button>
      </CardFooter>
    </Card>
  );
}