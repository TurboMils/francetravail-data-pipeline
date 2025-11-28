# tests/unit/test_auth.py
from unittest.mock import Mock, patch

import pytest

from etl.extractors.auth import FranceTravailAuth, FranceTravailAuthError


def test_auth_initialization():
    """L'auth doit se construire sans erreur avec les settings."""
    auth = FranceTravailAuth()
    assert auth.client_id
    assert auth.client_secret
    assert auth.token_url
    assert auth.scope


@patch("etl.extractors.auth.requests.post")
def test_get_access_token_success(mock_post):
    """Obtention d'un token avec succès."""
    mock_response = Mock()
    mock_response.json.return_value = {"access_token": "fake_token_123", "expires_in": 3600}
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    auth = FranceTravailAuth()
    token = auth.get_access_token()

    assert token == "fake_token_123"
    mock_post.assert_called_once()


@patch("etl.extractors.auth.requests.post")
def test_get_access_token_failure(mock_post):
    """Échec d'authentification -> exception custom."""
    mock_post.side_effect = Exception("Auth failed")

    auth = FranceTravailAuth()
    with pytest.raises(FranceTravailAuthError):
        auth.get_access_token()
