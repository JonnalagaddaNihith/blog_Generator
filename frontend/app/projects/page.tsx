"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Company } from "@/lib/types";
import { createProjectAndStartWorkflow, getCompany } from "@/lib/api";
import { CompanySelector } from "@/components/companies/CompanySelector";
import { ProjectFormFields } from "@/components/projects/ProjectFormFields";
import { FullPageLoader } from "@/components/ui/FullPageLoader";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Sparkles, Loader2, ArrowRight } from "lucide-react";

function WizardFallback() {
  return (
    <div className="container mx-auto flex max-w-3xl justify-center py-12">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}

function NewProjectWizard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get("company_id");
  const [step, setStep] = useState<"company" | "project">("company");
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    topic: "",
    target_word_count: 500,
    audience: "Tech professionals and developers",
    tone: "Professional yet engaging",
  });

  useEffect(() => {
    const companyId = Number(companyIdParam);
    if (!companyIdParam || !Number.isInteger(companyId) || companyId <= 0) return;

    let cancelled = false;
    getCompany(companyId)
      .then((company) => {
        if (cancelled) return;
        setSelectedCompany(company);
        setStep("project");
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load company");
      });

    return () => {
      cancelled = true;
    };
  }, [companyIdParam]);

  const handleCompanySelect = (company: Company) => {
    setSelectedCompany(company);
    setStep("project");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompany) {
      setError("Please select a company first.");
      return;
    }
    if (!formData.topic.trim()) {
      setError("Please enter a blog topic.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const project = await createProjectAndStartWorkflow({
        company_id: selectedCompany.id,
        topic: formData.topic,
        target_word_count: formData.target_word_count,
        audience: formData.audience,
        tone: formData.tone,
      });

      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start blog generation workflow.");
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-3xl py-12">
      {loading && <FullPageLoader />}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight">New Blog Project</h1>
        <p className="mt-2 text-muted-foreground">
          Select a company and configure your parameters to kick off web research, competitor gap analysis, and outline generation.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {step === "company" ? (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Select Company</CardTitle>
            <CardDescription>
              Choose or create a company to associate with your blog project
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CompanySelector
              onSelect={handleCompanySelect}
              selectedCompanyId={selectedCompany?.id}
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <form onSubmit={handleSubmit}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Step 2: Create Blog Project</CardTitle>
                  <CardDescription>
                    Configure your parameters to kick off web research, competitor gap analysis, and outline generation.
                  </CardDescription>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setStep("company")}
                >
                  Change Company
                </Button>
              </div>
              {selectedCompany && (
                <div className="mt-4 rounded-md bg-muted p-3 text-sm">
                  <span className="font-medium">Selected Company:</span> {selectedCompany.name}
                </div>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <ProjectFormFields value={formData} onChange={setFormData} />
            </CardContent>
            <CardFooter className="flex justify-end border-t pt-4">
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Initializing Pipeline...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" /> Start Workflow
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}
    </div>
  );
}

export default function NewProjectPage() {
  return (
    <Suspense fallback={<WizardFallback />}>
      <NewProjectWizard />
    </Suspense>
  );
}
