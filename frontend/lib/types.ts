export interface OutlineSection {
  section: string;
  word_count: number;
  description: string;
}

export interface Company {
  id: number;
  name: string;
  description?: string;
  website?: string;
  created_at: string;
  updated_at?: string;
}

export interface CompanyCreate {
  name: string;
  description?: string;
  website?: string;
}

export interface CompanyUpdate {
  name?: string;
  description?: string;
  website?: string;
}

export interface Project {
  id: number;
  company_id: number;
  topic: string;
  target_word_count: number;
  audience?: string;
  tone?: string;
  status: "draft" | "in_progress" | "completed" | "failed";
  created_at: string;
  updated_at?: string;
}

export interface ProjectCreate {
  company_id: number;
  topic: string;
  target_word_count: number;
  audience?: string;
  tone?: string;
}

export interface ProjectUpdate {
  topic?: string;
  target_word_count?: number;
  audience?: string;
  tone?: string;
  status?: "draft" | "in_progress" | "completed" | "failed";
}

export interface BlogVersion {
  id: number;
  project_id: number;
  outline_id?: number;
  content?: string;
  version: number;
  status: "draft" | "pending_review" | "approved" | "rejected";
  created_at: string;
  updated_at?: string;
}

export interface BlogVersionCreate {
  project_id: number;
  outline_id?: number;
  content?: string;
  version?: number;
}

export interface BlogVersionUpdate {
  content?: string;
}

export interface Outline {
  id: number;
  project_id: number;
  structure?: Record<string, unknown>;
  version: number;
  status: "draft" | "pending_review" | "approved" | "rejected";
  created_at: string;
  updated_at?: string;
}

export interface OutlineCreate {
  project_id: number;
  structure?: Record<string, unknown>;
  version?: number;
}

export interface OutlineUpdate {
  structure?: Record<string, unknown>;
}

export interface Research {
  id: number;
  project_id: number;
  query: string;
  results?: Record<string, unknown>;
  created_at: string;
}

export interface ResearchCreate {
  project_id: number;
  query: string;
  results?: Record<string, unknown>;
}

export interface Keyword {
  id: number;
  project_id: number;
  primary_keywords?: string[];
  secondary_keywords?: string[];
  long_tail_keywords?: string[];
  created_at: string;
  updated_at?: string;
}

export interface KeywordCreate {
  project_id: number;
  primary_keywords?: string[];
  secondary_keywords?: string[];
  long_tail_keywords?: string[];
}

export interface KeywordUpdate {
  primary_keywords?: string[];
  secondary_keywords?: string[];
  long_tail_keywords?: string[];
}

export interface WorkflowStatusResponse {
  project_id: number;
  current_stage: string;
  approval_status: "pending" | "approved" | "rejected" | "regenerate" | "none";
  approval_stage: "blog_strategy" | "final_review" | null;
  is_waiting_approval: boolean;
  next: string[];
  is_complete: boolean;
  outline: {
    strategy?: string;
    outline?: OutlineSection[];
  };
  blog_content: string;
  seo_metadata: {
    title?: string;
    meta_description?: string;
    keyword_density?: Record<string, number>;
    structured_data?: Record<string, unknown>;
    rich_results?: { valid: boolean; errors: string[]; warnings: string[] };
  };
  quality_report: {
    grammar_score?: number;
    readability_score?: number;
    overall_assessment?: string;
    readability_metrics?: Record<string, number>;
    grammar_issue_count?: number;
    grammar_issues?: Array<{ message: string; context: string; suggestions: string[] }>;
  };
  fact_verification_report: {
    claims_verified?: number;
    total_claims?: number;
    confidence_score?: number;
    sources?: Array<{
      claim: string;
      supported: boolean;
      source: string;
      source_url: string;
      issue?: string;
    }>;
  };
  image_details: {
    prompt?: string;
    image_path?: string;
    image_url?: string;
    model_used?: string;
  };
  image_generation_enabled: boolean;
  blog_version_id: number;
}