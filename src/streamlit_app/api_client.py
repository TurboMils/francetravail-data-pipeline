import os
from typing import Any, cast

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from config.logging_config import get_logger

logger = get_logger(__name__)


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
        data: Any = response.json()
        return cast(dict[str, Any], data)

    def fetch_offers(
        self,
        keyword: list[str] | None = None,
        departement: list[str] | None = None,
        type_contrat: list[str] | None = None,
        experience: list[str] | None = None,
        page: int = 1,
        limit: int = 50,
        date_from: str | None = None,
    ) -> tuple[pd.DataFrame, int]:
        payload = {
            "keyword": keyword,
            "departement": departement,
            "experience": experience,
            "type_contrat": type_contrat,
            "page": page,
            "size": limit,
            "date_from": date_from,
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        logger.info(f"Payload :  {payload}")

        try:
            logger.info(f"Fetching offers with filters: {payload}")

            response = self.session.post(
                f"{self.base_url}/offers/search",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, dict):
                raise ValueError("Réponse /offers/search invalide (dict attendu).")

            items = data.get("items", [])
            total = data.get("total", 0)

            if not items:
                logger.warning("No offers found with current filters")
                return pd.DataFrame(), 0

            df = pd.DataFrame(items)
            logger.info(
                f"Fetched {len(df)} offers successfully (page={page}, size={limit}, total={total})"
            )

            return df, total

        except requests.Timeout as e:
            # Pas de e.response garanti sur Timeout
            logger.error("Request timeout - API took too long to respond")
            raise Exception(
                "La requête a pris trop de temps. Réessayez avec moins de résultats."
            ) from e

        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if e.response is not None and e.response.status_code == 422:
                logger.error("Validation error in request")
                raise Exception(
                    f"Erreur de validation. Vérifiez vos filtres. Payload : {payload}"
                ) from e
            elif e.response is not None and e.response.status_code == 404:
                logger.error("Endpoint not found")
                raise Exception("L'API n'est pas accessible. Vérifiez la configuration.") from e
            else:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"Erreur HTTP {status_code}") from e

        except requests.RequestException as e:
            # Erreurs réseau génériques (connexion refusée, DNS, etc.)
            logger.error(f"Request error: {e}")
            raise Exception(f"Erreur de connexion à l'API : {str(e)}") from e

    def load_filters_values(self) -> tuple[list[str], list[str], list[str]]:
        """
        Charge les listes de valeurs pour les filtres (type contrat, départements, expérience).
        Résultat mis en cache au niveau de l'instance.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/filters",
                timeout=self.timeout,
            )
            response.raise_for_status()

            data: Any = response.json()

            if not isinstance(data, dict):
                raise ValueError("Réponse /filters invalide (dict attendu).")

            contrat_raw = data.get("contrat", [])
            deps_raw = data.get("departements", [])
            experience_raw = data.get("experience", [])

            if (
                not isinstance(contrat_raw, list)
                or not isinstance(deps_raw, list)
                or not isinstance(experience_raw, list)
            ):
                raise ValueError(
                    "Champs 'contrat', 'departements' et 'experience' doivent être des listes."
                )

            contrat_type = [str(v) for v in contrat_raw if v is not None]
            departements = [str(v) for v in deps_raw if v is not None]
            experience = [str(v) for v in experience_raw if v is not None]

            return departements, contrat_type, experience

        except requests.RequestException as e:
            logger.error(f"Erreur lors du chargement des filtres: {e}")
            return [], [], []

    def get_statistics(
        self,
        keyword: list[str] | None = None,
        departement: list[str] | None = None,
        type_contrat: list[str] | None = None,
        experience: list[str] | None = None,
        date_from: str | None = None,
    ) -> tuple[int, int, int, str | None]:
        payload: dict[str, Any] = {
            "keyword": keyword,
            "departement": departement,
            "experience": experience,
            "type_contrat": type_contrat,
            "date_from": date_from,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = self.session.post(
                f"{self.base_url}/stats/global",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data: Any = response.json()
            if not isinstance(data, dict):
                raise ValueError("Réponse /stats/global invalide (dict attendu).")

            total_offers = data.get("total_offers", 0)
            total_departments = data.get("total_departments", 0)
            total_companies = data.get("total_companies", 0)
            last_date = data.get("last_date")

            return int(total_offers), int(total_departments), int(total_companies), last_date
        except requests.RequestException as e:
            logger.error(f"Failed to get global statistics: {e}")
            return 0, 0, 0, None

    def get_department_stats(
        self,
        keyword: list[str] | None = None,
        departement: list[str] | None = None,
        type_contrat: list[str] | None = None,
        experience: list[str] | None = None,
        date_from: str | None = None,
    ) -> pd.DataFrame:
        payload: dict[str, Any] = {
            "keyword": keyword,
            "departement": departement,
            "experience": experience,
            "type_contrat": type_contrat,
            "date_from": date_from,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = self.session.post(
                f"{self.base_url}/stats/departements",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data: Any = response.json()
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except requests.RequestException as e:
            logger.error(f"Failed to get department stats: {e}")
            return pd.DataFrame()

    def get_contrat_stats(
        self,
        keyword: list[str] | None = None,
        departement: list[str] | None = None,
        type_contrat: list[str] | None = None,
        experience: list[str] | None = None,
        date_from: str | None = None,
    ) -> pd.DataFrame:
        payload: dict[str, Any] = {
            "keyword": keyword,
            "departement": departement,
            "experience": experience,
            "type_contrat": type_contrat,
            "date_from": date_from,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = self.session.post(
                f"{self.base_url}/stats/contrats",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data: Any = response.json()
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except requests.RequestException as e:
            logger.error(f"Failed to get contrat stats: {e}")
            return pd.DataFrame()

    def get_timeline_data(
        self,
        keyword: list[str] | None = None,
        departement: list[str] | None = None,
        type_contrat: list[str] | None = None,
        experience: list[str] | None = None,
        date_from: str | None = None,
    ) -> pd.DataFrame:
        payload: dict[str, Any] = {
            "keyword": keyword,
            "departement": departement,
            "experience": experience,
            "type_contrat": type_contrat,
            "date_from": date_from,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = self.session.post(
                f"{self.base_url}/stats/timeline",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data: Any = response.json()
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except requests.RequestException as e:
            logger.error(f"Failed to get timeline stats: {e}")
            return pd.DataFrame()

    def close(self):
        """Ferme la session HTTP proprement."""
        if hasattr(self, "session"):
            self.session.close()
            logger.info("APIClient session closed")
