from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Fetch offers from the API with caching
@st.cache_data(show_spinner=False)
def fetch_offers(
    keyword: Optional[str] = None,
    departement: Optional[str] = None,
    type_contrat: Optional[str] = None,
    limit: int = 200,
) -> pd.DataFrame:
    payload = {
        "keyword": keyword or None,
        "departement": departement or None,
        "rome_code": None,
        "type_contrat": type_contrat or None,
        "page": 1,
        "size": limit,
    }
    resp = requests.post(f"{API_URL}/offers/search", json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        return pd.DataFrame()
    
    df = pd.DataFrame(items)
    return df

# Load filter values for departments and contract types
@st.cache_data(show_spinner=False)
def load_filters_values() -> tuple[list[str], list[str]]:

    df = fetch_offers(limit=500)
    if df.empty:
        return [], []
    
    deps: list[str] = []
    if "departement" in df.columns:
        deps = sorted(
            d 
            for d in df["departement"]
            .dropna()
            .astype(str)
            .unique()
            .tolist() 
            if d.strip()
        )
    contrats: list[str] = []
    if "type_contrat" in df.columns:
        contrats = sorted(
            c
            for c in df["type_contrat"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
            if c.strip()
        )
    return deps, contrats

def main() -> None:
    st.set_page_config(
        page_title="France Travail – Explorateur d'offres",
        layout="wide",
    )
    
    st.title("France Travail – Explorateur d'offres")

    deps, contrats = load_filters_values()

    with st.sidebar:
        st.header("Filtres")

        keyword = st.text_input("Mot-clé", value="")

        departement = (
            st.selectbox(
            "Département",
            options=["(Tous)"] + deps,
            index=0)
            if deps else "(Tous)"
        )

        type_contrat = (
            st.selectbox(
            "Type de contrat",
            options=["(Tous)"] + contrats,
            index=0)
            if contrats else "(Tous)"
        )

        if departement == "(Tous)":
            departement = None
        if type_contrat == "(Tous)":
            type_contrat = None
        
        limit = st.slider(
            "Nombre d'offres à afficher",
            min_value=10,
            max_value=500,
            value=200,
            step=10,
        )

    try:
        df_offers = fetch_offers(
            keyword=keyword or None,
            departement=departement,
            type_contrat=type_contrat,
            limit=limit,
        )
    except requests.RequestException as e:
        st.error(f"Erreur lors de la récupération des offres : {e}")
        return
        
    st.subheader(f"Offres récupérées : {len(df_offers)} offres")

    if df_offers.empty:
        st.info("Aucune offre trouvée avec les critères sélectionnés.")
        return
    
    colonne_affichage = [
        "id",
        "intitule",
        "lieu_travail",
        "departement",
        "type_contrat",
        "salaire_libelle",
        "date_creation",
        "rome_code",
    ]
    cols_existantes = [col for col in colonne_affichage if col in df_offers.columns]
    
    st.dataframe(
        df_offers[cols_existantes].sort_values(by="date_creation", ascending=False),
        width='stretch',
        height=600,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Offres par département")
        if "departement" in df_offers.columns:
            by_dep = (
                df_offers.dropna(subset=["departement"])
                .groupby("departement")
                .size()
                .reset_index(name="nb_offres")
                .sort_values(by="nb_offres", ascending=False)
            )
            if not by_dep.empty:
                fig_dep = px.bar(
                    by_dep,
                    x="departement",
                    y="nb_offres",
                    labels={"departement": "Département", "nb_offres": "Nombre d'offres"},
                    title="Nombre d'offres par département",
                )
                st.plotly_chart(fig_dep, width='stretch')
            else:
                st.write("Pas de données disponibles pour les départements.")
        else:
            st.write("La colonne 'departement' n'est pas exposée par l'API.")

    with col2:
        st.markdown("### Offres par type de contrat")
        if "type_contrat" in df_offers.columns:
            by_contrat = (
                df_offers.dropna(subset=["type_contrat"])
                .groupby("type_contrat")
                .size()
                .reset_index(name="nb_offres")
                .sort_values(by="nb_offres", ascending=False)
            )
            if not by_contrat.empty:
                fig_contrat = px.bar(
                    by_contrat,
                    x="type_contrat",
                    y="nb_offres",
                    labels={"type_contrat": "Type de contrat", "nb_offres": "Nombre d'offres"},
                    title="Nombre d'offres par type de contrat",
                )
                st.plotly_chart(fig_contrat, width='stretch')
            else:
                st.write("Pas de données disponibles pour les types de contrat.")
        else:
            st.write("La colonne 'type_contrat' n'est pas exposée par l'API.")

if __name__ == "__main__":
    main()
