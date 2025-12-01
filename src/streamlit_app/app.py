from __future__ import annotations

import plotly.express as px
import requests
import streamlit as st

from streamlit_app.api_client import APIClient

st.set_page_config(
    page_title="France Travail – Explorateur d'offres",
    layout="wide",
)

st.title("France Travail – Explorateur d'offres")


@st.cache_resource
def get_api_client() -> APIClient:
    return APIClient()


api = get_api_client()

try:
    deps, contrats = api.load_filters_values()
except requests.RequestException as e:
    st.error(f"Erreur lors de la récupération des valeurs de filtres : {e}")
    st.stop()

with st.sidebar:
    st.header("Filtres")

    keyword = st.text_input(
        "Mots-clés",
        placeholder="Ex: développeur python, data engineer...",
    )

    departement = (
        st.selectbox("Département", options=["(Tous)"] + deps, index=0) if deps else "(Tous)"
    )

    type_contrat = (
        st.selectbox("Type de contrat", options=["(Tous)"] + contrats, index=0)
        if contrats
        else "(Tous)"
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
    df_offers = api.fetch_offers(
        keyword=keyword or None,
        departement=departement,
        type_contrat=type_contrat,
        limit=limit,
    )
except requests.RequestException as e:
    st.error(f"Erreur lors de la récupération des offres : {e}")
    st.stop()


st.subheader(f"Offres récupérées : {len(df_offers)} offres")

if df_offers.empty:
    st.info("Aucune offre trouvée avec les critères sélectionnés.")
    st.stop()

colonne_affichage = [
    "id",
    "intitule",
    "description",
    "lieu_travail",
    "departement",
    "type_contrat",
    "type_contrat_libelle",
    "entreprise_nom",
    "experience_libelle",
    "experience_commentaire",
    "salaire_libelle",
    "date_actualisation",
    "rome_code",
    
    
]
cols_existantes = [col for col in colonne_affichage if col in df_offers.columns]

st.dataframe(
    df_offers[cols_existantes].sort_values(by="date_actualisation", ascending=False),
    width="stretch",
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
            st.plotly_chart(fig_dep, width="stretch")
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
            st.plotly_chart(fig_contrat, width="stretch")
        else:
            st.write("Pas de données disponibles pour les types de contrat.")
    else:
        st.write("La colonne 'type_contrat' n'est pas exposée par l'API.")
