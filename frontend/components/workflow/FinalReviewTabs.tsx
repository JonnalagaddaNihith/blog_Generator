"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { WorkflowStatusResponse } from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertTriangle, RefreshCw, Download } from "lucide-react";

interface Props {
  status: WorkflowStatusResponse;
  submitting: boolean;
  onApproveFinal: () => void;
  onRegenerateSection: (section: "outline" | "seo" | "verification" | "all") => void;
}

export function FinalReviewTabs({
  status,
  submitting,
  onApproveFinal,
  onRegenerateSection,
}: Props) {
  const { seo_metadata, quality_report, fact_verification_report, blog_content, is_complete } = status;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={submitting || is_complete}
            onClick={() => onRegenerateSection("seo")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run SEO
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={submitting || is_complete}
            onClick={() => onRegenerateSection("verification")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run Fact-Check
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={submitting || is_complete}
            onClick={() => onRegenerateSection("all")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Rewrite Article
          </Button>
        </div>

        {is_complete ? (
          <Button asChild>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/blogs/${status.blog_version_id}/pdf`}
              target="_blank"
              rel="noreferrer"
            >
              <Download className="mr-2 h-4 w-4" /> Export PDF
            </a>
          </Button>
        ) : (
          <Button disabled={submitting} onClick={onApproveFinal}>
            <CheckCircle2 className="mr-2 h-4 w-4" /> Approve & Finalize
          </Button>
        )}
      </div>

      <Tabs defaultValue="article">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="article">Article Draft</TabsTrigger>
          <TabsTrigger value="seo">SEO & JSON-LD</TabsTrigger>
          <TabsTrigger value="quality">Quality ({quality_report.grammar_score ?? "-"}%)</TabsTrigger>
          <TabsTrigger value="facts">
            Facts ({fact_verification_report.claims_verified ?? 0}/{fact_verification_report.total_claims ?? 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="article">
          <Card>
            <CardContent className="prose prose-neutral dark:prose-invert max-w-none pt-6">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{blog_content}</ReactMarkdown>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="seo">
          <Card>
            <CardHeader>
              <CardTitle>{seo_metadata.title}</CardTitle>
              <p className="text-sm text-muted-foreground">{seo_metadata.meta_description}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="mb-2 text-sm font-semibold">Keyword Density (%)</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(seo_metadata.keyword_density || {}).map(([kw, pct]) => (
                    <Badge key={kw} variant="secondary">
                      {kw}: {pct}%
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="mb-2 text-sm font-semibold">Schema.org Article JSON-LD</h4>
                <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
                  {JSON.stringify(seo_metadata.structured_data, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quality">
          <Card>
            <CardContent className="space-y-4 pt-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Grammar Score</div>
                  <div className="text-2xl font-bold">{quality_report.grammar_score}/100</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Readability Score</div>
                  <div className="text-2xl font-bold">{quality_report.readability_score}/100</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">LanguageTool Issues</div>
                  <div className="text-2xl font-bold">{quality_report.grammar_issue_count ?? 0}</div>
                </div>
              </div>
              <p className="text-sm">{quality_report.overall_assessment}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="facts">
          <Card>
            <CardContent className="space-y-3 pt-6">
              {(fact_verification_report.sources || []).map((item, i) => (
                <div key={i} className="flex items-start justify-between gap-4 rounded-lg border p-3">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{item.claim}</p>
                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-primary underline"
                      >
                        {item.source || item.source_url}
                      </a>
                    )}
                    {item.issue && <p className="text-xs text-destructive">{item.issue}</p>}
                  </div>
                  <Badge variant={item.supported ? "default" : "destructive"}>
                    {item.supported ? (
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                    ) : (
                      <AlertTriangle className="mr-1 h-3 w-3" />
                    )}
                    {item.supported ? "Verified" : "Unverified"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}