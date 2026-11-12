"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Company } from "@/lib/types";
import { createProject, startWorkflow } from "@/lib/api";
import { CompanySelector } from "@/components/companies/CompanySelector";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Sparkles, Loader2, ArrowRight } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
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
      // Step 1: Create project
      const project = await createProject({
        company_id: selectedCompany.id,
        topic: formData.topic,
        target_word_count: formData.target_word_count,
        audience: formData.audience,
        tone: formData.tone,
      });

      // Step 2: Start workflow
      await startWorkflow(project.id);

      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start blog generation workflow.");
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-3xl py-12">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight">AI Blog Generator Studio</h1>
        <p className="mt-2 text-muted-foreground">
          Autonomous multi-agent content generation pipeline with research, keyword intelligence, SEO, and human-in-the-loop approvals.
        </p>
      </div>

      {step === "company" ? (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Select Company</CardTitle>
            <CardDescription>
              Choose or create a company to associate with your blog project
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CompanySelector onSelect={handleCompanySelect} />
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
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="topic">Blog Topic / Working Title *</Label>
                <Input
                  id="topic"
                  placeholder="e.g., Building Multi-Agent AI Workflows with LangGraph and Python"
                  value={formData.topic}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="wordCount">Target Word Count</Label>
                  <Input
                    id="wordCount"
                    type="number"
                    step="100"
                    min="100"
                    max="10000"
                    value={formData.target_word_count}
                    onChange={(e) => setFormData({ ...formData, target_word_count: parseInt(e.target.value) || 500 })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tone">Content Tone</Label>
                  <Select
                    value={formData.tone}
                    onValueChange={(val) => setFormData({ ...formData, tone: val })}
                  >
                    <SelectTrigger id="tone">
                      <SelectValue placeholder="Select tone" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Professional yet engaging">Professional & Engaging</SelectItem>
                      <SelectItem value="Technical and authoritative">Technical & Authoritative</SelectItem>
                      <SelectItem value="Casual and conversational">Casual & Conversational</SelectItem>
                      <SelectItem value="Persuasive and marketing-focused">Persuasive & Marketing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="audience">Target Audience</Label>
                <Input
                  id="audience"
                  placeholder="e.g., Software Engineers, CTOs, Founders"
                  value={formData.audience}
                  onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
                />
              </div>
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