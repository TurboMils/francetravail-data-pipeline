import re
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.logging_config import get_logger
from domain.departments import DEPARTMENT_COORDS
from streamlit_app.api_client import APIClient

EXPERIENCE_LABELS: dict[str, str] = {
    "D": "Débutant",
    "E": "Expérimenté",
    "S": "Confirmé",
}

# Configuration du logging
logger = get_logger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="France Travail – Explorateur d'offres",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

if st.session_state.get("scroll_top"):
    st.markdown(
        """
        <script>
        window.scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["scroll_top"] = False


# Pagination
DEFAULT_PAGE_SIZE = 50

if "offers_page" not in st.session_state:
    st.session_state["offers_page"] = 1

if "filters" not in st.session_state:
    st.session_state["filters"] = {
        "keyword": None,  # list[str] | None
        "departement": None,  # list[str] | None
        "type_contrat": None,  # list[str] | None
        "experience": None,  # list[str] | None
        "date_from": None,  # str | None (YYYY-MM-DD)
    }

if "scroll_top" not in st.session_state:
    st.session_state["scroll_top"] = False


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================


def remove_tous_from_filter(items: list[str] | None) -> list[str] | None:
    if not items:
        return None
    if items == ["(Tous)"]:
        return None
    if "(Tous)" not in items:
        return items
    cleaned = [item for item in items if item != "(Tous)"]
    return cleaned if cleaned else None


def simple_markdown_format(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"^\*\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"\.\s+(?=[A-Z])", ".\n\n", text)

    sections = [
        "Missions principales",
        "De formation technique",
        "Les avantages",
        "Vous maîtrisez",
        "Rigoureux",
        "Profil recherché",
        "Vos missions",
        "Compétences requises",
    ]
    for section in sections:
        text = text.replace(section, f"**{section}**")

    return text


def create_department_map(df_deps: pd.DataFrame) -> go.Figure | None:

    if df_deps.empty or "departement" not in df_deps.columns or "nb_offres" not in df_deps.columns:
        return None

    try:
        map_data: list[dict[str, Any]] = []

        for _, row in df_deps.iterrows():
            dept = str(row["departement"])
            coord = DEPARTMENT_COORDS.get(dept)
            if not coord:
                continue

            map_data.append(
                {
                    "departement": dept,
                    "nom": coord["name"],
                    "nb_offres": int(row["nb_offres"]),
                    "lat": coord["lat"],
                    "lon": coord["lon"],
                }
            )

        if not map_data:
            return None

        df_map = pd.DataFrame(map_data)

        fig = px.scatter_mapbox(
            df_map,
            lat="lat",
            lon="lon",
            size="nb_offres",
            color="nb_offres",
            hover_name="nom",
            hover_data={"nb_offres": True, "departement": True, "lat": False, "lon": False},
            color_continuous_scale="Viridis",
            size_max=30,
            zoom=4.5,
            center={"lat": 46.5, "lon": 2},
            title="Offres par département",
            mapbox_style="carto-positron",
        )

        fig.update_layout(height=500, margin={"r": 0, "t": 40, "l": 0, "b": 0})
        return fig

    except Exception as e:
        logger.error(f"Error creating map: {e}")
        return None


def create_contract_pie_chart(df_contrats: pd.DataFrame) -> go.Figure | None:
    if (
        df_contrats.empty
        or "type_contrat" not in df_contrats.columns
        or "nb_offres" not in df_contrats.columns
    ):
        return None

    try:
        df = df_contrats.copy()

        fig = px.pie(
            df,
            values="nb_offres",
            names="type_contrat",
            title="Répartition par type de contrat",
            hole=0.4,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    except Exception as e:
        logger.error(f"Error creating contract chart: {e}")
        return None


def create_timeline_chart(df_timeline: pd.DataFrame) -> go.Figure | None:
    """
    df_timeline doit contenir:
      - 'date' (str ou date)
      - 'nb_offres' (int)
    """
    if (
        df_timeline.empty
        or "date" not in df_timeline.columns
        or "nb_offres" not in df_timeline.columns
    ):
        return None

    try:
        df = df_timeline.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        df = df.dropna(subset=["date"])
        if df.empty:
            return None

        fig = px.line(
            df,
            x="date",
            y="nb_offres",
            title="Évolution des publications",
            markers=True,
        )

        fig.update_layout(height=400, xaxis_title="Date", yaxis_title="Nombre d'offres")
        return fig

    except Exception as e:
        logger.error(f"Error creating timeline: {e}")
        return None


def display_stat_card(title: str, value: str | int, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <h3>{title}</h3>
            <div class="value">{value}</div>
            <div class="subtext">{subtitle}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def display_offer_card(offre: pd.Series) -> None:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown(f"### {offre.get('intitule', 'Titre non disponible')}")

        if offre.get("entreprise_nom"):
            st.markdown(f"**🏢 {offre['entreprise_nom']}**")

        if offre.get("lieu_travail"):
            st.markdown(f"📍 **Lieu :** {offre['lieu_travail']}")

        if offre.get("description"):
            desc = simple_markdown_format(str(offre["description"]))
            preview = desc[:300] + "..." if len(desc) > 300 else desc

            with st.expander(f"📖 **Description :** {preview}"):
                st.markdown(desc)

    with col_right:
        if offre.get("type_contrat_libelle"):
            st.markdown(
                f'<span class="badge badge-contract">{offre["type_contrat_libelle"]}</span>',
                unsafe_allow_html=True,
            )

        if offre.get("departement"):
            st.markdown(
                f'<span class="badge badge-department">Dépt. {offre["departement"]}</span>',
                unsafe_allow_html=True,
            )

        if offre.get("experience_libelle"):
            st.markdown(
                f'<span class="badge badge-experience">{offre["experience_libelle"]}</span>',
                unsafe_allow_html=True,
            )

        if offre.get("salaire_libelle"):
            st.info(f"💰 {offre['salaire_libelle']}")

        if offre.get("date_creation"):
            try:
                date_str = pd.to_datetime(offre["date_creation"]).strftime("%d/%m/%Y")
                st.caption(f"🔄 {date_str}")
            except (TypeError, ValueError) as e:
                logger.debug(f"Date parsing date_creation={offre.get('date_creation')!r}: {e}")


# ============================================================================
# INITIALISATION
# ============================================================================


@st.cache_resource
def get_api_client() -> APIClient:
    return APIClient()


api = get_api_client()

# CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stat-card h3 {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
        opacity: 0.9;
    }
    .stat-card .value {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .stat-card .subtext {
        font-size: 12px;
        opacity: 0.8;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 5px;
    }
    .badge-contract {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .badge-department {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .badge-experience {
        background-color: #e8f5e9;
        color: #388e3c;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# EN-TÊTE
# ============================================================================

col_title1, col_title2, col_title3 = st.columns([1, 2, 1])
with col_title2:
    st.markdown(
        """
        <h1 style="text-align: center; color: #2c3e50; margin-bottom: 10px;">
            💼 France Travail – Explorateur d'offres
        </h1>
        <p style="text-align: center; color: #7f8c8d; font-size: 16px;">
            Recherchez et analysez les offres d'emploi en temps réel
        </p>
    """,
        unsafe_allow_html=True,
    )

# ============================================================================
# SIDEBAR - FILTRES
# ============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <h3 style="color: white; margin: 0;">🔍 Recherche avancée</h3>
            <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 5px;">
                Filtrez les offres selon vos critères
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    keyword_str = st.text_input(
        "**Mots-clés**",
        placeholder="Ex: développeur python, data engineer...",
        help="Recherche dans le titre et la description",
    )

    with st.expander("**⚙️ Filtres avancés**", expanded=False):
        try:
            deps, contrats, experience = api.load_filters_values()

            departement = st.multiselect(
                "**Département**",
                options=["(Tous)"] + deps,
                default=["(Tous)"],
            )

            type_contrat = st.multiselect(
                "**Type de contrat**",
                options=["(Tous)"] + contrats,
                default=["(Tous)"],
            )

            experience_level = st.multiselect(
                "Expérience",
                options=["(Tous)"] + experience,
                default=["(Tous)"],
                format_func=lambda code: EXPERIENCE_LABELS.get(code, code),
            )

        except Exception as e:
            st.error(f"❌ Erreur de chargement des filtres : {e}")
            departement = ["(Tous)"]
            type_contrat = ["(Tous)"]
            experience_level = ["(Tous)"]

    st.markdown("---")

    page_size = st.slider(
        "**📊 Résultats par page**",
        min_value=10,
        max_value=50,
        value=DEFAULT_PAGE_SIZE,
        step=10,
    )

    publiee_depuis = st.selectbox(
        "**📅 Publiées depuis**",
        options=[1, 3, 7, 15, 30],
        index=0,
        format_func=lambda x: f"{x} jour" if x == 1 else f"{x} jours",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_btn = st.button("🔎 Rechercher", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🔄 Reset", width="content", use_container_width=True)

# Conversion des filtres pour sauvegarde

# keyword -> list[str]
keyword_list: list[str] | None = None
if keyword_str:
    tokens = re.split(r"[;,]\s*|\s+", keyword_str)
    keyword_list = [t for t in tokens if t]

departement_filter = remove_tous_from_filter(departement)
type_contrat_filter = remove_tous_from_filter(type_contrat)
experience_level_filter = remove_tous_from_filter(experience_level)
date_from_value = (datetime.now() - timedelta(days=publiee_depuis)).date().isoformat()

# Gestion des boutons : on stocke les filtres et on reset la page, puis on rerun
if reset_btn:
    st.session_state["filters"] = {
        "keyword": None,
        "departement": None,
        "type_contrat": None,
        "experience": None,
        "date_from": None,
    }
    st.session_state["offers_page"] = 1
    st.rerun()

if recherche_btn:
    st.session_state["filters"] = {
        "keyword": keyword_list,
        "departement": departement_filter,
        "type_contrat": type_contrat_filter,
        "experience": experience_level_filter,
        "date_from": date_from_value,
    }
    st.session_state["offers_page"] = 1
    st.rerun()

# ============================================================================
# RECHERCHE DES OFFRES (toujours à partir de l'état)
# ============================================================================

page = st.session_state["offers_page"]
filters = st.session_state["filters"]

try:
    with st.spinner("🔍 Recherche en cours..."):
        df_offers, total = api.fetch_offers(
            keyword=filters["keyword"],
            departement=filters["departement"],
            type_contrat=filters["type_contrat"],
            experience=filters["experience"],
            page=page,
            limit=page_size,
            date_from=filters["date_from"],
        )
        logger.info(
            f"Fetched {len(df_offers)} offers (page={page}, size={page_size}, total={total})"
        )
except Exception as e:
    st.error(f"❌ {str(e)}")
    st.stop()

# ============================================================================
# ONGLETS PRINCIPAUX
# ============================================================================

tab1, tab2, tab3 = st.tabs(["📋 Résultats", "📊 Statistiques", "🔍 Export"])

# ============================================================================
# TAB 1: RÉSULTATS
# ============================================================================

with tab1:
    total_offers, total_departments, total_companies, last_date = api.get_statistics(
        keyword=filters["keyword"],
        departement=filters["departement"],
        type_contrat=filters["type_contrat"],
        experience=filters["experience"],
        date_from=filters["date_from"],
    )

    if total_offers == 0:
        st.info("ℹ️ Aucune offre trouvée. Essayez d'élargir vos critères.")
    else:
        total_pages = max((total + page_size - 1) // page_size, 1)
        page = st.session_state["offers_page"]

        st.subheader("📈 Vue d'ensemble")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            display_stat_card("Total d'offres", total_offers, "résultats")

        with col2:
            display_stat_card("Départements", total_departments, "couverts")

        with col3:
            display_stat_card("Entreprises", total_companies, "recruteurs")

        with col4:
            if last_date:
                latest = pd.to_datetime(last_date, errors="coerce")
                if pd.notna(latest):
                    display_stat_card(
                        "Dernière MAJ",
                        latest.strftime("%d/%m"),
                        latest.strftime("%Y"),
                    )

        st.markdown("---")

        for _, offre in df_offers.iterrows():
            display_offer_card(offre)
            st.markdown("---")

        col_prev, col_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if page > 1:
                if st.button("⬅️ Page précédente"):
                    st.session_state["offers_page"] = page - 1
                    st.session_state["scroll_top"] = True
                    st.rerun()

        with col_info:
            st.markdown(
                f"<p style='text-align:center;'>Page {page} / {total_pages}</p>",
                unsafe_allow_html=True,
            )

        with col_next:
            if page < total_pages:
                if st.button("Page suivante ➡️"):
                    st.session_state["offers_page"] = page + 1
                    st.session_state["scroll_top"] = True
                    st.rerun()

# ============================================================================
# TAB 2: STATISTIQUES
# ============================================================================

with tab2:
    filters = st.session_state["filters"]
    df_deps = api.get_department_stats(**filters)
    logger.info(f"Department stats dataframe : {df_deps}")
    df_timeline = api.get_timeline_data(**filters)
    df_contrats = api.get_contrat_stats(**filters)

    logger.info(f"df_contrats stats dataframe shape: {df_contrats}")

    if not df_deps.empty and not df_offers.empty:
        st.subheader("📊 Analyse statistique")

        col1, col2 = st.columns(2)

        with col1:
            fig_map = create_department_map(df_deps)
            if fig_map:
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Pas assez de données pour la carte")

        with col2:
            fig_contrat = create_contract_pie_chart(df_contrats)
            if fig_contrat:
                st.plotly_chart(fig_contrat, use_container_width=True)

        if not df_timeline.empty:
            st.markdown("---")
            st.subheader("📅 Évolution des publications dans le temps")
            fig_timeline = create_timeline_chart(df_timeline)
            if fig_timeline:
                st.plotly_chart(fig_timeline, use_container_width=True)

# ============================================================================
# TAB 3: EXPORT
# ============================================================================

with tab3:
    if not df_offers.empty:
        st.subheader("💾 Export des données")

        col1, col2 = st.columns(2)

        with col1:
            export_format = st.selectbox("Format", ["CSV", "Excel", "JSON"])

            available_cols = df_offers.columns.tolist()
            default_cols = [
                "intitule",
                "entreprise_nom",
                "lieu_travail",
                "type_contrat_libelle",
                "experience_libelle",
                "date_creation",
            ]
            default_cols = [c for c in default_cols if c in available_cols]

            selected_cols = st.multiselect(
                "Colonnes à exporter", available_cols, default=default_cols
            )

        with col2:
            if st.button("📥 Générer l'export", type="primary"):
                export_df = df_offers[selected_cols] if selected_cols else df_offers

                if export_format == "CSV":
                    csv = export_df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        "⬇️ Télécharger CSV",
                        data=csv,
                        file_name="offres_france_travail.csv",
                        mime="text/csv",
                    )

                elif export_format == "JSON":
                    json_str = export_df.to_json(orient="records", force_ascii=False, indent=2)
                    st.download_button(
                        "⬇️ Télécharger JSON",
                        data=json_str,
                        file_name="offres_france_travail.json",
                        mime="application/json",
                    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #7f8c8d; padding: 20px;">
        <p><strong>France Travail – Explorateur d'offres</strong></p>
        <p style="font-size: 12px;">
            Données de l'API France Travail
        </p>
    </div>
""",
    unsafe_allow_html=True,
)
