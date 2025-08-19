# plot_heatmap_away.py
import json
import matplotlib.pyplot as plt
import pandas as pd

def plot_heatmap_from_json(json_path: str, output_image_path: str):
    """
    Reads a JSON file of heatmap coordinates and generates a scatter plot,
    assuming a top-right origin (for away teams).
    """
    print(f"--- Loading heatmap data from: {json_path} ---")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        heatmap_points = data.get('heatmap', [])
        if not heatmap_points:
            print("No heatmap data found in the JSON file.")
            return
            
        df = pd.DataFrame(heatmap_points)
        
        # --- THE FIX IS HERE ---
        # To simulate a top-right origin, we invert BOTH axes.
        # x_new = 100 - x_original
        # y_new = 100 - y_original
        x_coords = 100 - df['x']
        y_coords = 100 - df['y']

        print(f"--- Plotting {len(x_coords)} data points with INVERTED X and Y axes ---")

        # Create a plot figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.set_facecolor('#538d31')
        ax.scatter(x_coords, y_coords, color='cyan', alpha=0.6, s=100) # Using a different color
        
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        ax.set_title("Raw Heatmap Data Plot (Away Team - Top-Right Origin)")
        ax.set_xlabel("X-Axis (0 = Own Goal)")
        ax.set_ylabel("Y-Axis (0 = Bottom Sideline)")
        
        plt.savefig(output_image_path)
        print(f"✅ Away team heatmap plot saved successfully to: {output_image_path}")

    except FileNotFoundError:
        print(f"❌ ERROR: JSON file not found at {json_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # 1. Save your away team player's JSON data to a new file, e.g., 'away_player_heatmap.json'
    # 2. Update the json_path below to point to that new file.
    plot_heatmap_from_json(
        json_path='./data/raw/test_heatmap.json', # <-- Make sure this file exists with your away player's data
        output_image_path='./heatmap_plot_away.png'
    )