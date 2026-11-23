"use client";

import { useState, useEffect, useCallback, Suspense, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Company, CompanyUpdate, Project, WorkflowStatusResponse, ProjectUpdate } from "@/lib/types";
import { getCompany, updateCompany, deleteCompany, getProjects, getWorkflowStatus, updateProject, deleteProject } from "@/lib/api";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Breadcrumb,BreadcrumbItem,BreadcrumbLink,BreadcrumbList,BreadcrumbPage,BreadcrumbSeparator} from "@/components/ui/breadcrumb";
import { Home, Loader2, Building2 } from "lucide-react";
import { CompanyDetailCard, CompanyFormData } from "@/components/companies/CompanyDetailCard";
import { ProjectsListCard } from "@/components/companies/ProjectsListCard";
import { ProjectEditDialog, ProjectEditFormData } from "@/components/companies/ProjectEditDialog";
import { WordPressSettingsDialog } from "@/components/companies/WordPressSettingsDialog";

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
  const [wordPressSettingsOpen, setWordPressSettingsOpen] = useState(false);

  const [formData, setFormData] = useState<CompanyFormData>({
    name: "",
    description: "",
    website: "",
  });

  const [projectFormData, setProjectFormData] = useState<ProjectEditFormData>({
    target_word_count: 500,
    audience: "",
    tone: "",
  });

  const loadCompany = useCallback(async () => {
    try {
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
  }, [companyId]);

  const loadProjects = useCallback(async () => {
    try {
      const data = await getProjects(0, 100, companyId);
      setProjects(data);
      // Load workflow status for each project
      const statusEntries = await Promise.all(
        data.map(async (project) => {
          try {
            const status = await getWorkflowStatus(project.id);
            return [project.id, status] as const;
          } catch (err) {
            console.error(`Failed to load workflow status for project ${project.id}:`, err);
            return null;
          }
        })
      );
      setWorkflowStatuses(Object.fromEntries(statusEntries.filter((e) => e !== null)));
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  }, [companyId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch on mount
    loadCompany();
    loadProjects();
  }, [loadCompany, loadProjects]);

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
      const updateData: CompanyUpdate = {
        name: formData.name,
        description: formData.description || undefined,
        website: formData.website || undefined,
      };

      const updated = await updateCompany(companyId, updateData);
      setCompany(updated);
      setEditing(false);
      setError(null); // Clear any previous errors
    } catch (err) {
      console.error("Failed to update company:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to update company";
      setError(errorMessage);
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

  if (!company) {
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

      <CompanyDetailCard
        company={company}
        editing={editing}
        formData={formData}
        saving={saving}
        error={error}
        onEdit={() => setEditing(true)}
        onCancelEdit={() => setEditing(false)}
        onFormChange={setFormData}
        onSubmit={handleUpdate}
        onDelete={handleDelete}
        onWordPressSettings={() => setWordPressSettingsOpen(true)}
      />

      <ProjectsListCard
        projects={projects}
        workflowStatuses={workflowStatuses}
        onNewProject={() => router.push(`/projects?company_id=${companyId}`)}
        onEditProject={handleEditProject}
        onDeleteProject={handleDeleteProject}
      />

      <ProjectEditDialog
        open={projectDialogOpen}
        project={editingProject}
        formData={projectFormData}
        saving={savingProject}
        onOpenChange={setProjectDialogOpen}
        onFormChange={setProjectFormData}
        onSubmit={handleUpdateProject}
      />

      <WordPressSettingsDialog
        open={wordPressSettingsOpen}
        onOpenChange={setWordPressSettingsOpen}
        company={company}
        onSuccess={loadCompany}
      />

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