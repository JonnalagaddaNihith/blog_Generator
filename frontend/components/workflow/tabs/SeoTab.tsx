"use client";

import { WorkflowStatusResponse } from "@/lib/types";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CopyButton } from "@/components/ui/CopyButton";

interface Props {
  seoMetadata: WorkflowStatusResponse["seo_metadata"];
}

export function SeoTab({ seoMetadata }: Props) {
  return (
    <TabsContent value="seo">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <CardTitle>SEO Metadata</CardTitle>
            <Badge variant={seoMetadata.rich_results?.valid ? "default" : "destructive"}>
              {seoMetadata.rich_results?.valid ? "Rich Results Valid" : "Rich Results Issues"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <h4 className="text-sm font-semibold">Title</h4>
              {seoMetadata.title && <CopyButton value={seoMetadata.title} label="Title" />}
            </div>
            <p className="text-sm text-muted-foreground">
              {seoMetadata.title || "No title available."}
            </p>
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <h4 className="text-sm font-semibold">Meta Description</h4>
              {seoMetadata.meta_description && <CopyButton value={seoMetadata.meta_description} label="Meta Description" />}
            </div>
            <p className="text-sm text-muted-foreground">
              {seoMetadata.meta_description || "No meta description available."}
            </p>
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <h4 className="text-sm font-semibold">Keyword Density (%)</h4>
              <CopyButton value={JSON.stringify(seoMetadata.keyword_density || {}, null, 2)} label="Keyword Density" />
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(seoMetadata.keyword_density || {}).map(([kw, pct]) => (
                <Badge key={kw} variant="secondary">
                  {kw}: {pct}%
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <h4 className="text-sm font-semibold">Schema.org Article JSON-LD</h4>
              <CopyButton value={JSON.stringify(seoMetadata.structured_data, null, 2)} label="Structured Data" />
            </div>
            <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(seoMetadata.structured_data, null, 2)}
            </pre>
          </div>
          {seoMetadata.rich_results && (
            <div className="rounded-lg border p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">Rich Results</h4>
                <CopyButton value={JSON.stringify(seoMetadata.rich_results, null, 2)} label="Rich Results" />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {seoMetadata.rich_results.schema_org && (
                  <div className="rounded-md bg-muted/50 p-3">
                    <div className="text-xs text-muted-foreground">Schema.org Status</div>
                    <Badge variant={seoMetadata.rich_results.schema_org.valid ? "default" : "destructive"} className="mt-1">
                      {seoMetadata.rich_results.schema_org.valid ? "Valid" : "Invalid"}
                    </Badge>
                  </div>
                )}
              </div>
              {seoMetadata.rich_results.errors.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1 text-sm font-medium text-destructive">Errors</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-destructive">
                    {seoMetadata.rich_results.errors.map((error, index) => <li key={index}>{error}</li>)}
                  </ul>
                </div>
              )}
              {seoMetadata.rich_results.warnings.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1 text-sm font-medium text-yellow-600 dark:text-yellow-400">Warnings</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-yellow-700 dark:text-yellow-300">
                    {seoMetadata.rich_results.warnings.map((warning, index) => <li key={index}>{warning}</li>)}
                  </ul>
                </div>
              )}
              {seoMetadata.rich_results.schema_org && (
                <div className="mt-3 space-y-2 text-sm">
                  <div><span className="font-medium">Schema.org objects:</span> {seoMetadata.rich_results.schema_org.num_objects}</div>
                  {seoMetadata.rich_results.schema_org.errors.length > 0 && (
                    <div><span className="font-medium text-destructive">Schema.org errors:</span> {seoMetadata.rich_results.schema_org.errors.join(", ")}</div>
                  )}
                  {seoMetadata.rich_results.schema_org.warnings.length > 0 && (
                    <div><span className="font-medium text-yellow-600 dark:text-yellow-400">Schema.org warnings:</span> {seoMetadata.rich_results.schema_org.warnings.join(", ")}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );
}
