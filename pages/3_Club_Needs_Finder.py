# pages/3_Club_Needs_Finder.py
import streamlit as st
import pandas as pd
import base64
from weasyprint import HTML
from match_finder import MatchFinder
from player_analyzer import PlayerAnalyzer, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE

# --- Cache resources to load them only once ---
@st.cache_resource
def get_analyzer_and_finder():
    """Initializes both the PlayerAnalyzer and MatchFinder."""
    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    finder = MatchFinder(
        club_profiles_path='./data/processed/club_profiles_final.json',
        player_analyzer=analyzer
    )
    return finder

@st.cache_data
def get_club_and_position_lists(_finder):
    """Loads data to populate the selection boxes."""
    club_list = sorted(list(_finder.club_profiles.keys()))
    position_list = ['Defender', 'Midfielder', 'Forward']
    return club_list, position_list

def generate_player_report_html(results_df, club_name, position):
    """Generates a clean HTML string for the player recommendations report."""
    
    # Prepare the data for display
    results_df['Key Strengths'] = results_df['Key Strengths'].apply(
        lambda x: "<ul style='padding-left: 15px; margin: 0; text-align: left;'>" + 
                  "".join([f"<li>{s.strip()}</li>" for s in x.split('|')]) + 
                  "</ul>"
    )
    results_df['Match Score'] = results_df['Match Score'].map('{:.2f}'.format)
    if "Rank" not in results_df.columns:
        results_df.insert(0, "Rank", range(1, 1 + len(results_df)))

    top_5_html = results_df.head(5).style.hide(axis="index").to_html(escape=False)
    remaining_html = results_df.iloc[5:].style.hide(axis="index").to_html(escape=False)

    report = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; color: #333; }}
                .report-container {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; max-width: 900px; margin: auto; }}
                .header {{ display: flex; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 10px; }}
                h1 {{ margin: 0; font-size: 24px; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; color: #00529B; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <h1>Talent Finder Report</h1>
                </div>
                <p><strong>Club Searched:</strong> {club_name} | <strong>Position of Need:</strong> {position}</p>
                
                <h2>Top 5 Recommendations</h2>
                {top_5_html}
                
                <h2>Best of the Rest</h2>
                {remaining_html}
            </div>
        </body>
    </html>
    """
    return report

# --- Main App UI ---
st.title("Club Needs & Talent Finder")

st.markdown("""
<style>
    /* Main download button (blue) */
    div.stDownloadButton > button {
        background-color: #007bff;
        color: white !important;
        border-radius: 8px;
    }
    div.stDownloadButton > button:hover {
        background-color: #0056b3;
        color: white !important;
    }
    /* Vertically center content in the header columns */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

finder = get_analyzer_and_finder()
club_list, position_list = get_club_and_position_lists(finder)

st.header("1. Define Recruitment Profile")

col1, col2 = st.columns(2)
with col1:
    selected_club = st.selectbox("Select Your Club:", club_list)
with col2:
    selected_position = st.selectbox("Select Position of Need:", position_list)

if st.button("Find Best Player Matches", use_container_width=True, type="primary"):
    if selected_club and selected_position:
        with st.spinner(f"Analyzing all {selected_position}s for {selected_club}..."):
            best_players = finder.find_best_players_for_club(selected_club, selected_position)
            # Save results to session state to persist them across reruns
            st.session_state.best_players_results = best_players
            st.session_state.selected_club_for_report = selected_club
            st.session_state.selected_position_for_report = selected_position

# --- This block now handles displaying the results AND the download button ---
if 'best_players_results' in st.session_state:
    best_players = st.session_state.best_players_results
    
    if best_players:
        results_df = pd.DataFrame(best_players)
        
        st.markdown("---")
        # --- HEADER WITH CENTERED DOWNLOAD BUTTON ---
        col1_header, col2_header = st.columns([3, 1])
        with col1_header:
            st.header("Top Player Recommendations")
        with col2_header:
            report_html = generate_player_report_html(
                pd.DataFrame(best_players).copy(),
                st.session_state.selected_club_for_report,
                st.session_state.selected_position_for_report
            )
            pdf_bytes = HTML(string=report_html).write_pdf()
            st.download_button(
                label="📄 Download Report",
                data=pdf_bytes,
                file_name=f"talent_finder_{st.session_state.selected_club_for_report.replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
        
        # 1. Prepare the full DataFrame for display
        results_df.insert(0, "Rank", range(1, 1 + len(results_df)))
        results_df['Key Strengths'] = results_df['Key Strengths'].apply(
            lambda x: "<ul style='padding-left: 15px; margin: 0; text-align: left;'>" + 
                      "".join([f"<li>{s.strip()}</li>" for s in x.split('|')]) + 
                      "</ul>"
        )

        # 2. Split the data
        top_5_df = results_df.head(5)
        remaining_df = results_df.iloc[5:]

        # 3. Display the top 5
        st.markdown(
            top_5_df.style.format({"Match Score": "{:.2f}"}).hide(axis="index").to_html(escape=False), 
            unsafe_allow_html=True
        )

        # 4. Add the divider
        st.divider()

        # 5. Display the rest
        if not remaining_df.empty:
            st.markdown(
                remaining_df.style.format({"Match Score": "{:.2f}"}).hide(axis="index").to_html(escape=False),
                unsafe_allow_html=True
            )
    else:
        st.warning("No suitable players found for the selected criteria.")