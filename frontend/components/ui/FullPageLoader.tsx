"use client";

import { Loader2 } from "lucide-react";

export function FullPageLoader() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80">
      <div className="flex flex-col items-center gap-4 rounded-lg border bg-card p-8 shadow-lg">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">
          This may take couple of minutes, Please don&apos;t leave the page
        </p>
      </div>
    </div>
  );
}
