"""HTTP client for customer-side Custom SQL publishing connectors.

The connector is a small FastAPI app deployed on the customer's website
backend. It owns the database credentials and performs validated
insert/update operations against an allow-listed table. This client only
ever speaks to that connector over HTTPS with a bearer token.
"""

import ipaddress
import os
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urljoin

import httpx


class SqlConnectorError(Exception):
    """Raised when the remote publishing connector call fails."""
    pass


class SsrfError(SqlConnectorError):
    """Raised when a connector URL fails SSRF validation."""
    pass


def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_connector_url(url: str, allow_private: Optional[bool] = None) -> str:
    """Validate a connector URL against SSRF rules.

    - Only http/https schemes allowed.
    - Hostname is resolved and every resolved address must be public,
      unless allow_private is enabled (development only).
    - Plain HTTP is allowed only for localhost-style hosts in dev mode.

    Returns the normalized base URL (no trailing slash).
    """
    if allow_private is None:
        allow_private = os.getenv("SQL_CONNECTOR_ALLOW_PRIVATE", "").lower() in ("1", "true", "yes")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SsrfError("Connector URL must use http:// or https://")
    if not parsed.hostname:
        raise SsrfError("Connector URL has no hostname")
    if parsed.username or parsed.password:
        raise SsrfError("Connector URL must not contain embedded credentials")

    host = parsed.hostname
    is_local_host = (
        host in ("localhost", "127.0.0.1", "::1", "host.docker.internal", "gateway.docker.internal")
        or host.endswith(".local")
    )

    if parsed.scheme == "http" and not (allow_private and is_local_host):
        raise SsrfError("Connector URL must use HTTPS (plain HTTP is only allowed for localhost in development)")

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SsrfError(f"Cannot resolve connector host '{host}': {exc}") from exc

    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if _ip_is_blocked(addr) and not (allow_private and (is_local_host or addr.is_loopback)):
            raise SsrfError(f"Connector host '{host}' resolves to a private/reserved address")

    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    return base


class SqlConnectorClient:
    """Synchronous HTTP client for the customer-side publishing connector."""

    def __init__(
        self,
        connector_url: str,
        api_token: str,
        timeout: int = 30,
        allow_private: Optional[bool] = None,
    ):
        self.base_url = validate_connector_url(connector_url, allow_private=allow_private)
        self.api_token = api_token
        self.timeout = timeout
        self.http = httpx.Client(timeout=timeout)

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
        }
        try:
            response = self.http.request(method, url, headers=headers, **kwargs)
            if response.status_code == 401:
                raise SqlConnectorError("Connector rejected the API token (401 Unauthorized)")
            if response.status_code == 403:
                raise SqlConnectorError("Connector denied access (403 Forbidden)")
            if response.status_code >= 400:
                detail = ""
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        detail = body.get("detail") or body.get("message") or ""
                except ValueError:
                    detail = response.text[:200]
                raise SqlConnectorError(f"Connector error HTTP {response.status_code}: {detail}")
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()
        except httpx.TimeoutException:
            raise SqlConnectorError(f"Connector request timed out after {self.timeout}s")
        except httpx.RequestError as e:
            raise SqlConnectorError(f"Cannot reach connector: {type(e).__name__}")
        except SqlConnectorError:
            raise
        except ValueError as e:
            raise SqlConnectorError(f"Connector returned invalid JSON: {e}")

    def health(self) -> Dict[str, Any]:
        """Check connector health and database connectivity."""
        return self._request("GET", "/health")

    def list_tables(self) -> List[Dict[str, Any]]:
        """List authorized tables and their columns."""
        data = self._request("GET", "/tables")
        tables = data.get("tables", data if isinstance(data, list) else [])
        return tables

    def list_columns(self, table: str) -> List[Dict[str, Any]]:
        """List columns of an authorized table."""
        data = self._request("GET", f"/tables/{table}/columns")
        columns = data.get("columns", data if isinstance(data, list) else [])
        return columns

    def upsert_blog(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a blog record via the connector.

        payload: {table, column_mapping, record, dedupe_column?, status_column?, status_value?}
        Returns {action, external_id, url}.
        """
        return self._request("POST", "/blogs/upsert", json=payload)

    def get_record(self, table: str, column: str, value: str) -> Optional[Dict[str, Any]]:
        """Look up an existing record by a unique column (used for dedupe checks)."""
        try:
            return self._request(
                "GET", f"/records/lookup",
                params={"table": table, "column": column, "value": value},
            )
        except SqlConnectorError:
            return None

    def close(self):
        self.http.close()
