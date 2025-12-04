import logging
import re
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.api_client import APIClient

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="France Travail – Explorateur d'offres",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================


def simple_markdown_format(text: str) -> str:
    """
    Conversion minimaliste en markdown.

    Amélioration : Regex plus robuste et gestion des cas limites.
    """
    if not text:
        return ""

    # Remplacer les * en début de ligne par des •
    text = re.sub(r"^\*\s+", "• ", text, flags=re.MULTILINE)

    # Ajouter des sauts de ligne après les points finaux suivis de majuscule
    text = re.sub(r"\.\s+(?=[A-Z])", ".\n\n", text)

    # Mettre en gras les titres de sections courants
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


def create_department_map(df_offers: pd.DataFrame) -> go.Figure | None:
    """
    Crée une carte des départements français.

    Amélioration : Meilleure gestion des erreurs et fallback.
    """
    if df_offers.empty or "departement" not in df_offers.columns:
        return None

    try:
        # Compter les offres par département
        dept_counts = (
            df_offers.dropna(subset=["departement"])
            .groupby("departement")
            .size()
            .reset_index(name="nb_offres")
        )

        if dept_counts.empty:
            return None

        # Coordonnées approximatives des départements principaux
        department_coords = {
            "75": [48.8566, 2.3522, "Paris"],
            "13": [43.2965, 5.3698, "Bouches-du-Rhône"],
            "69": [45.7640, 4.8357, "Rhône"],
            "59": [50.6292, 3.0573, "Nord"],
            "33": [44.8378, -0.5792, "Gironde"],
            "31": [43.6047, 1.4442, "Haute-Garonne"],
            "67": [48.5734, 7.7521, "Bas-Rhin"],
            "92": [48.8637, 2.3615, "Hauts-de-Seine"],
            "93": [48.9062, 2.4848, "Seine-Saint-Denis"],
            "94": [48.7904, 2.4556, "Val-de-Marne"],
            "78": [48.8120, 2.1225, "Yvelines"],
            "91": [48.6322, 2.2417, "Essonne"],
            "95": [49.0333, 2.0833, "Val-d'Oise"],
            "44": [47.2184, -1.5536, "Loire-Atlantique"],
            "35": [48.1173, -1.6778, "Ille-et-Vilaine"],
            "57": [49.1193, 6.1757, "Moselle"],
            "06": [43.7044, 7.2619, "Alpes-Maritimes"],
        }

        # Préparer les données
        map_data = []
        for _, row in dept_counts.iterrows():
            dept = str(row["departement"])
            if dept in department_coords:
                lat, lon, name = department_coords[dept]
                map_data.append(
                    {
                        "departement": dept,
                        "nom": name,
                        "nb_offres": row["nb_offres"],
                        "lat": lat,
                        "lon": lon,
                    }
                )

        if not map_data:
            return None

        df_map = pd.DataFrame(map_data)

        # Créer la carte
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


