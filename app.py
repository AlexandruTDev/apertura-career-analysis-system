# app.py
import streamlit as st

st.set_page_config(
    page_title="Superliga Intelligence Hub",
    page_icon="🇷🇴",
    layout="wide"
)

st.title("🇷🇴 Superliga Intelligence Hub")
st.sidebar.success("Select an analysis tool from the options above.")

st.markdown("""
    ### Welcome to the Superliga Intelligence Hub.
    
    This is the central point for all our analytical tools for the Romanian Superliga.
    
    **Please select a tool from the sidebar on the left to begin:**
    
    - **Club Profile:** For a deep-dive into a specific club's tactical, squad, and financial data.
    - **Player Analysis:** To find the best club matches for a specific player.
    - **Club Needs & Talent Finder** To discover new talent. Select a club and a position of need to get a ranked list of the best-fitting players from across the league.
""")