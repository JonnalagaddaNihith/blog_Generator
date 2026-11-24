"use client";

import { useState, useEffect, useCallback } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, ExternalLink, CheckCircle2, ClipboardPaste } from "lucide-react";
import { getWordPressOAuthUrl, exchangeWordPressOAuthCode } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  companyId: number;
  companyName: string;
  onSuccess: () => void;
  autoStart?: boolean;
}

export function WordPressOAuthDialog({
  open,
  onOpenChange,
  companyId,
  companyName,
  onSuccess,
  autoStart = false,
}: Props) {
  const [step, setStep] = useState<"init" | "authorize" | "callback" | "success">("init");
  const [authUrl, setAuthUrl] = useState<string>("");
  const [state, setState] = useState<string>("");
  const [redirectInput, setRedirectInput] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartOAuth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getWordPressOAuthUrl(companyId);
      setAuthUrl(result.authorization_url);
      setState(result.state);
      setStep("authorize");
      // Open authorization URL in new tab
      window.open(result.authorization_url, "_blank");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get OAuth URL");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (open && autoStart) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentionally kick off OAuth when the dialog opens
      handleStartOAuth();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only auto-start when the dialog opens
  }, [open, autoStart]);

  const extractCodeFromUrl = (input: string): string | null => {
    try {
      // If it's a full URL, parse it
      const url = new URL(input);
      return url.searchParams.get("code");
    } catch {
      // If it's just the code, return it directly
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
      setError("Please enter the authorization code or paste the full redirect URL");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await exchangeWordPressOAuthCode(companyId, code, state);
      setStep("success");
      setTimeout(() => {
        onSuccess();
        onOpenChange(false);
        // Reset state
        setStep("init");
        setAuthUrl("");
        setState("");
        setRedirectInput("");
        setError(null);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to exchange authorization code");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    onOpenChange(false);
    // Reset state
    setStep("init");
    setAuthUrl("");
    setState("");
    setRedirectInput("");
    setError(null);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Connect to WordPress.com</DialogTitle>
          <DialogDescription>
            Authorize {companyName} to publish blogs to WordPress.com
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {step === "init" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Click the button below to authorize this application to access your WordPress.com account.
                You will be redirected to WordPress.com to complete the authorization.
              </p>
              <Button onClick={handleStartOAuth} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading...
                  </>
                ) : (
                  <>
                    <ExternalLink className="mr-2 h-4 w-4" /> Connect to WordPress
                  </>
                )}
              </Button>
            </div>
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
                  After authorizing, you&apos;ll be redirected to a URL like:
                  <br />
                  <code className="text-xs bg-background px-1 py-0.5 rounded">
                    http://127.0.0.1:8765/callback?code=abc123&state=xyz
                  </code>
                  <br />
                  Copy the <strong>entire URL</strong> from your browser&apos;s address bar and paste it below.
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

              <Button onClick={handleExchangeCode} disabled={loading || !redirectInput.trim()} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Verifying...
                  </>
                ) : (
                  "Complete Authorization"
                )}
              </Button>
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <CheckCircle2 className="h-12 w-12 text-green-500" />
              <div className="text-center">
                <p className="font-medium">Successfully Connected!</p>
                <p className="text-sm text-muted-foreground">
                  WordPress.com is now connected to {companyName}
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            {step === "success" ? "Close" : "Cancel"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
