# pages/2_Player_Analysis.py
import streamlit as st
import pandas as pd
import json
from player_analyzer import PlayerAnalyzer, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE
from match_finder import MatchFinder
import base64
from weasyprint import HTML

# --- Helper Functions ---
@st.cache_data
def load_all_data(stats_path, crests_path):
    try:
        players_df = pd.read_csv(stats_path, na_values=[''])
        players_df['full_name'] = players_df['firstName'] + ' ' + players_df['lastName']
        crests_df = pd.read_csv(crests_path)
        crest_dict = pd.Series(crests_df.crest_url.values,index=crests_df.club_name_official).to_dict()
        return players_df, crest_dict
    except FileNotFoundError:
        return None, None

@st.cache_resource
def get_player_analyzer():
    return PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)

@st.cache_resource
def get_match_finder():
    return MatchFinder(club_profiles_path='./data/processed/club_profiles_final.json')

# This mapping connects our clean system names to the names scraped from the official site.
OFFICIAL_NAME_MAPPING = {
    "Dinamo Bucuresti": "Dinamo Bucuresti", "FCS Bucuresti": "Fcsb",
    "Rapid Bucuresti": "Fc Rapid Bucuresti", "Otelul": "Otelul Galati",
    "CFR Cluj": "Cfr Cluj", "Botosani": "Fc Botosani",
    "Unirea Slobozia": "Unirea Slobozia", "Universitatea Craiova": "Universitatea Craiova",
    "UTA Arad": "Uta Arad", "Hermannstadt": "Afc Hermannstadt",
    "Universitatea Cluj": "Fc Universitatea Cluj", "Petrolul 52": "Petrolul Ploiesti",
    "Farul Constanta": "Fc Farul Constanta","FC Arges": "ACSC FC Arges",
    "Csikszereda Miercurea Ciuc": "Fk Csikszereda",
    "Metaloglobus Bucuresti": "FC Metaloglobus Bucharest"
}

