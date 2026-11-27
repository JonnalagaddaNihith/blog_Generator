"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
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
  Link2,
} from "lucide-react";
import { Button } from "./button";
import { Separator } from "./separator";
import { Input } from "./input";

interface RichTextEditorProps {
  content: string; // markdown content
  onChange: (content: string) => void; // callback with markdown content
  editable?: boolean;
}

function ToolbarButton({
  onClick,
  isActive,
  disabled,
  children,
}: {
  onClick: () => void;
  isActive?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
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
}

export function RichTextEditor({
  content,
  onChange,
  editable = true,
}: RichTextEditorProps) {
  const turndownService = useMemo(() => new TurndownService({
    headingStyle: "atx",
    codeBlockStyle: "fenced",
  }), []);
  const [linkPopoverOpen, setLinkPopoverOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const linkPopoverRef = useRef<HTMLDivElement>(null);

  // Convert markdown to HTML for Tiptap
  const markdownToHtml = (markdown: string): string => {
    return marked.parse(markdown) as string;
  };

  // Convert HTML from Tiptap back to markdown
  const htmlToMarkdown = useCallback((html: string): string => {
    return turndownService.turndown(html);
  }, [turndownService]);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        link: {
          openOnClick: false,
          autolink: true,
          linkOnPaste: true,
          HTMLAttributes: {
            target: "_blank",
            rel: "noopener noreferrer",
          },
        },
      }),
    ],
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
  }, [content, editor, htmlToMarkdown]);

  // Close the link popover when clicking outside it
  useEffect(() => {
    if (!linkPopoverOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (
        linkPopoverRef.current &&
        !linkPopoverRef.current.contains(e.target as Node)
      ) {
        setLinkPopoverOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [linkPopoverOpen]);

  if (!editor) {
    return null;
  }

  const openLinkPopover = () => {
    const existing = editor.getAttributes("link").href as string | undefined;
    setLinkUrl(existing || "");
    setLinkPopoverOpen((open) => !open);
  };

  const applyLink = () => {
    const url = linkUrl.trim();
    if (!url) {
      editor.chain().focus().unsetLink().run();
    } else {
      const href = /^https?:\/\//i.test(url) ? url : `https://${url}`;
      editor.chain().focus().setLink({ href }).run();
    }
    setLinkPopoverOpen(false);
  };

  return (
    <div className="border rounded-md">
      {editable && (
        <div className="sticky top-0 z-10 flex flex-wrap items-center gap-1 border-b p-2 bg-muted">
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
          <div className="relative" ref={linkPopoverRef}>
            <ToolbarButton
              onClick={openLinkPopover}
              isActive={editor.isActive("link")}
            >
              <Link2 className="h-4 w-4" />
            </ToolbarButton>
            {linkPopoverOpen && (
              <div className="absolute left-0 top-10 z-20 flex w-72 items-center gap-2 rounded-md border bg-background p-2 shadow-md">
                <Input
                  type="url"
                  placeholder="https://example.com"
                  value={linkUrl}
                  onChange={(e) => setLinkUrl(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      applyLink();
                    }
                  }}
                  className="h-8 text-sm"
                  autoFocus
                />
                <Button size="sm" className="h-8" onClick={applyLink}>
                  Apply
                </Button>
                {editor.isActive("link") && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8"
                    onClick={() => {
                      editor.chain().focus().unsetLink().run();
                      setLinkPopoverOpen(false);
                    }}
                  >
                    Remove
                  </Button>
                )}
              </div>
            )}
          </div>
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
      <div className="max-h-[70vh] overflow-y-auto">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
