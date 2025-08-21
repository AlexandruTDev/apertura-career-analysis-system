# pages/1_Club_Profile.py
import streamlit as st
import json
import pandas as pd
import base64
from weasyprint import HTML

# --- Helper Functions ---
@st.cache_data
def load_data(profiles_path, crests_path):
    """Loads both the club profiles and the club crests data."""
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles_data = json.load(f)
        club_profiles = {club['club_name']: club for club in profiles_data}
        
        crests_df = pd.read_csv(crests_path)
        crest_dict = pd.Series(crests_df.crest_url.values,index=crests_df.club_name_official).to_dict()
        
        return club_profiles, crest_dict
    except FileNotFoundError:
        return None, None

def generate_club_report_html(club_data, crest_url):
    """Generates a clean HTML string for the club profile report."""
    tactical_data = club_data.get('poc_metrics', {}).get('tactical_analysis', {})
    
    # Extract the full statistical profile
    statistical_profile = club_data.get('statistical_profile', {})
    
    # Find the top 5 statistical strengths based on raw totals
    # We filter out some less meaningful stats like 'matches'
    top_stats = sorted(
        {k: v for k, v in statistical_profile.items() if k not in ['total.matches', 'total.matchesInStart']}.items(), 
        key=lambda item: item[1], 
        reverse=True
    )[:5]
    
    stats_html = "".join([f"<li><b>{stat[0].replace('total.', '').replace('successful', 'Successful ').title()}:</b> {stat[1]:,.0f}</li>" for stat in top_stats])

    report = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; color: #333; }}
                .report-container {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; max-width: 800px; margin: auto; }}
                .header {{ display: flex; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }}
                .header img {{ width: 60px; height: 60px; margin-right: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 0; color: #666; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; color: #00529B; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin-bottom: 8px; font-size: 1.1em; }}
                b {{ color: #111; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <img src="{crest_url}">
                    <div>
                        <h1>Club Tactical Profile</h1>
                        <p><strong>{club_data['club_name']}</strong> | Season 2024/2025</p>
                    </div>
                </div>
                <h2>Tactical DNA (Top 5 Metrics)</h2>
                <ul>{stats_html}</ul>
                <h2>Implied Player Needs</h2>
                <p>Based on their statistical profile, this club's system appears to favor a specific style of play, creating opportunities for players with certain key attributes.</p>
            </div>
        </body>
    </html>
    """
    return report

def create_metric_card(icon_url: str, label: str, value: str):
    """Helper function to generate the HTML for a styled metric card."""
    st.markdown(f"""
    <div style="text-align: center; padding: 15px; border-radius: 5px; background-color: #FAFAFA; height: 100%;">
        <img src="{icon_url}" width="50" style="margin-bottom: 10px;">
        <h4 style="color: gray; margin: 0; text-transform: uppercase; font-size: 1em;">{label}</h4>
        <div style="margin-top: 5px;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def generate_club_report_html(club_data, crest_url):
    """Generates a clean HTML string for the club profile report."""
    
    # Extract the tactical data from the club's profile
    tactical_data = club_data.get('poc_metrics', {}).get('tactical_analysis', {})
    
    # Prepare the key metrics for display in the report
    stats_to_show = {
        "Primary Formation": tactical_data.get('primary_formation', 'N/A'),
        "Avg. Possession": f"{tactical_data.get('avg_possession_percentage', 0)}%",
        "Pressing (PPDA)": f"{tactical_data.get('ppda', 0):.1f}",
        "Avg. Pass Length": f"{tactical_data.get('avg_pass_length', 0):.1f}m"
    }
    
    stats_html = "".join([f"<li><b>{stat_name}:</b> {stat_value}</li>" for stat_name, stat_value in stats_to_show.items()])

    report = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; color: #333; }}
                .report-container {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; max-width: 800px; margin: auto; }}
                .header {{ display: flex; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }}
                .header img {{ width: 60px; height: 60px; margin-right: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 0; color: #666; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; color: #00529B; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin-bottom: 8px; font-size: 1.1em; }}
                b {{ color: #111; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <img src="{crest_url}">
                    <div>
                        <h1>Club Tactical Profile</h1>
                        <p><strong>{club_data['club_name']}</strong> | Season 2024-2025</p>
                    </div>
                </div>
                <h2>Key Tactical Metrics</h2>
                <ul>{stats_html}</ul>
            </div>
        </body>
    </html>
    """
    return report

# This mapping connects our clean system names to the names scraped from the official site.
OFFICIAL_NAME_MAPPING = {
    "Dinamo Bucuresti": "Dinamo Bucuresti", "FCS Bucuresti": "Fcsb",
    "Rapid Bucuresti": "Fc Rapid Bucuresti", "Otelul": "Otelul Galati",
    "CFR Cluj": "Cfr Cluj", "Botosani": "Fc Botosani",
    "Unirea Slobozia": "Unirea Slobozia", "Universitatea Craiova": "Universitatea Craiova",
    "UTA Arad": "Uta Arad", "Hermannstadt": "Afc Hermannstadt",
    "Universitatea Cluj": "Fc Universitatea Cluj", "Petrolul 52": "Petrolul Ploiesti",
    "Farul Constanta": "Fc Farul Constanta","Csíkszereda Miercurea Ciuc": "Fk Csikszereda",
    "FC Arges": "Fc Arges","Metaloglobus Bucuresti": "Metaloglobus"
}

# --- Main App UI ---

st.title("Club Profile Analysis")
st.markdown("""
    <style>
        .stButton>button {
            display: block;
            margin: 0 auto;
        }
        
        /* Main download button (blue) */
        div.stDownloadButton > button {
            background-color: #007bff;
            color: white;
        }
        div.stDownloadButton > button:hover {
            background-color: #0056b3;
            color: white; 
        }
        /* Close button (light red) */
        div[data-testid="stButton"] > button.st-emotion-cache-19n9s73 {
            background-color: #ffebee;
            color: #d32f2f;
        }
        div[data-testid="stButton"] > button.st-emotion-cache-19n9s73:hover {
            background-color: #ffcdd2;
            border-color: #d32f2f;
        }

        * Action button style (grey-blue) for View/Share */
        .action-button-container .stButton > button {
            background-color: #f0f2f6;
            color: #31333F;
            border: 1px solid #dde1e7;
        }
        .action-button-container .stButton > button:hover {
            background-color: #e6e8eb;
            border: 1px solid #31333F;
            color: #31333F;
        }
    </style>
    """, unsafe_allow_html=True)

club_profiles_dict, crest_dict = load_data(
    profiles_path='./data/processed/club_profiles_final.json',
    crests_path='./data/processed/club_crests.csv'
)

if not club_profiles_dict:
    st.error("❌ ERROR: Club profiles file not found. Please run main.py and crest_scraper.py to generate it.")
else:
    club_names = sorted(list(club_profiles_dict.keys()))
    
    # --- Session State Logic for Navigation & Persistence ---
    # If navigating from another page, set the current club and then clear the one-time trigger
    if 'selected_club' in st.session_state:
        st.session_state.current_profile_club = st.session_state.selected_club
        del st.session_state.selected_club
    
    # If no club is being viewed, default to the first one in the list
    if 'current_profile_club' not in st.session_state:
        st.session_state.current_profile_club = club_names[0]

    # Determine the index for the selectbox based on our persistent state
    default_index = club_names.index(st.session_state.current_profile_club)
    
    selected_club_name = st.selectbox(
        "Select a Club to Analyze:", 
        club_names, 
        index=default_index,
        key='club_selector' # Add a key for stability
    )

    # Update the persistent state if the user manually changes the selectbox
    st.session_state.current_profile_club = selected_club_name

    if selected_club_name:
        selected_club_data = club_profiles_dict[selected_club_name]
        official_name = OFFICIAL_NAME_MAPPING.get(selected_club_name)
        crest_url = crest_dict.get(official_name)
        
        if crest_url:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <img src="{crest_url}" width="60" style="margin-right: 15px;">
                <h1 style="margin: 0;">{selected_club_name} - Club Profile</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.title(f"{selected_club_name} - Club Profile")

        st.markdown("---")
        st.header("Tactical Identity")
        
        tactical_data = selected_club_data.get('poc_metrics', {}).get('tactical_analysis', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            primary = tactical_data.get('primary_formation', 'N/A')
            secondary = tactical_data.get('secondary_formation')
            value_html = f'<p style="font-size: 1.2em; font-weight: bold; margin: 0;">{primary}</p>'
            if secondary:
                value_html += f'<p style="font-size: 0.9em; color: gray; margin-top: 5px;">Secondary: {secondary}</p>'
            create_metric_card("https://cdn-icons-png.flaticon.com/512/2173/2173508.png", "Formations", value_html)
        
        with col2:
            value = f"{tactical_data.get('avg_possession_percentage', 0)}%"
            create_metric_card("https://cdn-icons-png.flaticon.com/512/2718/2718459.png", "Avg. Possession", f"<h2 style='margin: 0;'>{value}</h2>")
        with col3:
            value = f"{tactical_data.get('ppda', 0):.1f}"
            create_metric_card("https://cdn-icons-png.flaticon.com/512/8831/8831516.png", "Pressing (PPDA)", f"<h2 style='margin: 0;'>{value}</h2>")
        with col4:
            value = f"{tactical_data.get('avg_pass_length', 0):.1f}m"
            create_metric_card("https://cdn-icons-png.flaticon.com/512/10062/10062255.png", "Avg. Pass Length", f"<h2 style='margin: 0;'>{value}</h2>")
        
        #with st.expander("Show Raw JSON Data"):
         #   st.json(selected_club_data)

        # --- REPORTING SECTION ---
        st.markdown("---")
        if st.button("Share Club Profile", use_container_width=True, type="primary"):
            #crest_url = crest_dict.get(official_name, "https://i.imgur.com/8f2E3s3.png")
            
            # Generate the report for the selected club
            report_html = generate_club_report_html(selected_club_data, crest_url)
            st.session_state.club_report_to_show = report_html
            #st.session_state.report_for_club = selected_club_name
            st.rerun()

    else:
        st.warning("Could not find data for the selected club.")

# --- MODAL DISPLAY LOGIC ---
if 'club_report_to_show' in st.session_state:
    # Use the persistent state variable to ensure the correct data is used
    report_club_name = st.session_state.current_profile_club
    report_club_data = club_profiles_dict[report_club_name]
    report_official_name = OFFICIAL_NAME_MAPPING.get(report_club_name)
    report_crest_url = crest_dict.get(report_official_name, "https://i.imgur.com/8f2E3s3.png")
    
    st.header("Club Profile Report")
    st.components.v1.html(st.session_state.club_report_to_show, height=400, scrolling=True)

    # --- Use a single centered column for both buttons ---
    _ , col_center, _ = st.columns([1, 2, 1]) # Use columns to center the container
    with col_center:
        # Re-generate the report with the correct data to ensure consistency
        report_html_for_download = generate_club_report_html(report_club_data, report_crest_url)
        # Convert the HTML report to a PDF in memory
        pdf_bytes = HTML(string=st.session_state.club_report_to_show).write_pdf()

        # Create a download button for the PDF
        st.download_button(
            label="📄 Download as PDF",
            data=pdf_bytes,
            file_name=f"club_report_{report_club_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        if st.button("Close Report", use_container_width=True, type="secondary"):
            del st.session_state.club_report_to_show
            #del st.session_state.selected_club_name_report
            #del st.session_state.report_for_club
            st.rerun()

else:
    st.info("Please run the data processing pipeline to generate the required files.")
        