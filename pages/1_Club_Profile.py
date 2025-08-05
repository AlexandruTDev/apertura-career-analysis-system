# dashboard.py (Final, Polished, and Robust Version)
import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide", page_title="Superliga Club Analysis")

@st.cache_data
def load_data(file_path):
    """Loads the final club profiles JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {club['club_name']: club for club in data}
    except FileNotFoundError:
        return None

def create_metric_card(icon_url: str, label: str, value: str):
    """Helper function to generate the HTML for a styled metric card."""
    st.markdown(f"""
    <div style="text-align: center; padding: 15px; border-radius: 5px; background-color: #FAFAFA; height: 100%;">
        <img src="{icon_url}" width="50" style="margin-bottom: 10px;">
        <h4 style="color: gray; margin: 0; text-transform: uppercase; font-size: 1em;">{label}</h4>
        <h2 style="margin: 0;">{value}</h2>
    </div>
    """, unsafe_allow_html=True)

# --- UI Elements ---
col1_title, col2_title = st.columns([1, 10])
with col1_title:
    st.image("https://tmssl.akamaized.net/images/logo/header/ro1.png?lm=1548242838", width=70)
with col2_title:
    st.title("Club Intelligence Dashboard - Superliga")

club_profiles_dict = load_data('./data/processed/club_profiles_final.json')

if not club_profiles_dict:
    st.error("❌ ERROR: Club profiles file not found. Please run main.py to generate it.")
else:
    club_names = sorted(list(club_profiles_dict.keys()))
    selected_club_name = st.selectbox("Select a Club to Analyze:", club_names)
    
    selected_club_data = club_profiles_dict[selected_club_name]
    
    st.markdown("---")
    
    st.header(f"Tactical Identity: {selected_club_name}")
    
    tactical_data = selected_club_data.get('poc_metrics', {}).get('tactical_analysis', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    # --- Card 1: Formation (with dynamic secondary formation) ---
    with col1:
        primary = tactical_data.get('primary_formation', 'N/A')
        secondary = tactical_data.get('secondary_formation')
        
        value_html = f"{primary}"
        if secondary:
            value_html += f" <span style='font-size: 0.6em; color: gray;'>/ {secondary}</span>"
        
        create_metric_card(
            icon_url="https://cdn-icons-png.flaticon.com/512/2173/2173508.png",
            label="Formations",
            value=value_html
        )

    # --- Card 2: Possession ---
    with col2:
        create_metric_card(
            icon_url="https://cdn-icons-png.flaticon.com/512/2718/2718459.png",
            label="Avg. Possession",
            value=f"{tactical_data.get('avg_possession_percentage', 0)}%"
        )

    # --- Card 3: Pressing ---
    with col3:
        create_metric_card(
            icon_url="https://cdn-icons-png.flaticon.com/512/8831/8831516.png",
            label="Pressing (PPDA)",
            value=f"{tactical_data.get('ppda', 0):.1f}"
        )
        
    # --- Card 4: Pass Length ---
    with col4:
        create_metric_card(
            icon_url="https://cdn-icons-png.flaticon.com/512/10062/10062255.png",
            label="Avg. Pass Length",
            value=f"{tactical_data.get('avg_pass_length', 0):.1f}m"
        )

    with st.expander("Show Raw JSON Data"):
        st.json(selected_club_data)