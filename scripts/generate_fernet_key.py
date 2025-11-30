"""
Script pour générer une clé Fernet pour Airflow.
"""
from cryptography.fernet import Fernet
import secrets

def generate_fernet_key():
    """Génère une clé Fernet pour Airflow."""
    key = Fernet.generate_key()
    return key.decode()

def generate_secret_key():
    """Génère une clé secrète aléatoire pour le webserver."""
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    print("=" * 80)
    print("Clés pour Airflow")
    print("=" * 80)
    print("\n📝 Ajoutez ces lignes dans votre fichier .env:\n")
    print(f"AIRFLOW__CORE__FERNET_KEY={generate_fernet_key()}")
    print(f"AIRFLOW__WEBSERVER__SECRET_KEY={generate_secret_key()}")
    print("\n" + "=" * 80)