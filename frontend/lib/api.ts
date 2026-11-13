import {
  WorkflowStatusResponse,
  OutlineSection,
  Company,
  CompanyCreate,
  CompanyUpdate,
  Project,
  ProjectCreate,
  ProjectUpdate,
  BlogVersion,
  BlogVersionUpdate,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

// Company API
export async function createCompany(data: CompanyCreate): Promise<Company> {
  const res = await fetch(`${API_BASE}/companies/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create company");
  return res.json();
}

export async function getCompanies(skip = 0, limit = 100): Promise<Company[]> {
  const res = await fetch(`${API_BASE}/companies/?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch companies");
  return res.json();
}

export async function getCompany(companyId: number): Promise<Company> {
  const res = await fetch(`${API_BASE}/companies/${companyId}`);
  if (!res.ok) throw new Error("Failed to fetch company");
  return res.json();
}

export async function updateCompany(companyId: number, data: CompanyUpdate): Promise<Company> {
  const res = await fetch(`${API_BASE}/companies/${companyId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update company");
  return res.json();
}

export async function deleteCompany(companyId: number): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/companies/${companyId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete company");
  return res.json();
}

// Project API
export async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function getProjects(skip = 0, limit = 100, companyId?: number): Promise<Project[]> {
  const url = companyId
    ? `${API_BASE}/projects/?skip=${skip}&limit=${limit}&company_id=${companyId}`
    : `${API_BASE}/projects/?skip=${skip}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function getProject(projectId: number): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return res.json();
}

export async function updateProject(projectId: number, data: ProjectUpdate): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to update project" }));
    throw new Error(errorData.detail || "Failed to update project");
  }
  return res.json();
}

export async function deleteProject(projectId: number): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete project");
  return res.json();
}

// Workflow API
export async function startWorkflow(projectId: number): Promise<{ message: string; project_id: number; thread_id: string }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/workflow/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to start workflow");
  return res.json();
}

export async function getWorkflowStatus(projectId: number): Promise<WorkflowStatusResponse> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/workflow/status`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch workflow status");
  return res.json();
}

export async function resumeWorkflow(
  projectId: number,
  payload: {
    action: "approve" | "reject" | "regenerate";
    updated_outline?: { strategy?: string; outline: OutlineSection[] };
    regenerate_section?: "outline" | "blog_content" | "seo" | "image" | "verification" | "all";
  }
): Promise<{ message: string; project_id: number; current_stage: string }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/workflow/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to resume workflow" }));
    throw new Error(errorData.detail || "Failed to resume workflow");
  }
  return res.json();
}

export async function updateWorkflowOutline(projectId: number, updatedOutline: Record<string, unknown>): Promise<{ message: string; project_id: number }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/workflow/outline`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updatedOutline),
  });
  if (!res.ok) throw new Error("Failed to update outline");
  return res.json();
}

// Blog API
export async function getBlogs(projectId: number): Promise<BlogVersion[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/blogs`);
  if (!res.ok) throw new Error("Failed to fetch blogs");
  return res.json();
}

export async function getBlog(blogId: number): Promise<BlogVersion> {
  const res = await fetch(`${API_BASE}/blogs/${blogId}`);
  if (!res.ok) throw new Error("Failed to fetch blog");
  return res.json();
}

export async function updateBlog(blogId: number, data: BlogVersionUpdate): Promise<BlogVersion> {
  const res = await fetch(`${API_BASE}/blogs/${blogId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update blog");
  return res.json();
}

export async function updateWorkflowBlogContent(projectId: number, content: string): Promise<{ message: string; project_id: number }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/workflow/blog_content`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to update blog content" }));
    throw new Error(errorData.detail || "Failed to update blog content");
  }
  return res.json();
}

export async function approveBlog(blogId: number): Promise<BlogVersion> {
  const res = await fetch(`${API_BASE}/blogs/${blogId}/approve`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to approve blog");
  return res.json();
}

export async function rejectBlog(blogId: number): Promise<BlogVersion> {
  const res = await fetch(`${API_BASE}/blogs/${blogId}/reject`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to reject blog");
  return res.json();
}

// Export API
export async function exportPdf(blogId: number): Promise<{ message: string; blog_id: number; pdf_filename: string; download_url: string }> {
  const res = await fetch(`${API_BASE}/blogs/${blogId}/export/pdf`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to export PDF");
  return res.json();
}