# pages/3_Club_Needs_Finder.py
import streamlit as st
import pandas as pd
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

# --- Main App UI ---
st.title("Club Needs & Talent Finder")

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
            
            if best_players:
                st.markdown("---")
                st.header("Top Player Recommendations")
                
                results_df = pd.DataFrame(best_players)
                
                # 1. Prepare the full DataFrame
                results_df.insert(0, "Rank", range(1, 1 + len(results_df)))
                results_df['Key Strengths'] = results_df['Key Strengths'].apply(
                    lambda x: "<ul style='padding-left: 15px; margin: 0; text-align: left;'>" + 
                              "".join([f"<li>{s.strip()}</li>" for s in x.split('|')]) + 
                              "</ul>"
                )

                # 2. Split the data into top-tier and the rest
                top_5_df = results_df.head(5)
                remaining_df = results_df.iloc[5:]

                # 3. Display the top 5 with full styling and multi-line strengths
                st.markdown(
                    top_5_df.style.format({"Match Score": "{:.2f}"})\
                        .hide(axis="index")\
                        .to_html(escape=False), 
                    unsafe_allow_html=True
                )

                # 4. Add the visual divider
                st.divider()

                # 5. Display the rest of the teams, rendering the HTML correctly
                if not remaining_df.empty:
                    st.markdown(
                        remaining_df.style.format({"Match Score": "{:.2f}"})\
                            .hide(axis="index")\
                            .to_html(escape=False),
                        unsafe_allow_html=True
                    )
            else:
                st.warning("No suitable players found for the selected criteria.")