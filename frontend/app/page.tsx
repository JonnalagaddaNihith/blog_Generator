import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Building2, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <div className="container mx-auto max-w-3xl py-16 text-center">
      <h1 className="text-4xl font-extrabold tracking-tight">AI Blog Generator</h1>
      <p className="mt-4 text-lg text-muted-foreground">
        Create, review, and export AI-generated blog posts with research, SEO, and human approvals.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/projects">
            <Sparkles className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/companies">
            <Building2 className="mr-2 h-4 w-4" /> Companies
          </Link>
        </Button>
      </div>
    </div>
  );
}
