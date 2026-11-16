"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";
import { marked } from "marked";
import TurndownService from "turndown";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Heading3,
  Undo,
  Redo,
} from "lucide-react";
import { Button } from "./button";
import { Separator } from "./separator";

interface RichTextEditorProps {
  content: string; // markdown content
  onChange: (content: string) => void; // callback with markdown content
  editable?: boolean;
}

export function RichTextEditor({
  content,
  onChange,
  editable = true,
}: RichTextEditorProps) {
  const turndownService = new TurndownService({
    headingStyle: "atx",
    codeBlockStyle: "fenced",
  });

  // Convert markdown to HTML for Tiptap
  const markdownToHtml = (markdown: string): string => {
    return marked.parse(markdown) as string;
  };

  // Convert HTML from Tiptap back to markdown
  const htmlToMarkdown = (html: string): string => {
    return turndownService.turndown(html);
  };

  const editor = useEditor({
    extensions: [StarterKit],
    content: markdownToHtml(content),
    editable,
    immediatelyRender: true,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      const markdown = htmlToMarkdown(html);
      onChange(markdown);
    },
    editorProps: {
      attributes: {
        class:
          "prose prose-neutral dark:prose-invert max-w-none focus:outline-none min-h-[400px] px-4 py-2",
      },
    },
  });

  // Update editor content when markdown prop changes
  useEffect(() => {
    if (editor && content !== htmlToMarkdown(editor.getHTML())) {
      editor.commands.setContent(markdownToHtml(content));
    }
  }, [content, editor]);

  if (!editor) {
    return null;
  }

  const ToolbarButton = ({
    onClick,
    isActive,
    disabled,
    children,
  }: {
    onClick: () => void;
    isActive?: boolean;
    disabled?: boolean;
    children: React.ReactNode;
  }) => (
    <Button
      type="button"
      variant={isActive ? "secondary" : "ghost"}
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className="h-8 w-8 p-0"
    >
      {children}
    </Button>
  );

  return (
    <div className="border rounded-md">
      {editable && (
        <div className="flex flex-wrap items-center gap-1 border-b p-2 bg-muted/50">
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            isActive={editor.isActive("bold")}
          >
            <Bold className="h-4 w-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            isActive={editor.isActive("italic")}
          >
            <Italic className="h-4 w-4" />
          </ToolbarButton>
          <Separator orientation="vertical" className="h-6 mx-1" />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            isActive={editor.isActive("heading", { level: 1 })}
          >
            <Heading1 className="h-4 w-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            isActive={editor.isActive("heading", { level: 2 })}
          >
            <Heading2 className="h-4 w-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            isActive={editor.isActive("heading", { level: 3 })}
          >
            <Heading3 className="h-4 w-4" />
          </ToolbarButton>
          <Separator orientation="vertical" className="h-6 mx-1" />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            isActive={editor.isActive("bulletList")}
          >
            <List className="h-4 w-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            isActive={editor.isActive("orderedList")}
          >
            <ListOrdered className="h-4 w-4" />
          </ToolbarButton>
          <Separator orientation="vertical" className="h-6 mx-1" />
          <ToolbarButton
            onClick={() => {
              if (editor.can().undo()) {
                editor.chain().focus().undo().run();
              }
            }}
            disabled={!editor.can().undo()}
          >
            <Undo className="h-4 w-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => {
              if (editor.can().redo()) {
                editor.chain().focus().redo().run();
              }
            }}
            disabled={!editor.can().redo()}
          >
            <Redo className="h-4 w-4" />
          </ToolbarButton>
        </div>
      )}
      <EditorContent editor={editor} />
    </div>
  );
}