# Add this function near the top of your file
def generate_report_html(player_name, age, pos, top_skills, match_data, crest_url):
    """Generates a clean HTML string for the printable report."""
    
    skills_html = "".join([f"<li><b>{skill.replace('.', ' ').title()}:</b> Top {100-percentile:.0f}%</li>" for skill, percentile in top_skills])
    
    drivers_html = "".join([f"<li>✅ {driver}</li>" for driver in match_data['reason'].split(' | ')])

    report = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                .report-container {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; }}
                .header {{ display: flex; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                .header img {{ width: 70px; margin-right: 20px; }}
                h1 {{ margin: 0; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <img src="{crest_url}">
                    <div>
                        <h1>Player-Club Fit Analysis</h1>
                        <p><strong>Player:</strong> {player_name} | <strong>Position:</strong> {pos} | <strong>Age:</strong> {age}</p>
                    </div>
                </div>
                <h2>Top Match: {match_data['club_name']} (Score: {match_data['match_score']:.1f})</h2>
                <h3>Key Strengths</h3>
                <ul>{skills_html}</ul>
                <h3>Key Match Drivers</h3>
                <ul>{drivers_html}</ul>
            </div>
        </body>
    </html>
    """
    return report

# --- Main App ---
st.title("Player Analysis & Opportunity Finder")

# --- Center all buttons within their columns ---
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

if 'success_message' in st.session_state:
    st.success(st.session_state.success_message)
    # Clear the message so it doesn't reappear on the next interaction
    del st.session_state.success_message

players_df, crest_dict = load_all_data(
    stats_path='./data/processed/players_manually_enriched.csv',
    crests_path='./data/processed/club_crests.csv'
)
analyzer = get_player_analyzer()
match_finder = get_match_finder()

if players_df is not None and crest_dict is not None:
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

        st.markdown(
            """
            <style>
            .profile-card { padding: 15px; border-radius: 5px; background-color: #FAFAFA; border: 1px solid #EEEEEE; }
            .opportunity-card { padding: 15px; border-radius: 5px; background-color: #FFFFFF; border: 1px solid #EEEEEE; height: 350px; }
            </style>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="text-align: center;">{selected_player_name}</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''<div style="text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/1106/1106944.png" width="40">
                <p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase; margin: 0;">Position</p>
                <p style="font-size: 1.2em; font-weight: bold; margin: 0;">{pos}</p>
            </div>''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''<div style="text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/3333/3333673.png" width="40">
                <p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase; margin: 0;">Age</p>
                <p style="font-size: 1.2em; font-weight: bold; margin: 0;">{age} Years</p>
            </div>''', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<p style="font-size: 0.9em; color: gray; font-weight: bold; text-transform: uppercase;">Top Statistical Skills</p>', unsafe_allow_html=True)
        
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

        if st.button("Find Best Club Matches", use_container_width=True, type="primary"):
            st.session_state['show_matches_for_player'] = selected_player_name

        if st.session_state.get('show_matches_for_player') == selected_player_name:
            player_profile = analyzer.get_player_analysis(first_name, last_name)
            if player_profile:
                #best_matches = match_finder.find_best_matches(player_profile)
                all_matches_results  = match_finder.find_best_matches(player_profile)
                all_matches_df = pd.DataFrame(all_matches_results)

                st.markdown("---")
                st.header(f"Top 3 Club Matches for {selected_player_name}")
                
                top_3_matches = all_matches_df.head(3)
                cols = st.columns(3)
                for i, match in top_3_matches.iterrows():
                    with cols[i]:
                        # ---  UI LOGIC ---
            
                        # 1. Gather all data for the card
                        official_name = OFFICIAL_NAME_MAPPING.get(match['club_name'])
                        crest_url = crest_dict.get(official_name, "https://i.imgur.com/8f2E3s3.png")

                        drivers = match['reason'].split(' | ')
                        highlight_driver = match.get('highlight_driver') # Get the driver to highlight, if it exists
            
                        # 2. Build the drivers list with conditional coloring
                        drivers_html = ""
                        for driver in drivers:
                            color = "#D32F2F" if driver == highlight_driver else "#008000" # Red if it's the differentiator, else green
                            drivers_html += f"<li style='color:{color};'>✅ {driver}</li>"
            
                        # 3. Build the differentiator text line, if it exists
                        differentiator_html = ""
                        if 'differentiator_text' in match and pd.notna(match['differentiator_text']):
                            differentiator_html = f"<p style='color: #007bff; font-size: 0.9em; margin-top: 10px;'><b>⭐ Key Differentiator:</b> {match['differentiator_text']}</p>"

                        # 4. Build the complete HTML for the card in a single string
                        card_html = f"""
                        <div class="opportunity-card">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <img src="{crest_url}" width="50" style="margin-right: 10px;">
                                <h5 style="margin: 0;">{i+1}. {match['club_name']}</h5>
                            </div>
                            <div style="text-align: center;">
                                <p style="font-size: 0.9em; color: gray; margin: 0;">Best Match Score</p>
                                <p style="font-size: 2.5em; font-weight: bold; margin: 0;">{match['match_score']:.1f}</p>
                            </div>
                            <hr style="margin-top: 10px; margin-bottom: 10px;">
                            <b>Key Drivers:</b>
                            <ul style="margin-left: 20px; font-size: 0.9em; padding-left: 0;">{drivers_html}</ul>
                            {differentiator_html}
                        </div>
                        """

                        # 5. Render the HTML card
                        st.markdown(card_html, unsafe_allow_html=True)
                        # 5.1 Render the buttons immediately after the card, inside a styled container
                        st.markdown('<div class="action-button-container">', unsafe_allow_html=True)

                        # 6. Place the button AFTER the card
                        col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
                        
                        with col2_btn:
                            if st.button("View Full Club Profile",key=f"btn_{match['club_name']}"):
                                st.session_state['success_message'] = f"'{match['club_name']}' selected! Navigate to 'Club Profile' from the sidebar."
                                st.session_state['selected_club'] = match['club_name']
                                st.rerun()
                        # 7. Add a share button
                        col1_share, col2_share, col3_share = st.columns([1, 2, 1])
                        with col2_share:
                            if st.button("Share Report", key=f"share_{match['club_name']}"):
                                official_name = OFFICIAL_NAME_MAPPING.get(match['club_name'])
                                crest = crest_dict.get(official_name, "https://i.imgur.com/8f2E3s3.png")
            
                                # Generate the HTML for this specific match
                                report_html = generate_report_html(
                                    player_name=selected_player_name,
                                    age=age,
                                    pos=pos,
                                    top_skills=top_3_skills,
                                    match_data=match,
                                    crest_url=crest
                                )
                                # Store it in the session state to be shown in a modal
                                st.session_state.report_to_show = report_html
                        st.markdown('</div>', unsafe_allow_html=True)

                # --- MODAL DISPLAY LOGIC ---
                if 'report_to_show' in st.session_state:
                    st.header("Player-Club Fit Dossier")
                    # Display the report visually
                    st.components.v1.html(st.session_state.report_to_show, height=600, scrolling=True)
                    
                    # --- DOWNLOAD LOGIC ---
                    _ , col_center, _ = st.columns([1, 2, 1]) # Use columns to center the container
                    with col_center:
                        # 1. Convert the HTML report to a PDF in memory
                        pdf_bytes = HTML(string=st.session_state.report_to_show).write_pdf()
                    
                        # 2. Create a download button for the PDF
                        st.download_button(
                            label="📄 Download as PDF",
                            data=pdf_bytes,
                            file_name=f"player_report_{st.session_state.get('show_matches_for_player', 'report').replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        if st.button("Close Report",use_container_width=True, type="secondary"):
                            del st.session_state.report_to_show
                            st.rerun()

                st.markdown("---")
                st.subheader("Full League Context")

                # Correctly slice the DataFrame to get the remaining teams
                remaining_teams_df = all_matches_df.iloc[3:]

                if not remaining_teams_df.empty:
                    # Prepare a clean DataFrame for display
                    
                    display_df = remaining_teams_df[['club_name', 'match_score']].copy()
                    
                    display_df['match_score'] = display_df['match_score']
                    display_df['Score'] = display_df['match_score']
                    
                    display_df.rename(columns={
                        'club_name': 'Club Name',
                        'match_score': 'Score Visual'
                    }, inplace=True)

                    # Apply custom styling to the 'Score' text column
                    def style_score(val):
                        if val >= 70: color = 'green'
                        elif val >= 60: color = 'orange'
                        else: color = 'red'
                        return f'color: {color}; font-weight: bold; font-size: 1.5em;'

                    styled_df = display_df.style.map(style_score, subset=['Score'])\
                                        .format({'Score': '{:.1f}'})

                    st.dataframe(
                        styled_df,
                        column_order=("Club Name", "Score Visual", "Score"),
                        hide_index=True,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "Score Visual": st.column_config.ProgressColumn(
                                "Overall Score",
                                format=" ",
                                min_value=0,
                                max_value=100,
                            ),
                            "Score": st.column_config.TextColumn(
                                "Score",
                                width="80"
                            )
                        }
                    )
            else:
                st.error("Could not generate a profile for the selected player.")
else:
    st.info("Please run the data processing pipeline to generate the required files.")