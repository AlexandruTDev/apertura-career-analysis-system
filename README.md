# Apertura Intelligence: Player-Club Match Analysis
Apertura Intelligence is a data-driven Streamlit application designed to provide deep analysis for football player recruitment.

* It moves beyond simple statistics to generate a "Best Match Score," identifying the most suitable clubs for a player based on a holistic view of tactical fit, player growth potential, and deal attractiveness.

* This project was developed as a Proof of Concept, demonstrating how modern data analytics can create a strategic advantage for clubs, agents, and the league as a whole.

# Key Features
* Dynamic Player Profiling:<br />
Generates a 360-degree statistical "fingerprint" for any player, benchmarking their performance against peers in the same position.

* In-Depth Club Analysis:<br />
Creates a unique "Tactical Fingerprint" for every club in the database, including newly promoted teams, by analyzing their on-field playing style.

* The "Best Match Score":<br />
A proprietary algorithm that calculates a single, actionable score from 0-100, ranking the suitability of each club for a specific player.

* Full League Context:<br />
Provides complete transparency by showing not just the top 3 recommendations, but a ranked list of every club in the league, allowing scouts to validate the data against their own insights.

* One-Click PDF Reporting:<br />
Instantly generates and downloads clean, professional dossiers for any player-club match or individual club profile, streamlining communication between scouts, coaches, and management.

# Project Structure
career-analysis-system/<br />
├<br />
├─── data/<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── manual/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Manually created data files<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── processed/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Cleaned, merged, and final data files<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── raw/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# The initial, unchanged data from sources<br />
├<br />
├─── pages/<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 1_Club_Profile.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Streamlit page for club analysis<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 2_Player_Analysis.py&nbsp;&nbsp;&nbsp;# Streamlit page for player analysis<br />
├<br />
├─── scrapers/<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── data_collector.py&nbsp;&nbsp;&nbsp;&nbsp;# Scripts for fetching and processing data<br />
├&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── ...<br />
├<br />
├───app.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Main Streamlit application file<br />
├───match_finder.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Core class for the matching algorithm<br />
├───player_analyzer.py&nbsp;&nbsp;&nbsp;# Core class for player statistical analysis<br />
├───shell.nix&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Nix environment configuration<br />
└───README.md<br />

# How to Run the Application
* This project uses the Nix package manager to ensure a reproducible and consistent development environment.

* Start the Nix Shell:<br />
  * From the project's root directory, run the following command:<br /> 
`nix-shell`<br />
  * This will automatically download and configure all necessary system and Python dependencies.<br />

* Run the Streamlit App:<br />
  * Once you are inside the Nix shell, start the Streamlit server:<br />
`streamlit run app.py` or `streamlit run app.py --server.address 0.0.0.0 --server.enableCORS false` (in case there are environment limitations)<br />

* View the App:<br />
  * Open a web browser and navigate to the local URL provided by Streamlit (usually http://localhost:8501).<br />

# Data Pipeline
The application is powered by a robust data pipeline that transforms raw data into actionable insights.<br />

**1. Raw Data Ingestion:**<br />
* The system starts with raw CSV files for player stats, team stats, and physical metrics.<br />

**2. Data Processing & Enrichment:**<br />
* A series of scripts in the `scrapers/` directory are run to clean the data, add team names, and integrate newly promoted clubs.<br />

**3. Profile Generation:**<br />
* The processed data is aggregated to create the `club_profiles_final.json`, which serves as the "single source of truth" for the main application.
