"use client";

import { WorkflowStatusResponse } from "@/lib/types";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle } from "lucide-react";

interface Props {
  factVerificationReport: WorkflowStatusResponse["fact_verification_report"];
}

export function FactsTab({ factVerificationReport }: Props) {
  return (
    <TabsContent value="facts">
      <Card>
        <CardContent className="space-y-3 pt-6">
          {(factVerificationReport.sources || []).map((item, i) => (
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
  );
}
