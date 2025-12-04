import logging
import os
from functools import lru_cache
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)


class APIClient:
    """Client pour communiquer avec l'API FastAPI."""

    def __init__(self, timeout: int = 30) -> None:
        self.base_url = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")

        self.timeout = timeout

        self.session = self._create_session()

        logger.info(f"APIClient initialisé - URL: {self.base_url}")

    def _create_session(self) -> requests.Session:
        """
        Crée une session HTTP avec retry strategy.

        Amélioration : Retry automatique en cas d'erreur temporaire.
        """
        session = requests.Session()

        # Configuration du retry
        retry_strategy = Retry(
            total=3,  # 3 tentatives
            backoff_factor=1,  # Attendre 1s entre les tentatives
            status_forcelist=[429, 500, 502, 503, 504],  # Codes HTTP à retry
            allowed_methods=["HEAD", "GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get_health(self) -> dict[str, Any]:
        """Vérifie le statut de santé de l'API."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_offers(
        self,
        keyword: str | None = None,
        departement: str | None = None,
        type_contrat: str | None = None,
        rome_code: str | None = None,
        limit: int = 200,
        date_from: str | None = None,
    ) -> pd.DataFrame:

        payload = {
            "keyword": keyword,
            "departement": departement,
            "rome_code": rome_code,
            "type_contrat": type_contrat,
            "page": 1,
            "size": limit,
            "date_from": date_from,
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            logger.info(f"Fetching offers with filters: {payload}")

            response = self.session.post(
                f"{self.base_url}/offers/search",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            if not items:
                logger.warning("No offers found with current filters")
                return pd.DataFrame()

            df = pd.DataFrame(items)
            logger.info(f"Fetched {len(df)} offers successfully")

            return df

        except requests.Timeout:
            logger.error("Request timeout - API took too long to respond")
            raise Exception("⏱️ La requête a pris trop de temps. Réessayez avec moins de résultats.")

        except requests.HTTPError as e:
            if e.response.status_code == 422:
                logger.error("Validation error in request")
                raise Exception("❌ Erreur de validation. Vérifiez vos filtres.")
            elif e.response.status_code == 404:
                logger.error("Endpoint not found")
                raise Exception("❌ L'API n'est pas accessible. Vérifiez la configuration.")
            else:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"❌ Erreur HTTP {e.response.status_code}")

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"❌ Erreur de connexion à l'API : {str(e)}")

    @lru_cache(maxsize=10)  # Cache avec @lru_cache pour éviter des appels répétés
    def load_filters_values(self) -> tuple[list[str], list[str]]:

        try:
            logger.info("Loading filter values...")

            # Récupérer un échantillon d'offres pour extraire les valeurs
            df = self.fetch_offers(limit=500)

            if df.empty:
                logger.warning("No data available for filters")
                return [], []

            # Extraire les départements
            deps: list[str] = []
            if "departement" in df.columns:
                deps = sorted(
                    d
                    for d in df["departement"].dropna().astype(str).unique().tolist()
                    if d.strip() and d != "None"
                )

            # Extraire les types de contrat
            contrats: list[str] = []
            if "type_contrat" in df.columns:
                contrats = sorted(
                    c
                    for c in df["type_contrat"].dropna().astype(str).unique().tolist()
                    if c.strip() and c != "None"
                )

            logger.info(f"Loaded {len(deps)} departments and {len(contrats)} contract types")

            return deps, contrats

        except Exception as e:
            logger.error(f"Failed to load filters: {e}")
            return [], []

    def get_statistics(self) -> dict[str, Any]:

        try:
            response = self.session.get(f"{self.base_url}/stats/global", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def get_timeline_data(self, days: int = 30) -> pd.DataFrame:

        try:
            response = self.session.get(
                f"{self.base_url}/stats/timeline", params={"days": days}, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            return pd.DataFrame(data)

        except requests.RequestException as e:
            logger.error(f"Failed to get timeline: {e}")
            return pd.DataFrame()

    def get_department_stats(self, limit: int = 20) -> pd.DataFrame:

        try:
            response = self.session.get(
                f"{self.base_url}/stats/departements", params={"limit": limit}, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            return pd.DataFrame(data)

        except requests.RequestException as e:
            logger.error(f"Failed to get department stats: {e}")
            return pd.DataFrame()

    def close(self):
        """Ferme la session HTTP proprement."""
        if hasattr(self, "session"):
            self.session.close()
            logger.info("APIClient session closed")