def create_contract_pie_chart(df_offers: pd.DataFrame) -> go.Figure | None:
    """
    Crée un graphique en camembert des types de contrat.

    Amélioration : Gestion des libellés manquants.
    """
    if df_offers.empty or "type_contrat_libelle" not in df_offers.columns:
        return None

    try:
        by_contrat = (
            df_offers.dropna(subset=["type_contrat_libelle"])
            .groupby("type_contrat_libelle")
            .size()
            .reset_index(name="nb_offres")
        )

        if by_contrat.empty:
            return None

        fig = px.pie(
            by_contrat,
            values="nb_offres",
            names="type_contrat_libelle",
            title="Répartition par type de contrat",
            hole=0.4,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        return fig

    except Exception as e:
        logger.error(f"Error creating contract chart: {e}")
        return None


def create_timeline_chart(df_offers: pd.DataFrame) -> go.Figure | None:
    """
    Crée un graphique d'évolution temporelle.

    Amélioration : Meilleure gestion des dates.
    """
    if df_offers.empty or "date_creation" not in df_offers.columns:
        return None

    try:
        df_timeline = df_offers.copy()
        df_timeline["date_creation"] = pd.to_datetime(df_timeline["date_creation"], errors="coerce")

        timeline = df_timeline.dropna(subset=["date_creation"]).copy()
        timeline["date"] = timeline["date_creation"].dt.date

        if timeline.empty:
            return None

        timeline_counts = timeline.groupby("date").size().reset_index(name="nb_offres")

        fig = px.line(
            timeline_counts,
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
    """
    Affiche une carte de statistique stylée.

    Nouvelle fonction pour réutilisabilité.
    """
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
    """
    Affiche une carte d'offre.

    Amélioration : Code plus modulaire et réutilisable.
    """
    col_left, col_right = st.columns([3, 1])

    with col_left:
        # Titre
        st.markdown(f"### {offre.get('intitule', 'Titre non disponible')}")

        # Entreprise
        if offre.get("entreprise_nom"):
            st.markdown(f"**🏢 {offre['entreprise_nom']}**")

        # Localisation
        if offre.get("lieu_travail"):
            st.markdown(f"📍 **Lieu :** {offre['lieu_travail']}")

        # Description avec preview
        if offre.get("description"):
            desc = simple_markdown_format(str(offre["description"]))
            preview = desc[:300] + "..." if len(desc) > 300 else desc

            with st.expander(f"📖 **Description :** {preview}"):
                st.markdown(desc)

    with col_right:
        # Badges
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

        # Informations supplémentaires
        if offre.get("salaire_libelle"):
            st.info(f"💰 {offre['salaire_libelle']}")

        if offre.get("date_creation"):
            try:
                date_str = pd.to_datetime(offre["date_creation"]).strftime("%d/%m/%Y")
                st.caption(f"🔄 {date_str}")
            except:
                pass


# ============================================================================
# INITIALISATION
# ============================================================================


# Client API avec cache
@st.cache_resource
def get_api_client() -> APIClient:
    """Initialise le client API (mis en cache)."""
    return APIClient()


api = get_api_client()

# CSS personnalisé (inchangé mais amélioré)
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

    # Mots-clés
    keyword = st.text_input(
        "**Mots-clés**",
        placeholder="Ex: développeur python, data engineer...",
        help="Recherche dans le titre et la description",
    )

    # Filtres avancés
    with st.expander("**⚙️ Filtres avancés**", expanded=False):
        try:
            deps, contrats = api.load_filters_values()

            departement = st.selectbox(
                "**Département**",
                options=["(Tous)"] + deps,
                index=0,
            )

            type_contrat = st.selectbox(
                "**Type de contrat**",
                options=["(Tous)"] + contrats,
                index=0,
            )

        except Exception as e:
            st.error(f"❌ Erreur de chargement des filtres : {e}")
            departement = "(Tous)"
            type_contrat = "(Tous)"

    # Autres filtres
    st.markdown("---")

    limit = st.slider(
        "**📊 Nombre d'offres**",
        min_value=10,
        max_value=1000,
        value=500,
        step=10,
    )

    publiee_depuis = st.selectbox(
        "**📅 Publiées depuis**",
        options=[1, 3, 7, 15, 30],
        index=0,  # 1 jours par défaut
        format_func=lambda x: f"{x} jour" if x == 1 else f"{x} jours",
    )

    # Boutons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_btn = st.button("🔎 Rechercher", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

# Conversion des filtres
departement_filter = None if departement == "(Tous)" else departement
type_contrat_filter = None if type_contrat == "(Tous)" else type_contrat

# ============================================================================
# RECHERCHE DES OFFRES
# ============================================================================

try:
    # Déclencher une nouvelle recherche si bouton cliqué ou première visite
    if "df_offers" not in st.session_state or recherche_btn or reset_btn:
        with st.spinner("🔍 Recherche en cours..."):
            date_from = (datetime.now() - timedelta(days=publiee_depuis)).date().isoformat()

            df_offers = api.fetch_offers(
                keyword=keyword or None,
                departement=departement_filter,
                type_contrat=type_contrat_filter,
                limit=limit,
                date_from=date_from,
            )

            st.session_state.df_offers = df_offers
            logger.info(f"Fetched {len(df_offers)} offers")
    else:
        df_offers = st.session_state.df_offers

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
    if df_offers.empty:
        st.info("ℹ️ Aucune offre trouvée. Essayez d'élargir vos critères.")
    else:
        # Cartes de statistiques
        st.subheader("📈 Vue d'ensemble")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            display_stat_card("Total d'offres", len(df_offers), "résultats")

        with col2:
            if "departement" in df_offers.columns:
                deps_count = df_offers["departement"].nunique()
                display_stat_card("Départements", deps_count, "couverts")

        with col3:
            if "entreprise_nom" in df_offers.columns:
                entreprises = df_offers["entreprise_nom"].nunique()
                display_stat_card("Entreprises", entreprises, "recruteurs")

        with col4:
            if "date_actualisation" in df_offers.columns:
                latest = pd.to_datetime(df_offers["date_actualisation"], errors="coerce").max()
                if pd.notna(latest):
                    display_stat_card(
                        "Dernière MAJ", latest.strftime("%d/%m"), latest.strftime("%Y")
                    )

        st.markdown("---")

        # Liste des offres
        st.subheader(f"📋 {len(df_offers)} offres trouvées")

        for offre in df_offers.iterrows():
            display_offer_card(offre)
            st.markdown("---")

# ============================================================================
# TAB 2: STATISTIQUES
# ============================================================================

with tab2:
    if not df_offers.empty:
        st.subheader("📊 Analyse statistique")

        col1, col2 = st.columns(2)

        with col1:
            fig_map = create_department_map(df_offers)
            if fig_map:
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Pas assez de données pour la carte")

        with col2:
            fig_contrat = create_contract_pie_chart(df_offers)
            if fig_contrat:
                st.plotly_chart(fig_contrat, use_container_width=True)

        # Timeline
        fig_timeline = create_timeline_chart(df_offers)
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
                "date_creation",
            ]
            # Ne garder que les colonnes qui existent
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
