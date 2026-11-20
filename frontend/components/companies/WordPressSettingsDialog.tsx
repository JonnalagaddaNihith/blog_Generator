"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, ExternalLink, ClipboardPaste } from "lucide-react";
import { Company, CompanyUpdate } from "@/lib/types";
import { updateCompany, getWordPressOAuthUrl, exchangeWordPressOAuthCode } from "@/lib/api";
import { WordPressOAuthDialog } from "./WordPressOAuthDialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  company: Company;
  onSuccess: () => void;
}

type Step = "form" | "authorize" | "success";

export function WordPressSettingsDialog({
  open,
  onOpenChange,
  company,
  onSuccess,
}: Props) {
  const [step, setStep] = useState<Step>("form");
  const [formData, setFormData] = useState({
    wp_site: "",
    wp_client_id: "",
    wp_client_secret: "",
    wp_redirect_uri: "http://127.0.0.1:8765/callback",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OAuth state
  const [authUrl, setAuthUrl] = useState<string>("");
  const [oauthState, setOauthState] = useState<string>("");
  const [redirectInput, setRedirectInput] = useState<string>("");
  const [oauthLoading, setOauthLoading] = useState(false);
  const [oauthDialogOpen, setOAuthDialogOpen] = useState(false);

  useEffect(() => {
    if (open && company) {
      setStep("form");
      setFormData({
        wp_site: company.wp_site || "",
        wp_client_id: "",
        wp_client_secret: "",
        wp_redirect_uri: "http://127.0.0.1:8765/callback",
      });
      setError(null);
      setAuthUrl("");
      setOauthState("");
      setRedirectInput("");
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

      // Credentials saved — proceed to OAuth authorization if we have
      // client credentials (new or existing).
      const hasCredentials = !!(formData.wp_client_id || company.wp_configured);
      if (hasCredentials) {
        await startOAuthFlow();
      } else {
        onSuccess();
        onOpenChange(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update WordPress settings");
    } finally {
      setSaving(false);
    }
  };

  const startOAuthFlow = async () => {
    setOauthLoading(true);
    setError(null);
    try {
      const result = await getWordPressOAuthUrl(company.id);
      setAuthUrl(result.authorization_url);
      setOauthState(result.state);
      setStep("authorize");
      window.open(result.authorization_url, "_blank");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start WordPress authorization");
      setStep("form");
    } finally {
      setOauthLoading(false);
    }
  };

  const extractCodeFromUrl = (input: string): string | null => {
    try {
      const url = new URL(input);
      return url.searchParams.get("code");
    } catch {
      return input.trim() || null;
    }
  };

  const handlePasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setRedirectInput(text);
    } catch {
      setError("Failed to read from clipboard. Please paste manually.");
    }
  };

  const handleExchangeCode = async () => {
    const code = extractCodeFromUrl(redirectInput);
    if (!code) {
      setError("Please paste the full redirect URL or the authorization code");
      return;
    }

    setOauthLoading(true);
    setError(null);
    try {
      await exchangeWordPressOAuthCode(company.id, code, oauthState);
      setStep("success");
      setTimeout(() => {
        onSuccess();
        onOpenChange(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to exchange authorization code");
    } finally {
      setOauthLoading(false);
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

  const handleClose = () => {
    onOpenChange(false);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>WordPress.com Settings</DialogTitle>
            <DialogDescription>
              {step === "form" && `Configure WordPress.com integration for ${company.name}`}
              {step === "authorize" && "Authorize WordPress.com access"}
              {step === "success" && "WordPress.com connected"}
            </DialogDescription>
          </DialogHeader>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {step === "form" && (
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
                  <Button type="button" variant="outline" onClick={handleClose} disabled={saving}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={saving || oauthLoading}>
                    {saving || oauthLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {oauthLoading ? "Connecting..." : "Saving..."}
                      </>
                    ) : (
                      company.wp_configured ? "Save Settings" : "Save & Connect"
                    )}
                  </Button>
                </div>
              </DialogFooter>
            </form>
          )}

          {step === "authorize" && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-muted p-4">
                <p className="text-sm font-medium mb-2">Step 1: Authorize in Browser</p>
                <p className="text-sm text-muted-foreground mb-3">
                  A WordPress.com authorization page has been opened in a new tab.
                  Please log in and authorize the application.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(authUrl, "_blank")}
                  className="w-full"
                >
                  <ExternalLink className="mr-2 h-4 w-4" /> Open Authorization Page
                </Button>
              </div>

              <div className="rounded-lg border bg-muted p-4">
                <p className="text-sm font-medium mb-2">Step 2: Paste Redirect URL</p>
                <p className="text-sm text-muted-foreground mb-3">
                  After authorizing, you'll be redirected to a URL like:
                  <br />
                  <code className="text-xs bg-background px-1 py-0.5 rounded">
                    http://127.0.0.1:8765/callback?code=abc123&state=xyz
                  </code>
                  <br />
                  Copy the <strong>entire URL</strong> from your browser's address bar and paste it below.
                </p>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <Label htmlFor="redirect-url">Redirect URL or Code</Label>
                      <Input
                        id="redirect-url"
                        placeholder="Paste the full URL or just the code"
                        value={redirectInput}
                        onChange={(e) => setRedirectInput(e.target.value)}
                      />
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={handlePasteFromClipboard}
                      title="Paste from clipboard"
                      className="mt-6"
                    >
                      <ClipboardPaste className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    You can paste the full URL or just the code value. The code will be extracted automatically.
                  </p>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={handleClose} disabled={oauthLoading}>
                  Cancel
                </Button>
                <Button onClick={handleExchangeCode} disabled={oauthLoading || !redirectInput.trim()}>
                  {oauthLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Verifying...
                    </>
                  ) : (
                    "Complete Authorization"
                  )}
                </Button>
              </DialogFooter>
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <CheckCircle2 className="h-12 w-12 text-green-500" />
              <div className="text-center">
                <p className="font-medium">Successfully Connected!</p>
                <p className="text-sm text-muted-foreground">
                  WordPress.com is now connected to {company.name}
                </p>
              </div>
              <DialogFooter>
                <Button onClick={handleClose}>Close</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <WordPressOAuthDialog
        open={oauthDialogOpen}
        onOpenChange={setOAuthDialogOpen}
        companyId={company.id}
        companyName={company.name}
        onSuccess={onSuccess}
      />
    </>
  );
}
