"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startWorkflow } from "@/lib/api";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sparkles, Loader2 } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    topic: "",
    target_word_count: 500,
    audience: "Tech professionals and developers",
    tone: "Professional yet engaging",
    company_description: "",
    company_website: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.topic.trim()) {
      setError("Please enter a blog topic.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // For demonstration, we generate a mock project ID or use timestamp
      // Alternatively, if your backend returns the created project/thread ID, use it here.
      const projectId = Math.floor(Date.now() / 1000); 
      
      await startWorkflow({
        ...formData,
      });

      router.push(`/projects/${projectId}`);
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

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Create New Blog Project</CardTitle>
            <CardDescription>
              Configure your parameters to kick off web research, competitor gap analysis, and outline generation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
                {error}
              </div>
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

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="companyWebsite">Company Website (Optional)</Label>
                <Input
                  id="companyWebsite"
                  placeholder="https://yourcompany.com"
                  value={formData.company_website}
                  onChange={(e) => setFormData({ ...formData, company_website: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="companyDesc">Company / Brand Context (Optional)</Label>
                <Textarea
                  id="companyDesc"
                  placeholder="Brief context about your product or services..."
                  rows={2}
                  value={formData.company_description}
                  onChange={(e) => setFormData({ ...formData, company_description: e.target.value })}
                />
              </div>
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
                </>
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}