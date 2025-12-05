
import streamlit as st

from config.logging_config import get_logger
from streamlit_app.api_client import APIClient

# Configuration du logging
logger = get_logger(__name__)


# Client API avec cache
@st.cache_resource
def get_api_client() -> APIClient:
    """Initialise le client API (mis en cache)."""
    return APIClient()


api = get_api_client()

deps, contrats, experience = api.load_filters_values()

print(deps, contrats, experience)