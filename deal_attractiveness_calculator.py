# deal_attractiveness_calculator.py (Final Version with Disruption Score)

class DealAttractivenessCalculator:
    def __init__(self):
        # --- THE FIX IS HERE: New, re-balanced weights ---
        # We now include the disruption score as a key factor.
        self.weights = {
            'squad_depth': 0.35,      # 35% importance
            'incumbent_age': 0.25,    # 25% importance
            'financial_power': 0.20, # 20% importance
            'squad_disruption': 0.20 # 20% importance
        }
        print("✅ DealAttractivenessCalculator (with Disruption Score) initialized.")

    def _normalize_value(self, value, min_val, max_val):
        """Helper function to scale a value to a 0-100 score."""
        if max_val == min_val:
            return 50 
        return 100 * (value - min_val) / (max_val - min_val)

    def calculate_deal_attractiveness(self, club_profile: dict, all_clubs_data: list) -> dict:
        """
        Calculates a 'Deal Attractiveness' score for each position at a given club.
        """
        attractiveness_scores = {}
        squad_analysis = club_profile.get('poc_metrics', {}).get('current_squad_analysis', {})
        
        # --- Create a league-wide context for normalization ---
        all_depths = [pos['depth'] for club in all_clubs_data for pos in club['poc_metrics']['current_squad_analysis'].values()]
        all_ages = [pos['avg_age'] for club in all_clubs_data for pos in club['poc_metrics']['current_squad_analysis'].values()]
        
        min_depth, max_depth = min(all_depths), max(all_depths)
        min_age, max_age = min(all_ages), max(all_ages)
        
        # --- Get the financial and disruption scores ---
        financial_score = 50 # Default score
        net_spend_str = club_profile.get('poc_metrics', {}).get('financial_analysis', {}).get('two_year_net_spend', '€0.0m')
        if 'm' in net_spend_str and float(net_spend_str.replace('€','').replace('m','')) > 0:
            financial_score = 80 
        elif '-' in net_spend_str:
            financial_score = 20

        # Scale the 0-10 disruption score to 0-100 to match the other scores
        disruption_score = club_profile.get('poc_metrics', {}).get('squad_disruption_analysis', {}).get('squad_disruption_score', 0.0) * 10

        for position, data in squad_analysis.items():
            # Invert depth score (lower depth is better)
            depth_score = 100 - self._normalize_value(data['depth'], min_depth, max_depth)
            # Higher age is better
            age_score = self._normalize_value(data['avg_age'], min_age, max_age)
            
            # --- THE FIX IS HERE: Add the disruption score to the final calculation ---
            final_score = (
                depth_score * self.weights['squad_depth'] +
                age_score * self.weights['incumbent_age'] +
                financial_score * self.weights['financial_power'] +
                disruption_score * self.weights['squad_disruption'] # <-- New Component
            )
            
            attractiveness_scores[position] = round(final_score, 1)
            
        return attractiveness_scores