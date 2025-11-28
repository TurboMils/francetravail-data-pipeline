"""
PHASE 1 : Tests de l'authentification.
"""
import pytest
from unittest.mock import Mock, patch

from src.api_client.auth import FranceTravailAuth


def test_auth_initialization():
    """Test que l'auth se crée correctement."""
    auth = FranceTravailAuth()
    assert auth.client_id is not None
    assert auth.client_secret is not None
    assert auth.token_url is not None


@patch('src.api_client.auth.requests.post')
def test_get_access_token_success(mock_post):
    """Test d'obtention d'un token avec succès."""
    # Mock de la réponse
    mock_response = Mock()
    mock_response.json.return_value = {"access_token": "fake_token_123"}
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    # Test
    auth = FranceTravailAuth()
    token = auth.get_access_token()
    
    assert token == "fake_token_123"
    mock_post.assert_called_once()


@patch('src.api_client.auth.requests.post')
def test_get_access_token_failure(mock_post):
    """Test d'échec d'authentification."""
    # Mock d'une erreur
    mock_post.side_effect = Exception("Auth failed")
    
    # Test
    auth = FranceTravailAuth()
    
    with pytest.raises(Exception):
        auth.get_access_token()


@pytest.mark.integration
def test_real_authentication():
    """Test réel avec l'API France Travail."""
    auth = FranceTravailAuth()
    token = auth.get_access_token()
    
    assert token is not None
    assert len(token) > 0