"use client";

import { useCallback, useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Plus, Trash2, Pencil, PlugZap, Database, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { Company, SqlDatabaseType, SqlTableInfo, SqlWebsite } from "@/lib/types";
import {
  createSqlWebsite,
  deleteSqlWebsite,
  getSqlWebsiteSchema,
  getSqlWebsites,
  testSqlWebsite,
  updateSqlWebsite,
} from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  company: Company;
}

const DATABASE_TYPES: { value: SqlDatabaseType; label: string }[] = [
  { value: "mysql", label: "MySQL" },
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mariadb", label: "MariaDB" },
  { value: "sqlite", label: "SQLite" },
  { value: "mssql", label: "Microsoft SQL Server" },
];

// Canonical blog fields that can be mapped to SQL columns
const BLOG_FIELD_LABELS: { field: string; label: string }[] = [
  { field: "title", label: "Title" },
  { field: "slug", label: "Slug" },
  { field: "content_html", label: "Content (HTML)" },
  { field: "excerpt", label: "Excerpt" },
  { field: "meta_title", label: "SEO Title" },
  { field: "meta_description", label: "SEO Description" },
  { field: "image_url", label: "Featured Image URL" },
  { field: "status", label: "Status" },
  { field: "keywords", label: "Keywords" },
  { field: "categories", label: "Categories" },
  { field: "tags", label: "Tags" },
];

const NONE = "__none__";

interface FormState {
  name: string;
  website_url: string;
  database_type: SqlDatabaseType;
  connector_url: string;
  api_token: string;
  table_name: string;
  column_mapping: Record<string, string>;
}

const emptyForm: FormState = {
  name: "",
  website_url: "",
  database_type: "mysql",
  connector_url: "",
  api_token: "",
  table_name: "",
  column_mapping: {},
};

function statusBadge(status: string) {
  if (status === "connected") return <Badge className="bg-green-600">Connected</Badge>;
  if (status === "error") return <Badge variant="destructive">Error</Badge>;
  return <Badge variant="secondary">Untested</Badge>;
}

/** Heuristic auto-mapping: match blog fields to column names. */
function autoMapFields(columns: string[]): Record<string, string> {
  const aliases: Record<string, string[]> = {
    title: ["title", "blog_title", "post_title", "headline"],
    slug: ["slug", "blog_slug", "post_slug", "url_slug"],
    content_html: ["content", "blog_content", "post_content", "body", "content_html", "article_body"],
    excerpt: ["excerpt", "blog_excerpt", "summary", "description_short"],
    meta_title: ["meta_title", "seo_title", "seo_title_tag"],
    meta_description: ["meta_description", "seo_description", "meta_desc"],
    image_url: ["image_url", "featured_image", "featured_image_url", "thumbnail_url", "image"],
    status: ["status", "publish_status", "post_status", "state"],
    keywords: ["keywords", "meta_keywords", "tags_csv"],
    categories: ["categories", "category", "post_categories"],
    tags: ["tags", "post_tags"],
  };
  const normalized = columns.map((c) => ({ raw: c, norm: c.toLowerCase().replace(/[^a-z0-9]/g, "") }));
  const mapping: Record<string, string> = {};
  for (const [field, names] of Object.entries(aliases)) {
    for (const alias of names) {
      const match = normalized.find((c) => c.norm === alias.replace(/[^a-z0-9]/g, ""));
      if (match) {
        mapping[field] = match.raw;
        break;
      }
    }
  }
  return mapping;
}

