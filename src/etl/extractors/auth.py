# src/etl/extractors/auth.py
from __future__ import annotations

import time
from typing import Optional

import requests

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class FranceTravailAuthError(Exception):
    """Erreur d'authentification France Travail."""


class FranceTravailAuth:
    """Gestion du token OAuth2 client_credentials pour France Travail."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        scope: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.client_id = client_id or settings.france_travail_client_id
        self.client_secret = client_secret or settings.france_travail_client_secret
        self.token_url = token_url or settings.france_travail_token_url
        self.scope = scope or settings.france_travail_scope
        self.timeout = timeout

        self._access_token: Optional[str] = None
        self._expires_at: Optional[float] = None  # timestamp en secondes

    def get_access_token(self) -> str:
        """Retourne un token valide, rafraîchit si nécessaire."""
        if self._access_token and self._expires_at:
            # marge de 60s avant expiration
            if time.time() < self._expires_at - 60:
                return self._access_token

        self._request_new_token()
        if not self._access_token:
            raise FranceTravailAuthError("Impossible d'obtenir un access token")
        return self._access_token

    def _request_new_token(self) -> None:
        """Appelle l'endpoint OAuth2 de France Travail."""
        logger.info("Requesting new France Travail access token")
        data = {
            "grant_type": "client_credentials",
            "scope": self.scope,
        }

        try:
            resp = requests.post(
                self.token_url,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.error("Error while requesting access token: %s", exc, exc_info=True)
            raise FranceTravailAuthError("Erreur lors de l'appel token OAuth2") from exc

        token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)

        if not token:
            logger.error("No access_token in OAuth2 response: %s", payload)
            raise FranceTravailAuthError("Réponse OAuth2 invalide (pas d'access_token)")

        self._access_token = token
        self._expires_at = time.time() + int(expires_in)
        logger.info("France Travail access token obtained (expires_in=%s)", expires_in)
