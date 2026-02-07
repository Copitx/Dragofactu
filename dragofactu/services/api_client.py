"""
API Client for Dragofactu Backend.
Handles all HTTP communication with the FastAPI backend.
Includes offline cache support: caches GET responses and falls back
to cached data when the server is unreachable.
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('dragofactu.api_client')


@dataclass
class TokenData:
    """Stores authentication tokens."""
    access_token: str
    refresh_token: str
    user_id: str
    company_id: str
    username: str
    role: str


class APIError(Exception):
    """Exception raised for API errors."""
    def __init__(self, message: str, status_code: int = 0, detail: str = ""):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class APIClient:
    """
    HTTP client for Dragofactu API.

    Usage:
        client = APIClient("http://localhost:8000")
        client.login("admin", "password")
        clients = client.list_clients()
    """

    def __init__(self, base_url: str = None):
        """Initialize API client."""
        self.base_url = (base_url or os.getenv("API_URL", "http://localhost:8000")).rstrip("/")
        self.api_prefix = "/api/v1"
        self._token_data: Optional[TokenData] = None
        self._session = requests.Session()
        self._token_file = Path.home() / ".dragofactu" / "api_tokens.json"

        # Try to load saved tokens
        self._load_tokens()

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid tokens."""
        return self._token_data is not None

    @property
    def current_user(self) -> Optional[Dict]:
        """Get current user info."""
        if not self._token_data:
            return None
        return {
            "user_id": self._token_data.user_id,
            "company_id": self._token_data.company_id,
            "username": self._token_data.username,
            "role": self._token_data.role
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self._token_data:
            headers["Authorization"] = f"Bearer {self._token_data.access_token}"
        return headers

    def _url(self, endpoint: str) -> str:
        """Build full URL for endpoint."""
        return f"{self.base_url}{self.api_prefix}{endpoint}"

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response, raising errors if needed."""
        if response.status_code == 401:
            # Try to refresh token
            if self._token_data and self._refresh_token():
                # Retry would need to be handled by caller
                pass
            raise APIError("No autorizado", 401, "Token invalido o expirado")

        if response.status_code == 403:
            raise APIError("Acceso denegado", 403, "No tienes permiso")

        if response.status_code == 404:
            raise APIError("No encontrado", 404)

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", "Error desconocido")
            except:
                detail = response.text
            raise APIError(f"Error {response.status_code}", response.status_code, detail)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except:
            return {"raw": response.text}

    def _endpoint_to_cache_key(self, endpoint: str) -> Optional[str]:
        """Map API endpoint to cache entity key."""
        # Only cache list endpoints
        mapping = {
            "/clients": "clients",
            "/products": "products",
            "/documents": "documents",
            "/workers": "workers",
            "/diary": "diary",
            "/suppliers": "suppliers",
            "/reminders": "reminders",
            "/dashboard/stats": "dashboard_stats",
        }
        for path, key in mapping.items():
            if endpoint == path:
                return key
        return None

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with offline cache support.

        - GET requests: cache response on success, fall back to cache on failure
        - Write requests: raise error on failure (caller can queue if needed)
        """
        url = self._url(endpoint)
        headers = self._get_headers()
        cache_key = self._endpoint_to_cache_key(endpoint) if method.upper() == "GET" else None

        try:
            response = self._session.request(
                method, url, headers=headers, timeout=30, **kwargs
            )
            result = self._handle_response(response)

            # Cache successful GET responses
            if cache_key and method.upper() == "GET":
                try:
                    from dragofactu.services.offline_cache import get_cache, get_connectivity_monitor
                    get_cache().save(cache_key, result)
                    get_connectivity_monitor().set_online()
                except Exception as e:
                    logger.debug(f"Cache save error (non-critical): {e}")

            return result

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
            # Mark as offline
            try:
                from dragofactu.services.offline_cache import get_connectivity_monitor
                get_connectivity_monitor().set_offline()
            except Exception:
                pass

            # For GET requests, try to serve from cache
            if cache_key:
                try:
                    from dragofactu.services.offline_cache import get_cache
                    cached = get_cache().load(cache_key, max_age=0)  # Accept any age when offline
                    if cached is not None:
                        logger.info(f"Serving {cache_key} from offline cache")
                        # Mark as cached so UI can show indicator
                        if isinstance(cached, dict):
                            cached["_from_cache"] = True
                        return cached
                except Exception as e:
                    logger.debug(f"Cache load error: {e}")

            # No cache available
            if isinstance(conn_err, requests.exceptions.Timeout):
                raise APIError("Timeout", 0, "La solicitud tardo demasiado")
            raise APIError("Error de conexion", 0, f"No se puede conectar a {self.base_url}")

    def _save_tokens(self):
        """Save tokens to file."""
        if not self._token_data:
            return
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": self._token_data.access_token,
            "refresh_token": self._token_data.refresh_token,
            "user_id": self._token_data.user_id,
            "company_id": self._token_data.company_id,
            "username": self._token_data.username,
            "role": self._token_data.role
        }
        self._token_file.write_text(json.dumps(data))

    def _load_tokens(self):
        """Load tokens from file."""
        if self._token_file.exists():
            try:
                data = json.loads(self._token_file.read_text())
                self._token_data = TokenData(**data)
            except:
                self._token_data = None

    def _clear_tokens(self):
        """Clear saved tokens."""
        self._token_data = None
        if self._token_file.exists():
            self._token_file.unlink()

    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token.

        Only clears tokens if server explicitly rejects (401/403).
        Network errors preserve tokens for retry.
        """
        if not self._token_data:
            return False
        try:
            response = self._session.post(
                self._url("/auth/refresh"),
                headers={"Content-Type": "application/json"},
                json={"refresh_token": self._token_data.refresh_token},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self._token_data.access_token = data["access_token"]
                self._save_tokens()
                return True
            elif response.status_code in (401, 403):
                # Server explicitly rejected - tokens are invalid
                self._clear_tokens()
                return False
            else:
                # Other server error, keep tokens for retry
                return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Network error - don't clear tokens, keep for later retry
            return False
        except Exception:
            # Unknown error - don't clear tokens
            return False

    # ==================== AUTH ====================

    def login(self, username: str, password: str) -> Dict:
        """Login and store tokens."""
        response = self._request("POST", "/auth/login", json={
            "username": username,
            "password": password
        })

        user = response.get("user", {})
        self._token_data = TokenData(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            user_id=user.get("id", ""),
            company_id=user.get("company_id", ""),
            username=user.get("username", ""),
            role=user.get("role", "")
        )
        self._save_tokens()
        return response

    def logout(self):
        """Logout and clear tokens."""
        try:
            self._request("POST", "/auth/logout")
        except:
            pass
        self._clear_tokens()

    def register(self, company_code: str, company_name: str, username: str,
                 email: str, password: str, **kwargs) -> Dict:
        """Register new company and admin user."""
        return self._request("POST", "/auth/register", json={
            "company_code": company_code,
            "company_name": company_name,
            "username": username,
            "email": email,
            "password": password,
            **kwargs
        })

    def get_me(self) -> Dict:
        """Get current user info from API."""
        return self._request("GET", "/auth/me")

    # ==================== CLIENTS ====================

    def list_clients(self, skip: int = 0, limit: int = 50, search: str = None,
                     active_only: bool = True) -> Dict:
        """List clients."""
        params = {"skip": skip, "limit": limit, "active_only": active_only}
        if search:
            params["search"] = search
        return self._request("GET", "/clients", params=params)

    def get_client(self, client_id: str) -> Dict:
        """Get client by ID."""
        return self._request("GET", f"/clients/{client_id}")

    def create_client(self, code: str, name: str, **kwargs) -> Dict:
        """Create client."""
        return self._request("POST", "/clients", json={"code": code, "name": name, **kwargs})

    def update_client(self, client_id: str, **kwargs) -> Dict:
        """Update client."""
        return self._request("PUT", f"/clients/{client_id}", json=kwargs)

    def delete_client(self, client_id: str) -> Dict:
        """Delete client (soft)."""
        return self._request("DELETE", f"/clients/{client_id}")

    # ==================== PRODUCTS ====================

    def list_products(self, skip: int = 0, limit: int = 50, search: str = None,
                      category: str = None, low_stock: bool = False) -> Dict:
        """List products."""
        params = {"skip": skip, "limit": limit, "low_stock": low_stock}
        if search:
            params["search"] = search
        if category:
            params["category"] = category
        return self._request("GET", "/products", params=params)

    def get_product(self, product_id: str) -> Dict:
        """Get product by ID."""
        return self._request("GET", f"/products/{product_id}")

    def create_product(self, code: str, name: str, **kwargs) -> Dict:
        """Create product."""
        return self._request("POST", "/products", json={"code": code, "name": name, **kwargs})

    def update_product(self, product_id: str, **kwargs) -> Dict:
        """Update product."""
        return self._request("PUT", f"/products/{product_id}", json=kwargs)

    def delete_product(self, product_id: str) -> Dict:
        """Delete product (soft)."""
        return self._request("DELETE", f"/products/{product_id}")

    def adjust_stock(self, product_id: str, quantity: int, reason: str) -> Dict:
        """Adjust product stock."""
        return self._request("POST", f"/products/{product_id}/adjust-stock", json={
            "product_id": product_id,
            "quantity": quantity,
            "reason": reason
        })

    # ==================== SUPPLIERS ====================

    def list_suppliers(self, skip: int = 0, limit: int = 50, search: str = None) -> Dict:
        """List suppliers."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        return self._request("GET", "/suppliers", params=params)

    def get_supplier(self, supplier_id: str) -> Dict:
        return self._request("GET", f"/suppliers/{supplier_id}")

    def create_supplier(self, code: str, name: str, **kwargs) -> Dict:
        return self._request("POST", "/suppliers", json={"code": code, "name": name, **kwargs})

    def update_supplier(self, supplier_id: str, **kwargs) -> Dict:
        return self._request("PUT", f"/suppliers/{supplier_id}", json=kwargs)

    def delete_supplier(self, supplier_id: str) -> Dict:
        return self._request("DELETE", f"/suppliers/{supplier_id}")

    # ==================== DOCUMENTS ====================

    def list_documents(self, skip: int = 0, limit: int = 50, doc_type: str = None,
                       doc_status: str = None, client_id: str = None) -> Dict:
        """List documents."""
        params = {"skip": skip, "limit": limit}
        if doc_type:
            params["doc_type"] = doc_type
        if doc_status:
            params["doc_status"] = doc_status
        if client_id:
            params["client_id"] = client_id
        return self._request("GET", "/documents", params=params)

    def get_document(self, document_id: str) -> Dict:
        """Get document with lines."""
        return self._request("GET", f"/documents/{document_id}")

    def create_document(self, doc_type: str, client_id: str, issue_date: str,
                        lines: List[Dict], **kwargs) -> Dict:
        """Create document with lines."""
        return self._request("POST", "/documents", json={
            "type": doc_type,
            "client_id": client_id,
            "issue_date": issue_date,
            "lines": lines,
            **kwargs
        })

    def update_document(self, document_id: str, **kwargs) -> Dict:
        """Update document (only DRAFT)."""
        return self._request("PUT", f"/documents/{document_id}", json=kwargs)

    def delete_document(self, document_id: str) -> Dict:
        """Delete document (only DRAFT)."""
        return self._request("DELETE", f"/documents/{document_id}")

    def change_document_status(self, document_id: str, new_status: str) -> Dict:
        """Change document status."""
        return self._request("POST", f"/documents/{document_id}/change-status",
                           json={"new_status": new_status})

    def convert_document(self, document_id: str, target_type: str) -> Dict:
        """Convert quote to invoice/delivery_note."""
        return self._request("POST", f"/documents/{document_id}/convert",
                           params={"target_type": target_type})

    def get_documents_summary(self) -> Dict:
        """Get documents summary for dashboard."""
        return self._request("GET", "/documents/stats/summary")

    # ==================== WORKERS ====================

    def list_workers(self, skip: int = 0, limit: int = 50, search: str = None,
                     department: str = None) -> Dict:
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        if department:
            params["department"] = department
        return self._request("GET", "/workers", params=params)

    def get_worker(self, worker_id: str) -> Dict:
        return self._request("GET", f"/workers/{worker_id}")

    def create_worker(self, code: str, first_name: str, last_name: str, **kwargs) -> Dict:
        return self._request("POST", "/workers", json={
            "code": code, "first_name": first_name, "last_name": last_name, **kwargs
        })

    def update_worker(self, worker_id: str, **kwargs) -> Dict:
        return self._request("PUT", f"/workers/{worker_id}", json=kwargs)

    def delete_worker(self, worker_id: str) -> Dict:
        return self._request("DELETE", f"/workers/{worker_id}")

    def add_course(self, worker_id: str, name: str, **kwargs) -> Dict:
        return self._request("POST", f"/workers/{worker_id}/courses",
                           json={"name": name, **kwargs})

    # ==================== DIARY ====================

    def list_diary_entries(self, skip: int = 0, limit: int = 50,
                           date_from: str = None, date_to: str = None) -> Dict:
        params = {"skip": skip, "limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._request("GET", "/diary", params=params)

    def get_diary_entry(self, entry_id: str) -> Dict:
        return self._request("GET", f"/diary/{entry_id}")

    def create_diary_entry(self, title: str, content: str, entry_date: str, **kwargs) -> Dict:
        return self._request("POST", "/diary", json={
            "title": title, "content": content, "entry_date": entry_date, **kwargs
        })

    def update_diary_entry(self, entry_id: str, **kwargs) -> Dict:
        return self._request("PUT", f"/diary/{entry_id}", json=kwargs)

    def delete_diary_entry(self, entry_id: str) -> Dict:
        return self._request("DELETE", f"/diary/{entry_id}")

    # ==================== REMINDERS ====================

    def list_reminders(self, pending_only: bool = True, priority: str = None) -> Dict:
        params = {"pending_only": pending_only}
        if priority:
            params["priority"] = priority
        return self._request("GET", "/reminders", params=params)

    def get_reminder(self, reminder_id: str) -> Dict:
        return self._request("GET", f"/reminders/{reminder_id}")

    def create_reminder(self, title: str, **kwargs) -> Dict:
        return self._request("POST", "/reminders", json={"title": title, **kwargs})

    def update_reminder(self, reminder_id: str, **kwargs) -> Dict:
        return self._request("PUT", f"/reminders/{reminder_id}", json=kwargs)

    def complete_reminder(self, reminder_id: str) -> Dict:
        return self._request("POST", f"/reminders/{reminder_id}/complete")

    def delete_reminder(self, reminder_id: str) -> Dict:
        return self._request("DELETE", f"/reminders/{reminder_id}")

    # ==================== DASHBOARD ====================

    def get_dashboard_stats(self) -> Dict:
        """Get aggregated dashboard statistics."""
        return self._request("GET", "/dashboard/stats")
    
    def get_document_pdf(self, document_id: str) -> bytes:
        """Get PDF for document as bytes."""
        response = self._session.get(
            f"{self.base_url}{self.api_prefix}/documents/{document_id}/pdf",
            headers=self._get_headers(),
            timeout=30
        )
        if response.status_code == 200:
            return response.content
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", "")
                if error_detail:
                    error_msg = f"{error_msg}: {error_detail}"
            except:
                pass
            raise APIError(f"Error generating PDF: {error_msg}", response.status_code)

    # ==================== HEALTH ====================

    def health_check(self) -> Dict:
        """Check API health."""
        try:
            response = self._session.get(f"{self.base_url}/health", timeout=5)
            return response.json()
        except:
            return {"status": "unreachable"}


# Singleton instance for easy access
_api_client: Optional[APIClient] = None

def get_api_client(base_url: str = None) -> APIClient:
    """Get or create API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = APIClient(base_url)
    elif base_url and _api_client.base_url != base_url.rstrip("/"):
        # URL changed, create new instance
        _api_client = APIClient(base_url)
    return _api_client


def reset_api_client():
    """Reset the singleton API client instance."""
    global _api_client
    _api_client = None
