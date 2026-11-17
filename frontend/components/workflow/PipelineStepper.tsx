"use client";

import { CheckCircle2, Circle, Loader2, PauseCircle, ImageOff } from "lucide-react";
import { cn } from "@/lib/utils";

const STAGES: { id: string; label: string; disabled?: boolean }[] = [
  { id: "web_research", label: "Web Research" },
  { id: "keyword_intelligence", label: "Keywords" },
  { id: "competitor_gap", label: "Competitor Gap" },
  { id: "blog_strategy", label: "Strategy" },
  { id: "blog_strategy_approval", label: "Outline Gate" },
  { id: "blog_writing", label: "Writing" },
  { id: "seo", label: "SEO & Schema" },
  { id: "image", label: "Image", disabled: true },
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
    <div className="w-full rounded-lg border bg-card p-6">
      <div className="relative">
        {/* Horizontal line connecting all steps */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-muted" />

        {/* Progress line (filled portion) */}
        {activeIndex > -1 && (
          <div
            className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500"
            style={{
              width: `${(activeIndex / (STAGES.length - 1)) * 100}%`,
            }}
          />
        )}
        {isComplete && (
          <div className="absolute top-5 left-0 right-0 h-0.5 bg-primary" />
        )}

        {/* Steps */}
        <div className="relative flex items-start justify-between">
          {STAGES.map((stage, idx) => {
            if (stage.disabled) {
              return (
                <div key={stage.id} className="flex flex-col items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-muted bg-muted/50">
                    <ImageOff className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <span className="text-xs text-muted-foreground">{stage.label}</span>
                </div>
              );
            }

            const done = isComplete || (activeIndex > -1 && idx < activeIndex);
            const active = !isComplete && idx === activeIndex;
            const upcoming = activeIndex > -1 && idx > activeIndex;

            return (
              <div key={stage.id} className="flex flex-col items-center gap-2">
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300",
                    done && "border-primary bg-primary text-primary-foreground",
                    active && "border-primary bg-background",
                    upcoming && "border-muted bg-background",
                    !done && !active && !upcoming && "border-muted bg-background"
                  )}
                >
                  {done ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : active && isWaitingApproval ? (
                    <PauseCircle className="h-5 w-5 text-amber-500" />
                  ) : active ? (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-xs font-medium text-center max-w-[80px]",
                    done && "text-primary",
                    active && "text-primary",
                    upcoming && "text-muted-foreground"
                  )}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
