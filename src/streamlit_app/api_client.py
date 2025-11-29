import os
import pandas as pd
from typing import Any, Optional

import requests

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIClient:
    """Client pour communiquer avec l'API FastAPI."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30) -> None:
        self.base_url = {
            base_url 
            or os.getenv("STREAMLIT_API_URL")
            or os.getenv("API_BASE_URL")
            or "http://localhost:8000"}
        self.timeout = timeout

    def get_health(self) -> dict[str, Any]:
        """Vérifie le statut de santé de l'API."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_offers(
        self,
        keyword: Optional[str] = None,
        departement: Optional[str] = None,
        type_contrat: Optional[str] = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        payload = {
            "keyword": keyword or None,
            "departement": departement or None,
            "rome_code": None,
            "type_contrat": type_contrat or None,
            "page": 1,
            "size": limit,
        }
        resp = requests.post(
            f"{API_URL}/offers/search", 
            json=payload, 
            timeout=self.timeout,
            )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return pd.DataFrame()

        df = pd.DataFrame(items)
        return df

    def load_filters_values(self) -> tuple[list[str], list[str]]:

        df = self.fetch_offers(limit=500)
        if df.empty:
            return [], []

        deps: list[str] = []
        if "departement" in df.columns:
            deps = sorted(
                d for d in df["departement"].dropna().astype(str).unique().tolist() 
                if d.strip()
            )
        contrats: list[str] = []
        if "type_contrat" in df.columns:
            contrats = sorted(
                c for c in df["type_contrat"].dropna().astype(str).unique().tolist() 
                if c.strip()
            )
        return deps, contrats
