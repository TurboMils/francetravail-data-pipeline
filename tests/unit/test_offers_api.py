from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool  # Pour SQLite in-memory

from api.main import app
from api.dependencies import get_db
from db.models import Base, Offre

engine_test = create_engine("sqlite:///:memory:",
                            connect_args={'check_same_thread': False},
                            future=True,
                            poolclass=StaticPool
                            )

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine_test,
    future=True,
)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module(_module=None):
    """Seed minimal de données pour les tests API."""
    db = TestingSessionLocal()
    try:
        offer = Offre(
            id="OFFRE_TEST_1",
            intitule="Développeur Python",
            description="Poste de dev backend",
            date_creation="2024-01-01T10:00:00",
            date_actualisation="2024-01-02T10:00:00",
            lieu_travail="Paris",
            rome_code="M1805",
            rome_libelle="Études et développement informatique",
            type_contrat="CDI",
            salaire_libelle="Selon profil",
        )
        db.add(offer)
        db.commit()
    finally:
        db.close()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_get_offers_list():
    resp = client.get("/offers?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["total"] >= 1
    assert any(o["id"] == "OFFRE_TEST_1" for o in data["items"])

def test_get_offer_by_id():
    resp = client.get("/offers/OFFRE_TEST_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "OFFRE_TEST_1"
    assert data["intitule"] == "Développeur Python"


def test_search_offers():
    payload = {"keyword": "Python", "page": 1, "size": 10}
    resp = client.post("/offers/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("Python" in (o["intitule"] or "") for o in data["items"])