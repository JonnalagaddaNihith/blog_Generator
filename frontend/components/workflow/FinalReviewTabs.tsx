"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { WorkflowStatusResponse } from "@/lib/types";
import { exportPdf, updateWorkflowBlogContent } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { CheckCircle2, AlertTriangle, RefreshCw, Download, Loader2, Edit, Save, X } from "lucide-react";

interface Props {
  status: WorkflowStatusResponse;
  submitting: boolean;
  onApproveFinal: () => void;
  onRegenerateSection: (section: "outline" | "seo" | "verification" | "all") => void;
  onRefresh?: () => void;
  projectId: number;
}

export function FinalReviewTabs({
  status,
  submitting,
  onApproveFinal,
  onRegenerateSection,
  onRefresh,
  projectId,
}: Props) {
  const { seo_metadata, quality_report, fact_verification_report, blog_content, is_complete, blog_version_id } = status;
  const [exportingPdf, setExportingPdf] = useState(false);
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState(false);
  const [editedContent, setEditedContent] = useState(blog_content);
  const [savingContent, setSavingContent] = useState(false);

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      const result = await exportPdf(blog_version_id);
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      setPdfDownloadUrl(new URL(result.download_url, apiBase).toString());
    } catch (err) {
      console.error("Failed to export PDF:", err);
    } finally {
      setExportingPdf(false);
    }
  };

  const handleSaveContent = async () => {
    setSavingContent(true);
    try {
      await updateWorkflowBlogContent(projectId, editedContent);
      setEditingContent(false);
      if (onRefresh) {
        await onRefresh();
      }
    } catch (err) {
      console.error("Failed to save blog content:", err);
    } finally {
      setSavingContent(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedContent(blog_content);
    setEditingContent(false);
  };

  const handleStartEdit = () => {
    setEditedContent(blog_content);
    setEditingContent(true);
  };

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
          pdfDownloadUrl ? (
            <Button asChild>
              <a href={pdfDownloadUrl} target="_blank" rel="noreferrer">
                <Download className="mr-2 h-4 w-4" /> Download PDF
              </a>
            </Button>
          ) : (
            <Button disabled={exportingPdf} onClick={handleExportPdf}>
              {exportingPdf ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" /> Export PDF
                </>
              )}
            </Button>
          )
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
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Article Draft</CardTitle>
                {!is_complete && !editingContent && (
                  <Button variant="outline" size="sm" onClick={handleStartEdit}>
                    <Edit className="mr-2 h-4 w-4" /> Edit Content
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {editingContent ? (
                <div className="space-y-4">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    rows={20}
                    className="font-mono text-sm"
                    placeholder="Edit the blog content here..."
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={handleCancelEdit} disabled={savingContent}>
                      <X className="mr-2 h-4 w-4" /> Cancel
                    </Button>
                    <Button onClick={handleSaveContent} disabled={savingContent}>
                      {savingContent ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" /> Save Changes
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="prose prose-neutral dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{blog_content}</ReactMarkdown>
                </div>
              )}
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