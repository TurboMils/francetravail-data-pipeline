# src/etl/extractors/france_travail_api.py
from __future__ import annotations

from typing import Any

import requests
from requests import HTTPError

from config.logging_config import get_logger
from config.settings import settings
from etl.extractors.auth import FranceTravailAuth, FranceTravailAuthError

logger = get_logger(__name__)


class FranceTravailApiError(Exception):
    """Erreur lors d'un appel à l'API France Travail."""


class FranceTravailClient:
    """Client HTTP : recherche simple par département."""

    def __init__(
        self,
        auth: FranceTravailAuth | None = None,
        timeout: int = 30,
    ) -> None:
        self.auth = auth or FranceTravailAuth()
        self.base_url = f"{settings.france_travail_api_url}/offresdemploi/v2/offres/search"
        self.timeout = timeout

    def search_offers(
        self,
        keyword: str | None = None,
        departement: str | None = None,
        limit: int = 150,
        publiee_depuis: int | None = 7,
        sort: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Recherche simple par mots-clés + département.
        """
        try:
            token = self.auth.get_access_token()
        except FranceTravailAuthError as exc:
            raise FranceTravailApiError("Impossible d'obtenir un token") from exc

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        max_per_page = min(limit, settings.france_travail_max_results_per_page)
        range_param = f"0-{max_per_page - 1}"

        params: dict[str, Any] = {
            "range": range_param,
            "sort": sort,
        }
        if keyword:
            params["motsCles"] = keyword
        if departement:
            params["departement"] = departement
        if publiee_depuis is not None:
            params["publieeDepuis"] = publiee_depuis

        logger.info(
            "Calling France Travail search_offers (keyword=%s, departement=%s, range=%s, publieeDepuis=%s, sort=%s)",
            keyword,
            departement,
            range_param,
            publiee_depuis,
            sort,
        )

        try:
            resp = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            try:
                resp.raise_for_status()
            except HTTPError:
                logger.error(
                    "France Travail API error HTTP %s, body=%s",
                    resp.status_code,
                    resp.text,
                )
                raise
            data = resp.json()
        except Exception as exc:
            logger.error("Error calling France Travail API: %s", exc, exc_info=True)
            raise FranceTravailApiError("Erreur HTTP vers France Travail") from exc

        offres = data.get("resultats", [])
        if not isinstance(offres, list):
            logger.error("Unexpected 'resultats' format: %s", type(offres))
            raise FranceTravailApiError("Format de réponse inattendu")

        return offres[:limit]
