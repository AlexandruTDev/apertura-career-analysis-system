# pages/2_Player_Analysis.py (Version-Compatible)
import streamlit as st
import pandas as pd
import unicodedata
from player_analyzer import PlayerAnalyzer, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Player Analysis")

# --- Helper Functions ---
@st.cache_data
def load_all_data(stats_path):
    """Loads and prepares the main player data file."""
    try:
        players_df = pd.read_csv(stats_path, na_values=[''])
        players_df['full_name'] = players_df['firstName'] + ' ' + players_df['lastName']
        return players_df
    except FileNotFoundError:
        return None

@st.cache_resource
def get_player_analyzer():
    """Creates and caches a single instance of the PlayerAnalyzer."""
    print("--- Initializing PlayerAnalyzer ---")
    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    return analyzer

# --- Main App ---
st.title("Player Analysis & Opportunity Finder")

players_df = load_all_data(
    stats_path='./data/processed/players_manually_enriched.csv'
)
analyzer = get_player_analyzer()

if players_df is not None:
    st.header("1. Select Player to Analyze")
    player_list = sorted(players_df['full_name'].dropna().unique())
    selected_player_name = st.selectbox("Select a player from the database:", player_list)
    
    if selected_player_name:
        player_data = players_df[players_df['full_name'] == selected_player_name].iloc[0]
        
        pos = player_data['positions.position.name']
        
        today = pd.to_datetime('today')
        birth_date = pd.to_datetime(player_data['birthDate'])
        age = int((today - birth_date).days / 365.25)
        
        st.subheader("Player Profile:")
        
        # --- THE FIX IS HERE ---
        # We create the card effect with a styled div in markdown.
        st.markdown(
            """
            <style>
            .profile-card {
                padding: 15px;
                border-radius: 5px;
                background-color: #FAFAFA;
                border: 1px solid #EEEEEE;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(f'<div class="profile-card">', unsafe_allow_html=True)
        
        st.markdown(f'<h3 style="text-align: center;">{selected_player_name}</h3>', unsafe_allow_html=True)
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/1106/1106944.png" width="40">
                <p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase; margin: 0;">Position</p>
                <p style="font-size: 1.2em; font-weight: bold; margin: 0;">{pos}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/3333/3333673.png" width="40">
                <p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase; margin: 0;">Age</p>
                <p style="font-size: 1.2em; font-weight: bold; margin: 0;">{age} Years</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown('<p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase;">Top Statistical Skills</p>', unsafe_allow_html=True)
        
        # Call the analyzer to get the player's skills
        first_name = player_data['firstName']
        last_name = player_data['lastName']
        analysis_results = analyzer.get_player_analysis(first_name, last_name)
        
        if analysis_results and 'analysis' in analysis_results:
            percentiles = {kpi: data['percentile'] for kpi, data in analysis_results['analysis'].items()}
            top_3_skills = sorted(percentiles.items(), key=lambda item: item[1], reverse=True)[:3]
            
            skills_html = "<ul>"
            for skill, percentile in top_3_skills:
                skills_html += f"<li><b>{skill.replace('.', ' ').title()}</b> (Top {100-percentile:.0f}%)</li>"
            skills_html += "</ul>"
            st.markdown(skills_html, unsafe_allow_html=True)
        else:
            st.markdown("<i>No performance data available for this player.</i>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        if st.button("Find Best Club Matches", use_container_width=True, type="primary"):
            st.success(f"ANALYSIS TRIGGERED for {selected_player_name}...")

else:
    st.info("Please run the data processing pipeline to generate the required files.")