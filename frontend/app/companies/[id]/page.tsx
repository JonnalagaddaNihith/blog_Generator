"use client";

import { useState, useEffect, Suspense, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Company, Project, WorkflowStatusResponse, ProjectUpdate } from "@/lib/types";
import { getCompany, updateCompany, deleteCompany, getProjects, getWorkflowStatus, updateProject, deleteProject } from "@/lib/api";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Home, Loader2, Edit, Trash2, FolderOpen, Building2 } from "lucide-react";

function CompanyDetailContent({ companyId }: { companyId: number }) {
  const router = useRouter();

  const [company, setCompany] = useState<Company | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [workflowStatuses, setWorkflowStatuses] = useState<Record<number, WorkflowStatusResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [savingProject, setSavingProject] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ kind: "project" | "company"; id: number; label: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    website: "",
  });

  const [projectFormData, setProjectFormData] = useState({
    target_word_count: 500,
    audience: "",
    tone: "",
  });

  useEffect(() => {
    loadCompany();
    loadProjects();
  }, [companyId]);

  const loadCompany = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCompany(companyId);
      setCompany(data);
      setFormData({
        name: data.name,
        description: data.description || "",
        website: data.website || "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load company");
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await getProjects(0, 100, companyId);
      setProjects(data);
      // Load workflow status for each project
      const statuses: Record<number, WorkflowStatusResponse> = {};
      for (const project of data) {
        try {
          const status = await getWorkflowStatus(project.id);
          statuses[project.id] = status;
        } catch (err) {
          console.error(`Failed to load workflow status for project ${project.id}:`, err);
        }
      }
      setWorkflowStatuses(statuses);
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  };

  const getProjectStatusBadge = (projectId: number) => {
    const status = workflowStatuses[projectId];
    if (!status) {
      return { label: "Loading...", variant: "secondary" as const };
    }

    if (status.is_complete) {
      return { label: "Completed", variant: "default" as const };
    }

    if (status.is_waiting_approval) {
      return { label: "Waiting Approval", variant: "secondary" as const };
    }

    if (status.outline?.outline && status.outline.outline.length > 0) {
      if (status.blog_content) {
        return { label: "Generated", variant: "secondary" as const };
      }
      return { label: "Outline Ready", variant: "outline" as const };
    }

    return { label: "Draft", variant: "secondary" as const };
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setProjectFormData({
      target_word_count: project.target_word_count,
      audience: project.audience || "",
      tone: project.tone || "",
    });
    setProjectDialogOpen(true);
  };

  const handleUpdateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProject) return;

    setSavingProject(true);
    try {
      const updateData: ProjectUpdate = {
        target_word_count: projectFormData.target_word_count,
        audience: projectFormData.audience || undefined,
        tone: projectFormData.tone || undefined,
      };
      const updated = await updateProject(editingProject.id, updateData);
      setProjects((prev) => prev.map((p) => (p.id === editingProject.id ? updated : p)));
      setProjectDialogOpen(false);
      setEditingProject(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setSavingProject(false);
    }
  };

  const handleDeleteProject = (projectId: number) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      setDeleteTarget({ kind: "project", id: projectId, label: project.topic });
    }
  };

  const handleDelete = () => {
    if (company) {
      setDeleteTarget({ kind: "company", id: companyId, label: company.name });
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    setDeleting(true);
    try {
      if (deleteTarget.kind === "project") {
        await deleteProject(deleteTarget.id);
        setProjects((prev) => prev.filter((p) => p.id !== deleteTarget.id));
        setWorkflowStatuses((prev) => {
          const newStatuses = { ...prev };
          delete newStatuses[deleteTarget.id];
          return newStatuses;
        });
        setDeleteTarget(null);
      } else {
        await deleteCompany(deleteTarget.id);
        router.push("/companies");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
      setDeleting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("Company name is required.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const updated = await updateCompany(companyId, formData);
      setCompany(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update company");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto max-w-4xl py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="container mx-auto max-w-4xl py-8">
        <Alert variant="destructive">
          <AlertDescription>{error || "Company not found"}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl space-y-6 py-8">
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/" className="flex items-center gap-1.5">
                <Home className="h-4 w-4" />
              </Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/companies">Companies</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="flex items-center gap-1.5">
              <Building2 className="h-4 w-4" />
              {company.name}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{editing ? "Edit Company" : company.name}</CardTitle>
              <CardDescription>
                {editing ? "Update company information" : "Company details and associated projects"}
              </CardDescription>
            </div>
            {!editing && (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  <Edit className="mr-2 h-4 w-4" /> Edit
                </Button>
                <Button variant="outline" size="sm" onClick={handleDelete}>
                  <Trash2 className="mr-2 h-4 w-4 text-destructive" /> Delete
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {editing ? (
            <form onSubmit={handleUpdate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Company Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input
                  id="website"
                  placeholder="https://yourcompany.com"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of your company..."
                  rows={4}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setEditing(false)} disabled={saving}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              {company.website && (
                <div>
                  <Label className="text-muted-foreground">Website</Label>
                  <p className="mt-1">
                    <a href={company.website} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                      {company.website}
                    </a>
                  </p>
                </div>
              )}

              {company.description && (
                <div>
                  <Label className="text-muted-foreground">Description</Label>
                  <p className="mt-1 text-sm">{company.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <Label className="text-muted-foreground">Created</Label>
                  <p className="mt-1 text-sm">{new Date(company.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Last Updated</Label>
                  <p className="mt-1 text-sm">
                    {company.updated_at ? new Date(company.updated_at).toLocaleDateString() : "Never"}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Projects</CardTitle>
              <CardDescription>Blog projects associated with this company</CardDescription>
            </div>
            <Badge variant="secondary">{projects.length} Projects</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No projects yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.map((project) => {
                const { label, variant } = getProjectStatusBadge(project.id);
                const wfStatus = workflowStatuses[project.id];
                const isCompleted =
                  wfStatus?.is_complete === true && wfStatus?.approval_status === "approved";
                return (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50"
                  >
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => router.push(`/projects/${project.id}`)}
                    >
                      <p className="font-medium">{project.topic}</p>
                      <p className="text-xs text-muted-foreground">
                        {project.target_word_count} words
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={variant}>{label}</Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={isCompleted}
                        title={isCompleted ? "Completed projects cannot be edited" : "Edit project"}
                        onClick={() => handleEditProject(project)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteProject(project.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={projectDialogOpen} onOpenChange={setProjectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
            <DialogDescription>
              Update project settings for "{editingProject?.topic}"
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateProject} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="target_word_count">Target Word Count</Label>
              <Input
                id="target_word_count"
                type="number"
                min="100"
                max="10000"
                value={projectFormData.target_word_count}
                onChange={(e) => setProjectFormData({ ...projectFormData, target_word_count: parseInt(e.target.value) || 500 })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tone">Content Tone</Label>
              <Select
                value={projectFormData.tone}
                onValueChange={(val) => setProjectFormData({ ...projectFormData, tone: val })}
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

            <div className="space-y-2">
              <Label htmlFor="audience">Target Audience</Label>
              <Input
                id="audience"
                placeholder="e.g., Software Engineers, CTOs, Founders"
                value={projectFormData.audience}
                onChange={(e) => setProjectFormData({ ...projectFormData, audience: e.target.value })}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setProjectDialogOpen(false)} disabled={savingProject}>
                Cancel
              </Button>
              <Button type="submit" disabled={savingProject}>
                {savingProject ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) setDeleteTarget(null);
        }}
        title={deleteTarget?.kind === "company" ? "Delete Company" : "Delete Project"}
        description={
          deleteTarget?.kind === "company"
            ? `Are you sure you want to delete "${deleteTarget.label}"? This will also delete all associated projects. This cannot be undone.`
            : `Are you sure you want to delete "${deleteTarget?.label}"? This cannot be undone.`
        }
        loading={deleting}
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export default function CompanyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const companyId = Number(id);

  return (
    <Suspense fallback={
      <div className="container mx-auto max-w-4xl py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    }>
      <CompanyDetailContent companyId={companyId} />
    </Suspense>
  );
}
