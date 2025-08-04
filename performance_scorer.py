# performance_scorer.py

from player_analyzer import PlayerAnalyzer, PLAYERS_STATS_FILE, PLAYERS_PHYSICAL_FILE
from collections import Counter

# This dictionary defines the WEIGHTS for our KPIs for each position.
# The weights for each position must add up to 1.0.
KPI_WEIGHTS = {
    "Defender": {
        'percent.defensiveDuelsWon': 0.40,
        'total.interceptions': 0.30,
        'percent.aerialDuelsWon': 0.20,
        'Max Speed': 0.05,
        'Count High Acceleration': 0.05
    },
    "Midfielder": {
        'percent.successfulPasses': 0.30,
        'total.passesToFinalThird': 0.25,
        'total.duelsWon': 0.20,
        'Total Distance': 0.15,
        'High Intensity (HI) Distance': 0.10
    },
    "Forward": {
        'total.goals': 0.30,
        'percent.goalConversion': 0.30,
        'total.xgShot': 0.20,
        'Max Speed': 0.10,
        'Count Sprint': 0.10
    }
}

class PlayerPerformanceScorer:
    def __init__(self, analyzer: PlayerAnalyzer):
        """
        Initializes the scorer with a pre-loaded PlayerAnalyzer instance.
        """
        self.analyzer = analyzer
        print("✅ PlayerPerformanceScorer initialized.")

    def calculate_performance_score(self, first_name: str, last_name: str) -> float | None:
        """
        Calculates a single, weighted performance score for a player.
        """
        analysis_results = self.analyzer.get_player_analysis(first_name, last_name)
        
        if not analysis_results:
            return None

        position_group = analysis_results['position_group']
        percentiles = analysis_results['analysis'] # analysis contains the kpi data
        
        if position_group not in KPI_WEIGHTS:
            print(f"No KPI weights defined for position group: {position_group}")
            return None

        weights = KPI_WEIGHTS[position_group]
        
        final_score = 0
        total_weight = 0 # To normalize the score in case a KPI is missing
        
        for kpi, data in percentiles.items():
            if kpi in weights:
                final_score += (data['percentile'] * weights[kpi])
                total_weight += weights[kpi]
        
        # Normalize the score in case some KPIs were not available for the player
        if total_weight > 0:
            normalized_score = final_score / total_weight
        else:
            normalized_score = 0

        return normalized_score

# --- Main execution block ---
if __name__ == "__main__":
    # 1. First, create an instance of our analyzer
    analyzer = PlayerAnalyzer(stats_path=PLAYERS_STATS_FILE, physical_path=PLAYERS_PHYSICAL_FILE)
    
    # 2. Then, create an instance of our scorer, passing the analyzer to it
    scorer = PlayerPerformanceScorer(analyzer=analyzer)
    
    # 3. Finally, calculate the score for our test case
    first_name, last_name = "Kennedy Kofi", "Boateng"
    score = scorer.calculate_performance_score(first_name, last_name)
    
    if score is not None:
        # We can also call the display function from the analyzer for a full report
        analyzer.display_analysis(first_name, last_name)
        
        print(f"\n--- 📈 Final Calculated Performance Score ---")
        print(f"Overall Score for {first_name} {last_name}: {score:.1f}")