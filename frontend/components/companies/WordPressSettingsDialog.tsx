"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, ExternalLink } from "lucide-react";
import { Company, CompanyUpdate } from "@/lib/types";
import { updateCompany } from "@/lib/api";
import { WordPressOAuthDialog } from "./WordPressOAuthDialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  company: Company;
  onSuccess: () => void;
}

export function WordPressSettingsDialog({
  open,
  onOpenChange,
  company,
  onSuccess,
}: Props) {
  const [formData, setFormData] = useState({
    wp_site: "",
    wp_client_id: "",
    wp_client_secret: "",
    wp_redirect_uri: "http://127.0.0.1:8765/callback",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [oauthDialogOpen, setOAuthDialogOpen] = useState(false);
  const [autoStartOAuth, setAutoStartOAuth] = useState(false);

  useEffect(() => {
    if (open && company) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset the form each time the dialog opens
      setFormData({
        wp_site: company.wp_site || "",
        wp_client_id: "",
        wp_client_secret: "",
        wp_redirect_uri: "http://127.0.0.1:8765/callback",
      });
      setError(null);
    }
  }, [open, company]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const hasWordPressFields = formData.wp_site || formData.wp_client_id || formData.wp_client_secret;
    if (hasWordPressFields) {
      if (!formData.wp_site) {
        setError("WordPress Site URL is required");
        return;
      }
      if (!formData.wp_client_id && !company.wp_configured) {
        setError("WordPress Client ID is required");
        return;
      }
      if (!formData.wp_client_secret && !company.wp_configured) {
        setError("WordPress Client Secret is required");
        return;
      }
    }

    setSaving(true);
    try {
      const updateData: CompanyUpdate = {};
      if (formData.wp_site) updateData.wp_site = formData.wp_site;
      if (formData.wp_client_id) updateData.wp_client_id = formData.wp_client_id;
      if (formData.wp_client_secret) updateData.wp_client_secret = formData.wp_client_secret;
      if (formData.wp_redirect_uri) updateData.wp_redirect_uri = formData.wp_redirect_uri;

      await updateCompany(company.id, updateData);
      onSuccess();

      // Credentials saved — hand off to the OAuth dialog to authorize.
      const hasCredentials = !!(formData.wp_client_id || company.wp_configured);
      if (hasCredentials) {
        setAutoStartOAuth(true);
        setOAuthDialogOpen(true);
      }
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update WordPress settings");
    } finally {
      setSaving(false);
    }
  };

  const handleClearWordPress = async () => {
    if (!confirm("Are you sure you want to remove WordPress configuration? This will disconnect WordPress publishing.")) {
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await updateCompany(company.id, {
        wp_site: "",
        wp_client_id: "",
        wp_client_secret: "",
        wp_token: "",
        wp_redirect_uri: "",
      });
      onSuccess();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear WordPress settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>WordPress.com Settings</DialogTitle>
            <DialogDescription>
              Configure WordPress.com integration for {company.name}
            </DialogDescription>
          </DialogHeader>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {company.wp_configured && (
              <div className="rounded-lg border bg-green-50 p-3 dark:bg-green-950">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium text-green-800 dark:text-green-200">
                    WordPress is configured
                  </span>
                </div>
                {company.wp_site && (
                  <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                    Site: {company.wp_site}
                  </p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="wp_site">WordPress Site URL *</Label>
              <Input
                id="wp_site"
                placeholder="your-site.wordpress.com"
                value={formData.wp_site}
                onChange={(e) => setFormData({ ...formData, wp_site: e.target.value })}
                required
              />
              <p className="text-xs text-muted-foreground">
                Your WordPress.com site domain (e.g., example.wordpress.com)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="wp_client_id">Client ID *</Label>
              <Input
                id="wp_client_id"
                placeholder="WordPress OAuth Client ID"
                value={formData.wp_client_id}
                onChange={(e) => setFormData({ ...formData, wp_client_id: e.target.value })}
                required={!company.wp_configured}
              />
              {company.wp_configured && (
                <p className="text-xs text-muted-foreground">
                  Leave blank to keep existing Client ID
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="wp_client_secret">Client Secret *</Label>
              <Input
                id="wp_client_secret"
                type="password"
                placeholder="WordPress OAuth Client Secret"
                value={formData.wp_client_secret}
                onChange={(e) => setFormData({ ...formData, wp_client_secret: e.target.value })}
                required={!company.wp_configured}
              />
              {company.wp_configured && (
                <p className="text-xs text-muted-foreground">
                  Leave blank to keep existing Client Secret
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="wp_redirect_uri">Redirect URI</Label>
              <Input
                id="wp_redirect_uri"
                placeholder="http://127.0.0.1:8765/callback"
                value={formData.wp_redirect_uri}
                onChange={(e) => setFormData({ ...formData, wp_redirect_uri: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                Must match your WordPress.com app settings
              </p>
            </div>

            <DialogFooter className="flex-col sm:flex-row gap-2">
              <div className="flex gap-2 w-full sm:w-auto">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClearWordPress}
                  disabled={saving || !company.wp_configured}
                  className="flex-1 sm:flex-none"
                >
                  Remove
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOAuthDialogOpen(true)}
                  disabled={!company.wp_configured}
                  className="flex-1 sm:flex-none"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Reconnect
                </Button>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {company.wp_configured ? "Saving..." : "Connecting..."}
                    </>
                  ) : (
                    company.wp_configured ? "Save Settings" : "Save & Connect"
                  )}
                </Button>
              </div>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <WordPressOAuthDialog
        open={oauthDialogOpen}
        onOpenChange={(open) => {
          setOAuthDialogOpen(open);
          if (!open) setAutoStartOAuth(false);
        }}
        companyId={company.id}
        companyName={company.name}
        onSuccess={onSuccess}
        autoStart={autoStartOAuth}
      />
    </>
  );
}
