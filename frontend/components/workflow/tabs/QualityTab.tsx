"use client";

import { WorkflowStatusResponse } from "@/lib/types";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CopyButton } from "@/components/ui/CopyButton";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  qualityReport: WorkflowStatusResponse["quality_report"];
  onFixQualityIssues?: () => void;
  fixDisabled?: boolean;
}

type MetricTone = "good" | "ok" | "poor" | "neutral";

const METRIC_INFO: Record<string, { title: string; hint: string; interpret: (v: number) => { summary: string; tone: MetricTone } }> = {
  word_count: {
    title: "Word Count", hint: "Total words in the post",
    interpret: (v) => v < 300 ? { summary: "Short piece — may lack depth", tone: "poor" }
      : v < 600 ? { summary: "Compact blog length", tone: "ok" }
      : v <= 1500 ? { summary: "Ideal blog length", tone: "good" }
      : { summary: "Long-form — consider splitting", tone: "neutral" },
  },
  sentence_count: {
    title: "Sentence Count", hint: "Total number of sentences",
    interpret: (v) => v === 0 ? { summary: "No sentences detected", tone: "poor" }
      : { summary: "Total sentences in the post", tone: "neutral" },
  },
  avg_sentence_length: {
    title: "Avg Sentence Length", hint: "Words per sentence (15\-20 is ideal)",
    interpret: (v) => v < 10 ? { summary: "Very short sentences — punchy but choppy", tone: "ok" }
      : v <= 20 ? { summary: "Easy to follow", tone: "good" }
      : v <= 28 ? { summary: "Some long sentences — may feel dense", tone: "ok" }
      : { summary: "Long sentences — consider breaking them up", tone: "poor" },
  },
  flesch_reading_ease: {
    title: "Reading Ease", hint: "0–100 scale — higher is easier (70+ is easy)",
    interpret: (v) => v >= 70 ? { summary: "Easy to read — broad audience", tone: "good" }
      : v >= 50 ? { summary: "Standard reading level", tone: "ok" }
      : v >= 30 ? { summary: "Difficult — advanced vocabulary or long sentences", tone: "poor" }
      : { summary: "Very difficult — college-level complexity", tone: "poor" },
  },
  flesch_kincaid_grade: {
    title: "Grade Level", hint: "US school grade needed to understand (lower = simpler)",
    interpret: (v) => v <= 8 ? { summary: `~Grade ${Math.round(v)} level — accessible to most readers`, tone: "good" }
      : v <= 12 ? { summary: `~Grade ${Math.round(v)} level — high-school reading level`, tone: "ok" }
      : { summary: `~Grade ${Math.round(v)} level — college-level reading`, tone: "poor" },
  },
  smog_index: {
    title: "SMOG Index", hint: "Estimated grade level needed to understand",
    interpret: (v) => v <= 8 ? { summary: `~Grade ${Math.round(v)} level — widely understandable`, tone: "good" }
      : v <= 12 ? { summary: `~Grade ${Math.round(v)} level — moderate complexity`, tone: "ok" }
      : { summary: `~Grade ${Math.round(v)} level — very complex text`, tone: "poor" },
  },
};

const TONE_STYLES: Record<MetricTone, string> = {
  good: "border-green-500/40 bg-green-500/10 text-green-700 dark:text-green-400",
  ok: "border-yellow-500/40 bg-yellow-500/10 text-yellow-700 dark:text-yellow-400",
  poor: "border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-400",
  neutral: "border-border bg-muted/50 text-muted-foreground",
};

