"""
app/agents/base.py
------------------
Abstract base agent class and unified HTTP dispatcher utility.
Enforces that every agent implementation has a single responsibility
and returns strictly structured JSON data.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests

from utils.logger import logger

_DEFAULT_API_BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")


class BaseAgent(ABC):
    """
    Abstract interface for all domain agents.
    Every sub-agent must return a JSON-serializable dictionary.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the domain agent (e.g. 'sales', 'inventory', 'knowledge')."""
        pass

    @abstractmethod
    def run(self, question: str = "") -> Dict[str, Any]:
        """
        Execute domain-specific data retrieval and analysis.

        Returns
        -------
        dict[str, Any]
            Structured key-value pairs (numerical, boolean, or categorical).
            MUST NOT contain free-form conversational prose.
        """
        pass


def call_api(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    base_url: Optional[str] = None,
    timeout: float = 8.0,
) -> Dict[str, Any]:
    """
    Make an internal HTTP request to an existing platform API endpoint.

    Parameters
    ----------
    endpoint : str
        API path (e.g. '/api/sales/recommendation' or '/api/ml/inventory/predict').
    method : str
        HTTP method ('GET', 'POST', 'DELETE').
    json_data : dict, optional
        Payload for POST requests.
    params : dict, optional
        Query parameters for GET requests.
    base_url : str, optional
        Base server URL (defaults to http://127.0.0.1:5001).
    timeout : float
        Request timeout in seconds.

    Returns
    -------
    dict[str, Any]
        Parsed JSON response or error payload dictionary.
    """
    root = (base_url or _DEFAULT_API_BASE).rstrip("/")
    url = f"{root}{endpoint}" if endpoint.startswith("/") else f"{root}/{endpoint}"

    try:
        if method.upper() == "POST":
            resp = requests.post(url, json=json_data, params=params, timeout=timeout)
        else:
            resp = requests.get(url, params=params, timeout=timeout)

        if resp.status_code in (200, 201):
            return resp.json()
        
        logger.warning(f"[call_api] {method} {url} returned status {resp.status_code}: {resp.text[:150]}")
        return {"status": "error", "status_code": resp.status_code, "message": resp.text}
    except Exception as exc:
        logger.error(f"[call_api] Request failed for {method} {url}: {exc}")
        return {"status": "error", "message": str(exc)}
