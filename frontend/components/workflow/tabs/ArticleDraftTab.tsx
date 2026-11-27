"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { WorkflowStatusResponse } from "@/lib/types";
import { updateWorkflowBlogContent } from "@/lib/api";
import { TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RichTextEditor } from "@/components/ui/RichTextEditor";
import { Edit, Save, X, ImageOff, Loader2 } from "lucide-react";

interface Props {
  blogContent: string;
  isComplete: boolean;
  imageDetails?: WorkflowStatusResponse["image_details"];
  imageGenerationEnabled: boolean;
  projectId: number;
  onRefresh?: () => void;
}

export function ArticleDraftTab({
  blogContent,
  isComplete,
  imageDetails,
  imageGenerationEnabled,
  projectId,
  onRefresh,
}: Props) {
  const [editingContent, setEditingContent] = useState(false);
  const [editedContent, setEditedContent] = useState(blogContent);
  const [savingContent, setSavingContent] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL;
  const imageUrl = imageDetails?.image_path
    ? `${apiBase}/projects/${projectId}/workflow/image`
    : null;

  const handleStartEdit = () => {
    setEditedContent(blogContent);
    setEditingContent(true);
  };

  const handleCancelEdit = () => {
    setEditedContent(blogContent);
    setEditingContent(false);
  };

  const handleSaveContent = async () => {
    setSavingContent(true);
    try {
      await updateWorkflowBlogContent(projectId, editedContent);
      setEditingContent(false);
      if (onRefresh) {
        await onRefresh();
      }
    } catch (err) {
      console.error("Failed to save blog content:", err);
    } finally {
      setSavingContent(false);
    }
  };

  return (
    <TabsContent value="article">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-semibold">Article Draft</CardTitle>
              {!isComplete && !editingContent && (
                <Button variant="outline" size="sm" onClick={handleStartEdit}>
                  <Edit className="mr-2 h-4 w-4 text-primary hover:text-primary/80 transition-colors" /> Edit Content
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {editingContent ? (
              <div className="space-y-4">
                <RichTextEditor
                  content={editedContent}
                  onChange={setEditedContent}
                  editable={true}
                />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={handleCancelEdit} disabled={savingContent}>
                    <X className="mr-2 h-4 w-4" /> Cancel
                  </Button>
                  <Button onClick={handleSaveContent} disabled={savingContent}>
                    {savingContent ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" /> Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ ...props }) => (
                      <a
                        {...props}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline visited:text-blue-900 dark:text-blue-400 dark:visited:text-blue-300"
                      />
                    ),
                  }}
                >
                  {blogContent}
                </ReactMarkdown>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Featured Image</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {imageUrl ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  key={imageDetails?.image_path}
                  src={imageUrl}
                  alt="Generated featured image"
                  className="w-full rounded-md border object-cover"
                />
                {imageDetails?.model_used && (
                  <p className="text-xs text-muted-foreground">
                    Model: {imageDetails.model_used}
                  </p>
                )}
              </>
            ) : imageGenerationEnabled ? (
              <div className="flex flex-col items-center gap-2 py-8 text-center text-sm text-muted-foreground">
                <ImageOff className="h-8 w-8 opacity-50" />
                <p>No image generated yet.</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center text-sm text-muted-foreground">
                <ImageOff className="h-8 w-8 opacity-50" />
                <p>Image generation is disabled.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </TabsContent>
  );
}
