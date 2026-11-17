"use client";

import { useRouter } from "next/navigation";
import { Project, WorkflowStatusResponse } from "@/lib/types";
import { getProjectStatusBadge, isProjectCompleted } from "./statusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, FolderOpen, Plus, Trash2 } from "lucide-react";

interface Props {
  projects: Project[];
  workflowStatuses: Record<number, WorkflowStatusResponse>;
  onNewProject: () => void;
  onEditProject: (project: Project) => void;
  onDeleteProject: (projectId: number) => void;
}

export function ProjectsListCard({
  projects,
  workflowStatuses,
  onNewProject,
  onEditProject,
  onDeleteProject,
}: Props) {
  const router = useRouter();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Projects</CardTitle>
            <CardDescription>Blog projects associated with this company</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{projects.length} Projects</Badge>
            <Button size="sm" onClick={onNewProject}>
              <Plus className="mr-2 h-4 w-4" /> New Project
            </Button>
          </div>
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
              const { label, variant } = getProjectStatusBadge(workflowStatuses[project.id]);
              const isCompleted = isProjectCompleted(workflowStatuses[project.id]);
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
                      onClick={() => onEditProject(project)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onDeleteProject(project.id)}
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
  );
}
