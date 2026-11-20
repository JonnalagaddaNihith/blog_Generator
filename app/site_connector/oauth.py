"""WordPress.com OAuth authorization flow for obtaining access tokens.

Adapted from the reference oauth_setup.py for this project.
"""

import secrets
from typing import Dict, Any, Optional
from urllib.parse import urlencode

import httpx


def get_authorization_url(client_id: str, redirect_uri: str) -> tuple[str, str]:
    """
    Generate WordPress.com OAuth authorization URL and state.
    
    Uses global scope as required by the wp/v2 API.
    
    Returns:
        Tuple of (authorization_url, state)
    """
    state = secrets.token_urlsafe(32)
    auth_url = "https://public-api.wordpress.com/oauth2/authorize?" + urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "global",
        "state": state,
    })
    return auth_url, state


def exchange_code_for_token(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    site: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Exchange authorization code for access token.
    
    Args:
        client_id: WordPress.com OAuth client ID
        client_secret: WordPress.com OAuth client secret
        code: Authorization code from callback
        redirect_uri: OAuth redirect URI (must match app settings)
        site: Optional WordPress site to verify access after token exchange
        
    Returns:
        Dictionary with access_token, scope, blog_id, blog_url, token_type, expires_in
        
    Raises:
        RuntimeError: If token exchange fails
    """
    # Exchange authorization code for access token
    response = httpx.post("https://public-api.wordpress.com/oauth2/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=20)
    
    if response.is_error:
        raise RuntimeError(f"Token exchange failed: HTTP {response.status_code}")
    
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError("No access token returned")
    
    # Verify global scope was granted
    granted = str(data.get("scope") or "").strip()
    if granted and "global" not in granted.replace(",", " ").split():
        raise RuntimeError("WordPress did not grant global scope")
    
    # Verify the actual authenticated wp/v2 endpoint if site is provided
    # Skip verification if site is not provided or if endpoint returns 404
    if site:
        # Extract just the domain from the site URL if full URL is provided
        site_domain = site.replace("https://", "").replace("http://", "").rstrip("/")
        # WordPress.com REST API v2 endpoint format
        test_url = f"https://public-api.wordpress.com/wp/v2/sites/{site_domain}/posts"
        try:
            probe = httpx.get(
                test_url,
                headers={"Authorization": f"Bearer {data['access_token']}",
                         "Accept": "application/json"},
                params={"slug": "diagnostic-nonexistent-slug", "status": "any"},
                timeout=20,
            )
        except httpx.RequestError as exc:
            # If network error, don't fail - token might still be valid
            pass
        else:
            # Only fail if it's a real permission error (401/403), not 404
            if probe.status_code in (401, 403):
                error_code = "unknown"
                try:
                    error_info = probe.json()
                    if isinstance(error_info, dict):
                        error_code = str(error_info.get("code") or error_info.get("error") or "unknown")
                except ValueError:
                    pass
                raise RuntimeError(f"Token cannot read target site's posts (HTTP {probe.status_code}, code={error_code})")
            # 404 is OK - might mean site doesn't exist yet or endpoint format issue
    
    return {
        "access_token": data["access_token"],
        "scope": data.get("scope"),
        "blog_id": data.get("blog_id"),
        "blog_url": data.get("blog_url"),
        "token_type": data.get("token_type"),
        "expires_in": data.get("expires_in"),
    }
