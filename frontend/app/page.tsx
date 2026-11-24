import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Building2,
  CheckCircle2,
  Download,
  FileSearch,
  FileText,
  Image,
  ListTree,
  PenLine,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const steps = [
  {
    icon: Building2,
    title: "1. Set up a company",
    description:
      "Create a company profile first — it holds the brand voice, topics, and settings that every blog post is generated against.",
    href: "/companies/new",
    cta: "Add Company",
  },
  {
    icon: Sparkles,
    title: "2. Start a project",
    description:
      "Pick a company and a topic, then launch a generation project. The AI researches the subject and drafts a full outline for you to review.",
    href: "/projects",
    cta: "New Project",
  },
  {
    icon: Search,
    title: "3. Review research & outline",
    description:
      "Check the gathered sources and the proposed structure. Regenerate the outline if the angle isn't right — it's cheaper than rewriting the article.",
  },
  {
    icon: FileText,
    title: "4. Approve the draft",
    description:
      "The workflow generates the blog content, SEO metadata, and images, then verifies and scores quality. You approve, reject, or regenerate any stage.",
  },
  {
    icon: Download,
    title: "5. Export & publish",
    description:
      "Once approved, export the finished post in your preferred format and publish it on your company's site or CMS.",
  },
];

const features = [
  {
    icon: FileSearch,
    title: "Research-backed",
    description: "Every post is grounded in gathered sources, not just the model's memory.",
  },
  {
    icon: ListTree,
    title: "Structured outlines",
    description: "Review and edit the outline before a single paragraph is written.",
  },
  {
    icon: ShieldCheck,
    title: "Human approvals",
    description: "Nothing publishes automatically — every stage needs your sign-off.",
  },
  {
    icon: Image,
    title: "SEO & images",
    description: "Metadata, keywords, and featured images are generated alongside the copy.",
  },
  {
    icon: PenLine,
    title: "Regenerate anything",
    description: "Reject a stage and retry just that piece — outline, content, SEO, or image.",
  },
  {
    icon: CheckCircle2,
    title: "Quality verified",
    description: "Built-in verification and quality scoring catch weak drafts early.",
  },
];

export default function HomePage() {
  return (
    <div className="container mx-auto max-w-5xl py-16">
      {/* Hero */}
      <div className="text-center">
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

      {/* How to use */}
      <section className="mt-20">
        <h2 className="text-2xl font-bold tracking-tight text-center">How to use the Blog Generator</h2>
        <p className="mt-2 text-center text-muted-foreground">
          From company profile to published post in five steps.
        </p>
        <div className="mt-8 space-y-4">
          {steps.map((step) => (
            <Card key={step.title}>
              <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <step.icon className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <CardTitle>{step.title}</CardTitle>
                  <CardDescription className="text-sm leading-relaxed">
                    {step.description}
                  </CardDescription>
                </div>
              </CardHeader>
              {"href" in step && step.href && (
                <CardContent>
                  <Button asChild variant="secondary" size="sm">
                    <Link href={step.href}>{step.cta}</Link>
                  </Button>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mt-20">
        <h2 className="text-2xl font-bold tracking-tight text-center">What's included</h2>
        <p className="mt-2 text-center text-muted-foreground">
          A guided pipeline that keeps you in control at every stage.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title}>
              <CardHeader>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <feature.icon className="h-4 w-4" />
                </div>
                <CardTitle className="text-base">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* Footer CTA */}
      <section className="mt-20 rounded-xl border bg-muted/40 p-8 text-center">
        <h2 className="text-xl font-bold">Ready to write your next post?</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Create a company profile if you haven't yet, then start your first project.
        </p>
        <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild>
            <Link href="/companies/new">
              <Building2 className="mr-2 h-4 w-4" /> Set Up Company
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/projects">
              <Sparkles className="mr-2 h-4 w-4" /> View Projects
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
