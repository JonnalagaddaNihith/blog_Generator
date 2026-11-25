"use client";

import { useEffect, useState } from "react";
import { WorkflowStatusResponse, Company, SqlWebsite } from "@/lib/types";
import { exportPdf, exportDocx, exportTxt, exportHtml, exportMd, exportWordPress, getSqlWebsites, exportBlogToSql } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { CheckCircle2, RefreshCw, Download, Loader2, FileText, FileCode, Globe } from "lucide-react";
import { toast } from "sonner";
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
  company?: Company | null;
}

type ExportResult = { download_url: string; [key: string]: unknown };
type ExportFn = (id: number) => Promise<ExportResult>;

export function FinalReviewTabs({
  status,
  submitting,
  onApproveFinal,
  onRegenerateSection,
  onRefresh,
  projectId,
  company,
}: Props) {
  const { seo_metadata, quality_report, fact_verification_report, blog_content, is_complete, blog_version_id, image_details, image_generation_enabled } = status;
  const [exporting, setExporting] = useState<{ [key: string]: boolean }>({});
  const [publishingWordPress, setPublishingWordPress] = useState(false);
  const [sqlWebsites, setSqlWebsites] = useState<SqlWebsite[]>([]);
  const [publishingSql, setPublishingSql] = useState<string | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_URL;
  const regenerationDisabled = submitting || is_complete;

  useEffect(() => {
    if (!company?.id || !is_complete) return;
    let cancelled = false;
    getSqlWebsites(company.id)
      .then((websites) => {
        if (!cancelled) setSqlWebsites(websites);
      })
      .catch(() => {
        if (!cancelled) setSqlWebsites([]);
      });
    return () => {
      cancelled = true;
    };
  }, [company?.id, is_complete]);

  const triggerFileDownload = async (url: string, filename: string) => {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`);
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  };

  const handleExport = async (format: string, exportFn: ExportFn) => {
    setExporting(prev => ({ ...prev, [format]: true }));
    try {
      const result = await exportFn(blog_version_id);
      const filenameValue = result[`${format}_filename`];
      const filename = typeof filenameValue === "string" ? filenameValue : `${format}`;
      const url = new URL(result.download_url, apiBase).toString();
      await triggerFileDownload(url, filename);
      toast.success(`${format.toUpperCase()} downloaded`);
    } catch (err) {
      console.error(`Failed to export ${format.toUpperCase()}:`, err);
      toast.error(`Failed to export ${format.toUpperCase()}`, {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setExporting(prev => ({ ...prev, [format]: false }));
    }
  };

  const handlePublishWordPress = async (status: "draft" | "publish") => {
    // Check if WordPress is configured
    if (!company?.wp_configured) {
      toast.error("WordPress not configured", {
        description: `Please configure WordPress credentials for ${company?.name || "this company"} first.`,
        action: company ? {
          label: "Open Settings",
          onClick: () => window.location.href = `/companies/${company.id}`,
        } : undefined,
      });
      return;
    }

    setPublishingWordPress(true);
    try {
      const result = await exportWordPress(blog_version_id, status);
      toast.success(`Published to WordPress as ${status}`, {
        description: result.url || result.message,
        action: result.url ? {
          label: "View Post",
          onClick: () => window.open(result.url, "_blank"),
        } : undefined,
        duration: 10000,
      });
    } catch (err) {
      console.error("Failed to publish to WordPress:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      toast.error("WordPress publishing failed", {
        description: errorMessage,
        duration: 8000,
      });
    } finally {
      setPublishingWordPress(false);
    }
  };

  const sqlWebsiteReady = (w: SqlWebsite) =>
    w.status === "connected" && !!w.table_name && !!w.column_mapping && Object.keys(w.column_mapping).length > 0;

  const handlePublishSql = async (website: SqlWebsite, status: "draft" | "publish") => {
    if (!sqlWebsiteReady(website)) {
      toast.error(`"${website.name}" is not ready to publish`, {
        description: "Connect and configure a table mapping for this website first.",
        action: company ? {
          label: "Open Settings",
          onClick: () => window.location.href = `/companies/${company.id}`,
        } : undefined,
      });
      return;
    }

    const key = `${website.id}:${status}`;
    setPublishingSql(key);
    try {
      const result = await exportBlogToSql(website.id, blog_version_id, status);
      toast.success(`Published to ${website.name} as ${status}`, {
        description: result.message || result.url,
        action: result.url ? {
          label: "View Post",
          onClick: () => window.open(result.url, "_blank"),
        } : undefined,
        duration: 10000,
      });
    } catch (err) {
      console.error(`Failed to publish to ${website.name}:`, err);
      toast.error("SQL website publishing failed", {
        description: err instanceof Error ? err.message : "Unknown error",
        duration: 8000,
      });
    } finally {
      setPublishingSql(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={regenerationDisabled}
            onClick={() => onRegenerateSection("outline")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Regenerate Outline
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={regenerationDisabled}
            onClick={() => onRegenerateSection("seo")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run SEO
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={regenerationDisabled}
            onClick={() => onRegenerateSection("verification")}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-run Fact-Check
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={regenerationDisabled}
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
            <DropdownMenuContent align="end" className="w-56">
              {/* File Export Section */}
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Download as File</div>
              {[
                { format: 'pdf', label: 'PDF', icon: <FileText className="mr-2 h-4 w-4" />, exportFn: exportPdf },
                { format: 'docx', label: 'DOCX', icon: <FileText className="mr-2 h-4 w-4" />, exportFn: exportDocx },
                { format: 'txt', label: 'TXT', icon: <FileCode className="mr-2 h-4 w-4" />, exportFn: exportTxt },
                { format: 'html', label: 'HTML', icon: <Globe className="mr-2 h-4 w-4" />, exportFn: exportHtml },
                { format: 'md', label: 'Markdown', icon: <FileCode className="mr-2 h-4 w-4" />, exportFn: exportMd },
              ].map(({ format, label, icon, exportFn }) => (
                <DropdownMenuItem
                  key={format}
                  onClick={() => handleExport(format, exportFn)}
                  disabled={exporting[format]}
                >
                  <span className="flex items-center">
                    {exporting[format] ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : icon}
                    {exporting[format] ? `Generating ${label}...` : label}
                  </span>
                </DropdownMenuItem>
              ))}

              <DropdownMenuSeparator />

              {/* WordPress Section */}
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Publish to WordPress</div>
              <DropdownMenuItem 
                onClick={() => handlePublishWordPress("draft")} 
                disabled={publishingWordPress || !company?.wp_configured}
                className={!company?.wp_configured ? "opacity-50 cursor-not-allowed" : ""}
              >
                <span className="flex items-center">
                  {publishingWordPress ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
                  Draft
                  {!company?.wp_configured && <span className="ml-2 text-xs text-muted-foreground">(Not configured)</span>}
                </span>
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => handlePublishWordPress("publish")} 
                disabled={publishingWordPress || !company?.wp_configured}
                className={!company?.wp_configured ? "opacity-50 cursor-not-allowed" : ""}
              >
                <span className="flex items-center">
                  {publishingWordPress ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Globe className="mr-2 h-4 w-4" />}
                  Live
                  {!company?.wp_configured && <span className="ml-2 text-xs text-muted-foreground">(Not configured)</span>}
                </span>
              </DropdownMenuItem>

              {/* Custom SQL Websites Section */}
              {sqlWebsites.length > 0 && (
                <>
                  <DropdownMenuSeparator />
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Publish to Custom Website (SQL)</div>
                  {sqlWebsites.map((w) => {
                    const ready = sqlWebsiteReady(w);
                    return (
                      <DropdownMenuItem
                        key={w.id}
                        onClick={() => handlePublishSql(w, "draft")}
                        disabled={!ready || publishingSql !== null}
                        className={!ready ? "opacity-60 cursor-not-allowed" : ""}
                      >
                        <span className="flex items-center">
                          {publishingSql === `${w.id}:draft` ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
                          <span className="truncate max-w-[140px]">{w.name}</span>
                          {!ready && <span className="ml-2 text-xs text-muted-foreground">(not configured)</span>}
                        </span>
                      </DropdownMenuItem>
                    );
                  })}
                </>
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
          fixDisabled={regenerationDisabled}
        />
        <FactsTab factVerificationReport={fact_verification_report} />
      </Tabs>
    </div>
  );
}