export function SqlWebsitesDialog({ open, onOpenChange, company }: Props) {
  const [websites, setWebsites] = useState<SqlWebsite[]>([]);
  const [loading, setLoading] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<SqlWebsite | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Schema/mapping state (only for persisted websites)
  const [schema, setSchema] = useState<SqlTableInfo[]>([]);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [mappingWebsiteId, setMappingWebsiteId] = useState<number | null>(null);

  const loadWebsites = useCallback(async () => {
    setLoading(true);
    try {
      setWebsites(await getSqlWebsites(company.id));
    } catch (err) {
      toast.error("Failed to load SQL websites", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setLoading(false);
    }
  }, [company.id]);

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reload list each time dialog opens
      loadWebsites();
      setEditorOpen(false);
      setEditing(null);
      setError(null);
    }
  }, [open, loadWebsites]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setEditorOpen(true);
  };

  const openEdit = (w: SqlWebsite) => {
    setEditing(w);
    setForm({
      name: w.name,
      website_url: w.website_url || "",
      database_type: w.database_type,
      connector_url: w.connector_url,
      api_token: "",
      table_name: w.table_name || "",
      column_mapping: { ...(w.column_mapping || {}) },
    });
    setError(null);
    setEditorOpen(true);
  };

  const handleSave = async (andTest: boolean) => {
    setError(null);
    if (!form.name.trim()) return setError("Website name is required");
    if (!form.connector_url.trim()) return setError("Connector URL is required");
    if (!editing && !form.api_token.trim()) return setError("API token is required");

    setSaving(true);
    try {
      let websiteId: number;
      if (editing) {
        const payload: Parameters<typeof updateSqlWebsite>[1] = {
          name: form.name.trim(),
          website_url: form.website_url || undefined,
          database_type: form.database_type,
          connector_url: form.connector_url.trim(),
          table_name: form.table_name || undefined,
          column_mapping: Object.keys(form.column_mapping).length ? form.column_mapping : undefined,
        };
        if (form.api_token.trim()) payload.api_token = form.api_token.trim();
        await updateSqlWebsite(editing.id, payload);
        websiteId = editing.id;
      } else {
        const created = await createSqlWebsite({
          company_id: company.id,
          name: form.name.trim(),
          website_url: form.website_url || undefined,
          database_type: form.database_type,
          connector_url: form.connector_url.trim(),
          api_token: form.api_token.trim(),
          table_name: form.table_name || undefined,
          column_mapping: Object.keys(form.column_mapping).length ? form.column_mapping : undefined,
        });
        websiteId = created.id;
      }

      if (andTest) {
        const result = await testSqlWebsite(websiteId);
        toast.success(result.success ? "Connection successful" : "Saved, but connection test failed", {
          description: result.message,
        });
      } else {
        toast.success(editing ? "SQL website updated" : "SQL website added");
      }
      setEditorOpen(false);
      await loadWebsites();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save SQL website");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (websiteId: number) => {
    setTesting(websiteId);
    try {
      const result = await testSqlWebsite(websiteId);
      if (result.success) {
        toast.success("Connection successful", { description: result.message });
      } else {
        toast.error("Connection test failed", { description: result.message });
      }
      await loadWebsites();
    } catch (err) {
      toast.error("Connection test failed", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setTesting(null);
    }
  };

  const handleDelete = async (website: SqlWebsite) => {
    if (!confirm(`Remove "${website.name}"? Publishing history is kept, but the connection will be gone.`)) return;
    try {
      await deleteSqlWebsite(website.id);
      toast.success("SQL website removed");
      await loadWebsites();
    } catch (err) {
      toast.error("Failed to remove", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  const loadSchema = async (websiteId: number) => {
    setSchemaLoading(true);
    setMappingWebsiteId(websiteId);
    try {
      const data = await getSqlWebsiteSchema(websiteId);
      setSchema(data.tables || []);
      if (!data.tables?.length) {
        toast.info("No authorized tables returned by the connector");
      }
    } catch (err) {
      toast.error("Failed to load schema", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
      setSchema([]);
    } finally {
      setSchemaLoading(false);
    }
  };

  const saveMapping = async (website: SqlWebsite, tableName: string, mapping: Record<string, string>) => {
    try {
      await updateSqlWebsite(website.id, {
        table_name: tableName,
        column_mapping: mapping,
      });
      toast.success("Table mapping saved");
      await loadWebsites();
    } catch (err) {
      toast.error("Failed to save mapping", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Custom Website (SQL Database)</DialogTitle>
            <DialogDescription>
              Connect {company.name}&apos;s custom website by deploying the publishing connector on its backend.
              The connector holds the database credentials — never enter DB passwords here.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : websites.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                <Database className="mx-auto mb-2 h-8 w-8 opacity-50" />
                No custom websites connected yet.
              </div>
            ) : (
              websites.map((w) => (
                <div key={w.id} className="rounded-lg border p-3 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{w.name}</span>
                        {statusBadge(w.status)}
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {DATABASE_TYPES.find((d) => d.value === w.database_type)?.label} · {w.connector_url}
                      </p>
                      {w.table_name && (
                        <p className="text-xs text-muted-foreground">
                          Table: <code>{w.table_name}</code>
                          {w.column_mapping ? ` · ${Object.keys(w.column_mapping).length} fields mapped` : ""}
                        </p>
                      )}
                      {w.last_test_message && w.status === "error" && (
                        <p className="text-xs text-destructive truncate">{w.last_test_message}</p>
                      )}
                    </div>
                    <div className="flex gap-1 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTest(w.id)}
                        disabled={testing === w.id}
                      >
                        {testing === w.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlugZap className="h-4 w-4" />}
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => openEdit(w)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(w)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <Label className="text-xs font-semibold text-muted-foreground">Table &amp; Field Mapping</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (mappingWebsiteId === w.id) {
                          setMappingWebsiteId(null);
                        } else {
                          setMappingWebsiteId(w.id);
                          void loadSchema(w.id);
                        }
                      }}
                      disabled={schemaLoading}
                    >
                      {mappingWebsiteId === w.id ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      <span className="ml-1">{mappingWebsiteId === w.id ? "Hide" : "Configure"}</span>
                    </Button>
                  </div>

                  {mappingWebsiteId === w.id && (
                    <div className="rounded-md bg-muted/50 p-3 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">
                          {schemaLoading ? "Loading schema..." : schema.length ? `${schema.length} authorized table(s)` : "No tables loaded"}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => loadSchema(w.id)}
                          disabled={schemaLoading}
                        >
                          {schemaLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                          <span className="ml-1">Refresh</span>
                        </Button>
                      </div>
                      {schemaLoading ? (
                        <div className="flex justify-center py-3">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      ) : schema.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          Test the connection first, then refresh to load authorized tables.
                        </p>
                      ) : (
                        <>
                          <Select
                            value={w.table_name || ""}
                            onValueChange={(table) => {
                              const t = schema.find((s) => s.name === table);
                              const cols = t?.columns.map((c) => c.name) || [];
                              const suggested = autoMapFields(cols);
                              const merged = { ...suggested };
                              // Preserve explicit user choices for this table
                              if (w.table_name === table && w.column_mapping) {
                                for (const [f, c] of Object.entries(w.column_mapping)) {
                                  if (cols.includes(c)) merged[f] = c;
                                }
                              }
                              void saveMapping(w, table, merged);
                            }}
                          >
                            <SelectTrigger className="h-8 text-xs">
                              <SelectValue placeholder="Select table" />
                            </SelectTrigger>
                            <SelectContent>
                              {schema.map((t) => (
                                <SelectItem key={t.name} value={t.name}>
                                  {t.name} ({t.columns.length} columns)
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {w.table_name && (
                            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                              {BLOG_FIELD_LABELS.map(({ field, label }) => {
                                const selectedTable = schema.find((t) => t.name === w.table_name);
                                const tableColumns = selectedTable?.columns.map((c) => c.name) || [];
                                return (
                                  <div key={field} className="flex items-center gap-2">
                                    <span className="w-32 shrink-0 text-xs text-muted-foreground">{label}</span>
                                    <Select
                                      value={w.column_mapping?.[field] || NONE}
                                      onValueChange={(col) => {
                                        const next = { ...(w.column_mapping || {}) };
                                        if (col === NONE) delete next[field];
                                        else next[field] = col;
                                        void saveMapping(w, w.table_name!, next);
                                      }}
                                    >
                                      <SelectTrigger className="h-7 flex-1 text-xs">
                                        <SelectValue placeholder="—" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value={NONE}>— not mapped —</SelectItem>
                                        {tableColumns.map((c) => (
                                          <SelectItem key={c} value={c}>{c}</SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
            <Button onClick={openCreate}>
              <Plus className="mr-2 h-4 w-4" /> Add Website
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Editor dialog */}
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit SQL Website" : "Add SQL Website"}</DialogTitle>
            <DialogDescription>
              Point to the publishing connector deployed on the website&apos;s backend.
            </DialogDescription>
          </DialogHeader>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="sql_name">Website Name *</Label>
              <Input id="sql_name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Company Blog" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="sql_site">Website URL</Label>
              <Input id="sql_site" value={form.website_url} onChange={(e) => setForm({ ...form, website_url: e.target.value })} placeholder="https://blog.example.com" />
              <p className="text-xs text-muted-foreground">Used for &quot;view live&quot; links after publishing.</p>
            </div>
            <div className="space-y-1.5">
              <Label>Database Type *</Label>
              <Select value={form.database_type} onValueChange={(v) => setForm({ ...form, database_type: v as SqlDatabaseType })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {DATABASE_TYPES.map((d) => (
                    <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="sql_connector">Connector URL *</Label>
              <Input id="sql_connector" value={form.connector_url} onChange={(e) => setForm({ ...form, connector_url: e.target.value })} placeholder="https://blog.example.com/api/connector" />
              <p className="text-xs text-muted-foreground">HTTPS URL of the deployed connector (must not be a private/internal address).</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="sql_token">API Token {editing ? "" : "*"}</Label>
              <Input id="sql_token" type="password" value={form.api_token} onChange={(e) => setForm({ ...form, api_token: e.target.value })} placeholder={editing ? "Leave blank to keep existing token" : "Connector bearer token"} />
              <p className="text-xs text-muted-foreground">Stored encrypted. Must match CONNECTOR_API_TOKENS on the connector.</p>
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => setEditorOpen(false)} disabled={saving}>Cancel</Button>
            <Button variant="outline" onClick={() => handleSave(true)} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlugZap className="mr-2 h-4 w-4" />}
              Save &amp; Test
            </Button>
            <Button onClick={() => handleSave(false)} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {editing ? "Save" : "Add Website"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
