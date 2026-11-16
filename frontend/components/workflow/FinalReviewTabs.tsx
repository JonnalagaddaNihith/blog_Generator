"use client";

import { useState } from "react";
import { WorkflowStatusResponse } from "@/lib/types";
import { exportPdf } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { CheckCircle2, RefreshCw, Download, Loader2 } from "lucide-react";
import { ArticleDraftTab } from "./tabs/ArticleDraftTab";
import { SeoTab } from "./tabs/SeoTab";
import { QualityTab } from "./tabs/QualityTab";
import { FactsTab } from "./tabs/FactsTab";

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
  const { seo_metadata, quality_report, fact_verification_report, blog_content, is_complete, blog_version_id, image_details, image_generation_enabled } = status;
  const [exportingPdf, setExportingPdf] = useState(false);
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState<string | null>(null);

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      const result = await exportPdf(blog_version_id);
      setPdfDownloadUrl(new URL(result.download_url, apiBase).toString());
    } catch (err) {
      console.error("Failed to export PDF:", err);
    } finally {
      setExportingPdf(false);
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

        <ArticleDraftTab
          blogContent={blog_content}
          isComplete={is_complete}
          imageDetails={image_details}
          imageGenerationEnabled={image_generation_enabled}
          projectId={projectId}
          onRefresh={onRefresh}
        />
        <SeoTab seoMetadata={seo_metadata} />
        <QualityTab qualityReport={quality_report} />
        <FactsTab factVerificationReport={fact_verification_report} />
      </Tabs>
    </div>
  );
}
