"use client";

import { CheckCircle2, Circle, Loader2, PauseCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const STAGES = [
  { id: "web_research", label: "Web Research" },
  { id: "keyword_intelligence", label: "Keywords" },
  { id: "competitor_gap", label: "Competitor Gap" },
  { id: "blog_strategy", label: "Strategy" },
  { id: "blog_strategy_approval", label: "Outline Gate" },
  { id: "blog_writing", label: "Writing" },
  { id: "seo", label: "SEO & Schema" },
  { id: "quality", label: "Quality Check" },
  { id: "fact_verification", label: "Fact-Check" },
  { id: "final_approval", label: "Final Gate" },
];

export function PipelineStepper({
  currentStage,
  isWaitingApproval,
  isComplete,
}: {
  currentStage: string;
  isWaitingApproval: boolean;
  isComplete: boolean;
}) {
  const activeIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-card p-4">
      {STAGES.map((stage, idx) => {
        const done = isComplete || (activeIndex > -1 && idx < activeIndex);
        const active = !isComplete && idx === activeIndex;

        return (
          <div key={stage.id} className="flex items-center gap-2">
            <Badge
              variant={done ? "default" : active ? "secondary" : "outline"}
              className="flex items-center gap-1.5 py-1 px-2.5"
            >
              {done ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              ) : active && isWaitingApproval ? (
                <PauseCircle className="h-3.5 w-3.5 text-amber-500" />
              ) : active ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
              ) : (
                <Circle className="h-3.5 w-3.5 text-muted-foreground" />
              )}
              <span>{stage.label}</span>
            </Badge>
          </div>
        );
      })}
    </div>
  );
}