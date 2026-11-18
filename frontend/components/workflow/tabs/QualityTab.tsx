"use client";

import { WorkflowStatusResponse } from "@/lib/types";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CopyButton } from "@/components/ui/CopyButton";
import ReactMarkdown from "react-markdown";

interface Props {
  qualityReport: WorkflowStatusResponse["quality_report"];
}

export function QualityTab({ qualityReport }: Props) {
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
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {Object.entries(qualityReport.readability_metrics).map(([metric, value]) => (
                  <div key={metric} className="rounded-lg bg-muted/50 p-3">
                    <div className="text-xs capitalize text-muted-foreground">{metric.replaceAll("_", " ")}</div>
                    <div className="font-semibold">{typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "-"}</div>
                  </div>
                ))}
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
                <CopyButton value={JSON.stringify(qualityReport.issues, null, 2)} label="Quality Issues" />
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
