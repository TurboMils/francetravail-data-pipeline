
import requests

from src.config.settings import settings


class FranceTravailAuth:
    """Gestionnaire d'authentification OAuth2."""
    
    def __init__(self):
        self.client_id = settings.france_travail_client_id
        self.client_secret = settings.france_travail_client_secret
        self.token_url = settings.france_travail_token_url
    
    def get_access_token(self) -> str:
        """
        Obtient un access token.
        
        Returns:
            Access token valide
            
        Raises:
            requests.RequestException: Si l'authentification échoue
        """
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "api_offresdemploiv2 o2dsoffre",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        return token_data["access_token"]