export function QualityTab({ qualityReport, onFixQualityIssues, fixDisabled }: Props) {
  return (
    <TabsContent value="quality">
      <Card>
        <CardHeader><CardTitle>Quality Report</CardTitle></CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Grammar Score</div>
              <div className="text-2xl font-bold">{qualityReport.grammar_score ?? "-"}/100</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Grammar Issues</div>
              <div className="text-2xl font-bold">{qualityReport.grammar_issue_count ?? 0}</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Readability Score</div>
              <div className="text-2xl font-bold">{qualityReport.readability_score ?? "-"}/100</div>
            </div>
          </div>

          {qualityReport.readability_metrics && (
            <div>
              <h4 className="mb-3 text-sm font-semibold">Readability Metrics</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(qualityReport.readability_metrics).map(([metric, value]) => {
                  const info = METRIC_INFO[metric];
                  const num = typeof value === "number" ? value : null;
                  const interpretation = num !== null ? info?.interpret(num) : null;
                  return (
                    <div key={metric} className="rounded-lg border p-3">
                      <div className="flex items-baseline justify-between gap-2">
                        <div className="text-sm font-medium">{info?.title ?? metric.replaceAll("_", " ")}</div>
                        <div className="text-lg font-bold">
                          {num !== null ? num.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "-"}
                        </div>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{info?.hint ?? ""}</div>
                      {interpretation && (
                        <div className={`mt-2 rounded-md border px-2 py-1 text-xs font-medium ${TONE_STYLES[interpretation.tone]}`}>
                          {interpretation.summary}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {qualityReport.overall_assessment && (
            <div>
              <h4 className="mb-2 text-sm font-semibold">Overall Assessment</h4>
              <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{qualityReport.overall_assessment}</ReactMarkdown>
              </div>
            </div>
          )}

          {qualityReport.issues && qualityReport.issues.length > 0 && (
            <div>
              <div className="mb-3 flex items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">Quality Issues ({qualityReport.issues.length})</h4>
                <div className="flex items-center gap-2">
                  {onFixQualityIssues && (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={fixDisabled || !qualityReport.issues.some((issue) => issue.type !== "grammar")}
                      onClick={onFixQualityIssues}
                    >
                      <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Fix Quality Issues
                    </Button>
                  )}
                  <CopyButton value={JSON.stringify(qualityReport.issues, null, 2)} label="Quality Issues" />
                </div>
              </div>
              <div className="space-y-3">
                {qualityReport.issues.map((issue, index) => (
                  <div key={index} className="rounded-lg border p-3">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <Badge variant={issue.type === "grammar" ? "destructive" : "secondary"}>
                        {issue.type || "Issue"}
                      </Badge>
                      {issue.location && <span className="text-sm font-medium">{issue.location}</span>}
                    </div>
                    <div className="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{issue.suggestion}</ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {qualityReport.grammar_issues && qualityReport.grammar_issues.length > 0 && (
            <div>
              <div className="mb-3 flex items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">Grammar Issues ({qualityReport.grammar_issues.length})</h4>
                <CopyButton value={JSON.stringify(qualityReport.grammar_issues, null, 2)} label="Grammar Issues" />
              </div>
              <div className="space-y-3">
                {qualityReport.grammar_issues.map((issue, index) => (
                  <div key={index} className="rounded-lg border p-3">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <Badge variant="outline">{issue.short_message || issue.rule || "Issue"}</Badge>
                    </div>
                    <div className="text-sm prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{issue.message}</ReactMarkdown>
                    </div>
                    {issue.context && issue.context_offset !== undefined && issue.context_length && issue.rule === "MORFOLOGIK_RULE_EN_US" ? (
                      <div className="mt-2 rounded-md bg-muted p-2 text-sm">
                        <span className="text-muted-foreground">Context: </span>
                        {issue.context.slice(0, issue.context_offset)}
                        <span className="rounded bg-yellow-200 px-1 font-semibold text-yellow-900 dark:bg-yellow-700 dark:text-yellow-100">
                          {issue.context.slice(issue.context_offset, issue.context_offset + issue.context_length)}
                        </span>
                        {issue.context.slice(issue.context_offset + issue.context_length)}
                      </div>
                    ) : issue.context && (
                      <p className="mt-1 text-xs italic text-muted-foreground">{issue.context}</p>
                    )}
                    {issue.suggestions && issue.suggestions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {issue.suggestions.map((suggestion, i) => (
                          <Badge key={i} variant="secondary" className="font-normal">
                            {suggestion}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </CardContent>
      </Card>
    </TabsContent>
  );
}
