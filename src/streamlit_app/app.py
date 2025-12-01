from __future__ import annotations

import plotly.express as px
import pandas as pd
import requests
import streamlit as st
from datetime import datetime
from streamlit_app.api_client import APIClient

# Configuration de la page
st.set_page_config(
    page_title="France Travail – Explorateur d'offres",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personnalisé
st.markdown("""
    <style>
    /* Style global */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Cartes de statistiques */
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
    
    /* En-tête d'offre */
    .offer-header {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    
    .offer-header:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Badges */
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
    
    /* Filtres */
    .stSelectbox, .stTextInput, .stSlider {
        margin-bottom: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal avec style
col_title1, col_title2, col_title3 = st.columns([1, 2, 1])
with col_title2:
    st.markdown("""
        <h1 style="text-align: center; color: #2c3e50; margin-bottom: 10px;">
            France Travail – Explorateur d'offres
        </h1>
        <p style="text-align: center; color: #7f8c8d; font-size: 16px;">
            Recherchez et analysez les offres d'emploi en temps réel
        </p>
    """, unsafe_allow_html=True)

# Initialiser le client API
@st.cache_resource
def get_api_client() -> APIClient:
    return APIClient()

api = get_api_client()

# Sidebar améliorée
with st.sidebar:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <h3 style="color: white; margin: 0;">🔍 Recherche avancée</h3>
            <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 5px;">
                Filtrez les offres selon vos critères
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Mots-clés avec placeholder et aide
    keyword = st.text_input(
        "**Mots-clés**",
        placeholder="Ex: développeur python, data engineer, analyst...",
        help="Séparez les mots-clés par des virgules pour une recherche multiple",
    )
    
    # Filtres avancés dans un expander
    with st.expander("**⚙️ Filtres avancés**", expanded=False):
        try:
            deps, contrats = api.load_filters_values()
            
            departement = st.selectbox(
                "**Département**",
                options=["(Tous)"] + deps if deps else ["(Tous)"],
                index=0,
                help="Filtrer par département"
            )
            
            type_contrat = st.selectbox(
                "**Type de contrat**",
                options=["(Tous)"] + contrats if contrats else ["(Tous)"],
                index=0,
                help="Filtrer par type de contrat"
            )
            
            # Niveau d'expérience
            experience_levels = ["(Tous)", "Débutant", "Expérimenté", "Sénior", "Non spécifié"]
            experience = st.selectbox("**Niveau d'expérience**", options=experience_levels, index=0)
            
        except requests.RequestException as e:
            st.error(f"Erreur de chargement des filtres : {e}")
            departement = None
            type_contrat = None
    
    # Nombre d'offres avec style
    st.markdown("---")
    limit = st.slider(
        "**📊 Nombre d'offres à afficher**",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Limite le nombre d'offres affichées"
    )
    
    # Date de publication
    publiee_depuis = st.selectbox(
        "**📅 Offres publiées depuis**",
        options=[1, 3, 7, 15, 30],
        index=2,
        format_func=lambda x: f"{x} jour(s)" if x == 1 else f"{x} jours",
        help="Filtrer par ancienneté des offres"
    )
    
    # Boutons d'action
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_btn = st.button("🔎 Rechercher", use_container_width=True, type="primary")
    with col_btn2:
        reset_btn = st.button("🔄 Réinitialiser", use_container_width=True)

# Convertir les filtres
if departement == "(Tous)":
    departement = None
if type_contrat == "(Tous)":
    type_contrat = None
if experience == "(Tous)":
    experience = None

# Recherche des offres
try:
    if 'df_offers' not in st.session_state or recherche_btn or reset_btn:
        with st.spinner("🔍 Recherche d'offres en cours..."):
            df_offers = api.fetch_offers(
                keyword=keyword or None,
                departement=departement,
                type_contrat=type_contrat,
                limit=limit,
            )
            st.session_state.df_offers = df_offers
    else:
        df_offers = st.session_state.df_offers
        
except requests.RequestException as e:
    st.error(f"Erreur lors de la récupération des offres : {e}")
    st.stop()

# Section principale avec onglets
tab1, tab2, tab3 = st.tabs(["📋 Résultats", "📊 Statistiques", "🔍 Analyse détaillée"])

# TAB 1: Résultats
with tab1:
    if df_offers.empty:
        st.info("ℹ️ Aucune offre trouvée avec les critères sélectionnés.")
        st.markdown("""
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #7f8c8d;">🔍 Aucun résultat trouvé</h3>
                <p>Essayez d'élargir vos critères de recherche :</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Utilisez moins de mots-clés</li>
                    <li>Élargissez la zone géographique</li>
                    <li>Modifiez le type de contrat</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Cartes de statistiques
        st.subheader("📈 Vue d'ensemble")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="stat-card">
                    <h3>Total d'offres</h3>
                    <div class="value">{len(df_offers)}</div>
                    <div class="subtext">résultats trouvés</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if 'departement' in df_offers.columns and not df_offers['departement'].isna().all():
                deps_count = df_offers['departement'].nunique()
                st.markdown(f"""
                    <div class="stat-card">
                        <h3>Départements</h3>
                        <div class="value">{deps_count}</div>
                        <div class="subtext">départements couverts</div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if 'entreprise_nom' in df_offers.columns:
                entreprises_count = df_offers['entreprise_nom'].nunique()
                st.markdown(f"""
                    <div class="stat-card">
                        <h3>Entreprises</h3>
                        <div class="value">{entreprises_count}</div>
                        <div class="subtext">recruteurs différents</div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if 'date_actualisation' in df_offers.columns:
                latest_date = pd.to_datetime(df_offers['date_actualisation'], format='ISO8601', errors='coerce').max()
                st.markdown(f"""
                    <div class="stat-card">
                        <h3>Dernière mise à jour</h3>
                        <div class="value">{latest_date.strftime('%d/%m')}</div>
                        <div class="subtext">dernière offre</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Liste des offres avec vue améliorée
        st.subheader(f"📋 Offres ({len(df_offers)} résultats)")
        
        for idx, offre in df_offers.iterrows():
            with st.container():
                col_left, col_right = st.columns([3, 1])
                
                with col_left:
                    # Titre et entreprise
                    st.markdown(f"### {offre.get('intitule', 'Titre non disponible')}")
                    
                    if offre.get('entreprise_nom'):
                        st.markdown(f"**🏢 {offre['entreprise_nom']}**")
                    
                    # Localisation
                    if offre.get('lieu_travail'):
                        st.markdown(f"📍 **Lieu :** {offre['lieu_travail']}")
                    
                    # Description abrégée
                    if offre.get('description'):
                        desc = offre['description']
                        if len(desc) > 300:
                            desc = desc[:300] + "..."
                        with st.expander("📝 Voir la description"):
                            st.write(desc)
                
                with col_right:
                    # Badges d'informations
                    if offre.get('type_contrat_libelle'):
                        st.markdown(f'<span class="badge badge-contract">{offre["type_contrat_libelle"]}</span>', 
                                  unsafe_allow_html=True)
                    
                    if offre.get('departement'):
                        st.markdown(f'<span class="badge badge-department">Dépt. {offre["departement"]}</span>', 
                                  unsafe_allow_html=True)
                    
                    if offre.get('experience_libelle'):
                        st.markdown(f'<span class="badge badge-experience">{offre["experience_libelle"]}</span>', 
                                  unsafe_allow_html=True)
                    
                    # Informations supplémentaires
                    if offre.get('salaire_libelle'):
                        st.info(f"💰 {offre['salaire_libelle']}")
                    
                    if offre.get('date_actualisation'):
                        st.caption(f"🔄 {offre['date_actualisation']}")
                
                st.markdown("---")

# TAB 2: Statistiques
with tab2:
    if not df_offers.empty:
        st.subheader("📊 Analyse statistique")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique par département
            if 'departement' in df_offers.columns:
                by_dep = (
                    df_offers.dropna(subset=["departement"])
                    .groupby("departement")
                    .size()
                    .reset_index(name="nb_offres")
                    .sort_values(by="nb_offres", ascending=True)
                    .tail(15)  # Limiter aux 15 premiers
                )
                
                if not by_dep.empty:
                    fig_dep = px.bar(
                        by_dep,
                        y="departement",
                        x="nb_offres",
                        orientation='h',
                        title="Top 15 des départements",
                        color="nb_offres",
                        color_continuous_scale="Viridis",
                    )
                    fig_dep.update_layout(height=500)
                    st.plotly_chart(fig_dep, use_container_width=True)
        
        with col2:
            # Graphique par type de contrat
            if 'type_contrat_libelle' in df_offers.columns:
                by_contrat = (
                    df_offers.dropna(subset=["type_contrat_libelle"])
                    .groupby("type_contrat_libelle")
                    .size()
                    .reset_index(name="nb_offres")
                )
                
                if not by_contrat.empty:
                    fig_contrat = px.pie(
                        by_contrat,
                        values="nb_offres",
                        names="type_contrat_libelle",
                        title="Répartition par type de contrat",
                        hole=0.4,
                    )
                    st.plotly_chart(fig_contrat, use_container_width=True)
        
        # Graphique temporel (si date disponible)
        if 'date_actualisation' in df_offers.columns:
            df_offers['date_actualisation'] = pd.to_datetime(df_offers['date_actualisation'], format='ISO8601', errors='coerce')
            timeline = df_offers.dropna(subset=['date_actualisation']).copy()
            timeline['date'] = timeline['date_actualisation'].dt.date
            
            if not timeline.empty:
                timeline_counts = timeline.groupby('date').size().reset_index(name='nb_offres')
                
                fig_timeline = px.line(
                    timeline_counts,
                    x='date',
                    y='nb_offres',
                    title="Évolution des publications",
                    markers=True,
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)

# TAB 3: Analyse détaillée
with tab3:
    if not df_offers.empty:
        st.subheader("🔍 Analyse approfondie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Analyse des compétences (exemple)
            st.markdown("### 📝 Mots-clés fréquents")
            if 'description' in df_offers.columns:
                # Extraire les mots-clés des descriptions
                all_text = " ".join(df_offers['description'].dropna().astype(str).tolist())
                # Simplifié - à améliorer avec NLP
                keywords = ["python", "java", "sql", "javascript", "data", "cloud", "devops", "agile"]
                keyword_counts = {kw: all_text.lower().count(kw) for kw in keywords}
                
                # Afficher les mots-clés
                for kw, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
                    if count > 0:
                        progress = min(count / 50, 1.0)  # Normalisation
                        st.write(f"**{kw}**")
                        st.progress(progress, text=f"{count} occurrences")
        
        with col2:
            # Export des données
            st.markdown("### 💾 Export des données")
            
            # Format d'export
            export_format = st.selectbox(
                "Format d'export",
                ["CSV", "Excel", "JSON"],
                index=0
            )
            
            # Colonnes à exporter
            available_cols = df_offers.columns.tolist()
            default_cols = ['intitule', 'entreprise_nom', 'lieu_travail', 
                          'type_contrat_libelle', 'date_actualisation']
            selected_cols = st.multiselect(
                "Colonnes à exporter",
                available_cols,
                default=default_cols
            )
            
            if st.button("📥 Exporter les données", use_container_width=True):
                export_df = df_offers[selected_cols] if selected_cols else df_offers
                
                if export_format == "CSV":
                    csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="Télécharger CSV",
                        data=csv,
                        file_name="offres_france_travail.csv",
                        mime="text/csv",
                    )
                elif export_format == "Excel":
                    # Nécessite openpyxl
                    buffer = BytesIO()
                    export_df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        label="Télécharger Excel",
                        data=buffer.getvalue(),
                        file_name="offres_france_travail.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
        
        # Recherche par ROME
        st.markdown("### 🔎 Recherche par code ROME")
        if 'rome_code' in df_offers.columns:
            unique_rome = df_offers['rome_code'].dropna().unique()
            rome_selected = st.selectbox(
                "Sélectionnez un code ROME",
                options=["(Tous)"] + sorted(unique_rome.tolist())
            )
            
            if rome_selected != "(Tous)":
                rome_offers = df_offers[df_offers['rome_code'] == rome_selected]
                st.write(f"**{len(rome_offers)}** offres pour le code ROME {rome_selected}")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 20px;">
        <p><strong>France Travail – Explorateur d'offres</strong></p>
        <p style="font-size: 12px;">
            Données mises à jour quotidiennement • 
            Source: API France Travail • 
            © 2024
        </p>
    </div>
""", unsafe_allow_html=True)

# Ajouter un indicateur de chargement en bas
if st.session_state.get('loading', False):
    st.markdown("""
        <div style="position: fixed; bottom: 0; right: 0; margin: 20px; padding: 10px 20px; 
                    background: #667eea; color: white; border-radius: 20px; font-size: 14px;">
            🔄 Chargement...
        </div>
    """, unsafe_allow_html=True)