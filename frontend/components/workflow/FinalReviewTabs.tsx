"use client";

import { useState } from "react";
import { WorkflowStatusResponse } from "@/lib/types";
import { exportPdf, exportDocx, exportTxt, exportHtml, exportMd } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { CheckCircle2, RefreshCw, Download, Loader2, FileText, FileCode, Globe } from "lucide-react";
import { ArticleDraftTab } from "./tabs/ArticleDraftTab";
import { SeoTab } from "./tabs/SeoTab";
import { QualityTab } from "./tabs/QualityTab";
import { FactsTab } from "./tabs/FactsTab";

interface Props {
  status: WorkflowStatusResponse;
  submitting: boolean;
  onApproveFinal: () => void;
  onRegenerateSection: (section: "outline" | "seo" | "verification" | "quality" | "all") => void;
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
  const { seo_metadata, quality_report, fact_verification_report, blog_content, is_complete, blog_version_id, image_details, image_generation_enabled } = status;
  const [exporting, setExporting] = useState<{ [key: string]: boolean }>({});
  const [downloadUrls, setDownloadUrls] = useState<{ [key: string]: string | null }>({});

  const handleExport = async (format: string, exportFn: (id: number) => Promise<any>) => {
    setExporting(prev => ({ ...prev, [format]: true }));
    try {
      const result = await exportFn(blog_version_id);
      setDownloadUrls(prev => ({ ...prev, [format]: new URL(result.download_url, apiBase).toString() }));
    } catch (err) {
      console.error(`Failed to export ${format.toUpperCase()}:`, err);
    } finally {
      setExporting(prev => ({ ...prev, [format]: false }));
    }
  };

  const apiBase = process.env.NEXT_PUBLIC_API_URL;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={submitting}
            onClick={() => onRegenerateSection("outline")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Regenerate Outline
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={submitting}
            onClick={() => onRegenerateSection("seo")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run SEO
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={submitting}
            onClick={() => onRegenerateSection("verification")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run Fact-Check
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={submitting}
            onClick={() => onRegenerateSection("all")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Rewrite Article
          </Button>
        </div>

        {is_complete ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button>
                <Download className="mr-2 h-4 w-4" /> Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {downloadUrls['pdf'] ? (
                <DropdownMenuItem asChild>
                  <a href={downloadUrls['pdf']} target="_blank" rel="noreferrer" className="flex items-center">
                    <FileText className="mr-2 h-4 w-4" /> Download PDF
                  </a>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => handleExport('pdf', exportPdf)} disabled={exporting['pdf']}>
                  <span className="flex items-center">
                    {exporting['pdf'] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
                    {exporting['pdf'] ? 'Generating...' : 'Export PDF'}
                  </span>
                </DropdownMenuItem>
              )}
              {downloadUrls['docx'] ? (
                <DropdownMenuItem asChild>
                  <a href={downloadUrls['docx']} target="_blank" rel="noreferrer" className="flex items-center">
                    <FileText className="mr-2 h-4 w-4" /> Download DOCX
                  </a>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => handleExport('docx', exportDocx)} disabled={exporting['docx']}>
                  <span className="flex items-center">
                    {exporting['docx'] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
                    {exporting['docx'] ? 'Generating...' : 'Export DOCX'}
                  </span>
                </DropdownMenuItem>
              )}
              {downloadUrls['txt'] ? (
                <DropdownMenuItem asChild>
                  <a href={downloadUrls['txt']} target="_blank" rel="noreferrer" className="flex items-center">
                    <FileCode className="mr-2 h-4 w-4" /> Download TXT
                  </a>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => handleExport('txt', exportTxt)} disabled={exporting['txt']}>
                  <span className="flex items-center">
                    {exporting['txt'] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileCode className="mr-2 h-4 w-4" />}
                    {exporting['txt'] ? 'Generating...' : 'Export TXT'}
                  </span>
                </DropdownMenuItem>
              )}
              {downloadUrls['html'] ? (
                <DropdownMenuItem asChild>
                  <a href={downloadUrls['html']} target="_blank" rel="noreferrer" className="flex items-center">
                    <Globe className="mr-2 h-4 w-4" /> Download HTML
                  </a>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => handleExport('html', exportHtml)} disabled={exporting['html']}>
                  <span className="flex items-center">
                    {exporting['html'] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Globe className="mr-2 h-4 w-4" />}
                    {exporting['html'] ? 'Generating...' : 'Export HTML'}
                  </span>
                </DropdownMenuItem>
              )}
              {downloadUrls['md'] ? (
                <DropdownMenuItem asChild>
                  <a href={downloadUrls['md']} target="_blank" rel="noreferrer" className="flex items-center">
                    <FileCode className="mr-2 h-4 w-4" /> Download MD
                  </a>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => handleExport('md', exportMd)} disabled={exporting['md']}>
                  <span className="flex items-center">
                    {exporting['md'] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileCode className="mr-2 h-4 w-4" />}
                    {exporting['md'] ? 'Generating...' : 'Export MD'}
                  </span>
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
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

        <ArticleDraftTab
          blogContent={blog_content}
          isComplete={is_complete}
          imageDetails={image_details}
          imageGenerationEnabled={image_generation_enabled}
          projectId={projectId}
          onRefresh={onRefresh}
        />
        <SeoTab seoMetadata={seo_metadata} />
        <QualityTab
          qualityReport={quality_report}
          onFixQualityIssues={() => onRegenerateSection("quality")}
          fixDisabled={submitting}
        />
        <FactsTab factVerificationReport={fact_verification_report} />
      </Tabs>
    </div>
  );
}
