# tests/unit/test_client.py
from unittest.mock import Mock, patch

import pytest

from etl.extractors.france_travail_api import FranceTravailApiError, FranceTravailClient


@patch("etl.extractors.france_travail_api.FranceTravailAuth")
@patch("etl.extractors.france_travail_api.requests.get")
def test_search_offers_success(mock_get, mock_auth_cls):
    """Recherche simple OK, 10 offres renvoyées."""
    mock_auth = Mock()
    mock_auth.get_access_token.return_value = "token123"
    mock_auth_cls.return_value = mock_auth

    offres = [{"id": str(i), "intitule": f"Offre {i}"} for i in range(15)]
    mock_resp = Mock()
    mock_resp.json.return_value = {"resultats": offres}
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    client = FranceTravailClient()
    result = client.search_offers(keyword="python", departement="75", limit=10)

    assert len(result) == 10
    assert result[0]["id"] == "0"
    mock_get.assert_called_once()
    mock_auth.get_access_token.assert_called_once()


@patch("etl.extractors.france_travail_api.FranceTravailAuth")
@patch("etl.extractors.france_travail_api.requests.get")
def test_search_offers_http_error(mock_get, mock_auth_cls):
    """Erreur HTTP -> FranceTravailApiError."""
    mock_auth = Mock()
    mock_auth.get_access_token.return_value = "token123"
    mock_auth_cls.return_value = mock_auth

    mock_get.side_effect = Exception("HTTP failure")

    client = FranceTravailClient()
    with pytest.raises(FranceTravailApiError):
        client.search_offers(keyword="python", departement="75", limit=10)
