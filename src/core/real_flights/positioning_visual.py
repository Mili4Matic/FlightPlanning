#!/usr/bin/env python3
"""
Flight Path Visualization Tool

This script creates an interactive visualization of flight paths from a CSV file.

Usage:
    python positioning_visual.py [max_flights]
    
    [max_flights] (optional): Maximum number of unique flights to process.
"""
import pandas as pd
import folium
from folium import LayerControl
import os
import sys
from tqdm import tqdm

# --- Configuration ---
INPUT_CSV_PATH = '../../data/processed/filtered_flights_LEMD-UUEE.csv'
REQUIRED_COLUMNS = ['ID', 'Flight Level', 'Latitude', 'Longitude', 'Timestamp']

def dms_to_dd(dms):
    """Converts DMS coordinate string (e.g., "40 55 44N") to decimal degrees."""
    try:
        return float(dms)
    except (ValueError, TypeError):
        try:
            dms = str(dms).strip()
            parts = dms[:-1].strip().split()
            if len(parts) != 3: return None
            
            dd = float(parts[0]) + float(parts[1])/60 + float(parts[2])/3600
            if dms[-1].upper() in ['S', 'W']:
                dd *= -1
            return dd
        except (ValueError, IndexError):
            return None

def get_flight_level_color(fl):
    """Returns a color based on the flight level."""
    if pd.isna(fl): return '#808080'  # Gray
    if fl < 100: return '#FF0000'  # Red
    if fl < 200: return '#FF4500'  # Orange-red
    if fl < 300: return '#FFA500'  # Orange
    if fl < 400: return '#FFFF00'  # Yellow
    if fl < 500: return '#00FF00'  # Green
    return '#0000FF'  # Blue

def create_flight_visualization(csv_path, output_html_path, max_flights=None):
    try:
        df = pd.read_csv(csv_path, usecols=lambda c: c in REQUIRED_COLUMNS, on_bad_lines='warn')
    except (FileNotFoundError, ValueError) as e:
        print(f"Error reading CSV file: {e}")
        return

    if df.empty:
        print("CSV file is empty or required columns are missing.")
        return

    # Data cleaning and preparation
    df['Time Over'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Latitude'] = df['Latitude'].apply(dms_to_dd)
    df['Longitude'] = df['Longitude'].apply(dms_to_dd)
    df['Flight Level'] = pd.to_numeric(df['Flight Level'], errors='coerce')


    if max_flights and max_flights > 0:
        # Get flight IDs sorted by number of data points (descending)
        flight_counts = df['ID'].value_counts()
        selected_ids = flight_counts.head(max_flights).index.tolist()
        print(f"Selected flights with most data points: {selected_ids}")
        df = df[df['ID'].isin(selected_ids)]
        print(f"Processing {len(selected_ids)} flights (max_flights={max_flights}).")

    # Create map centered on the data
    flight_map = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=5, tiles="CartoDB positron")

    # Group data by flight ID and draw paths
    for flight_id, group in tqdm(df.groupby('ID'), desc="Processing flights"):
        group = group.sort_values(by='Time Over')
        flight_layer = folium.FeatureGroup(name=f"Flight {flight_id}")
        
        avg_fl = group['Flight Level'].mean()
        color = get_flight_level_color(avg_fl)
        popup_fl_info = f"Avg. FL: {avg_fl:.0f}" if pd.notna(avg_fl) else "Avg. FL: N/A"

        if len(group) >= 2:
            coords = group[['Latitude', 'Longitude']].values.tolist()
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=2.5,
                opacity=0.8,
                popup=f"Flight ID: {flight_id}<br>{popup_fl_info}"
            ).add_to(flight_layer)
        elif len(group) == 1:
            row = group.iloc[0]
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=5,
                color=color,
                fill=True,
                fillOpacity=0.8,
                popup=f"Flight ID: {flight_id}<br>FL: {row['Flight Level']}"
            ).add_to(flight_layer)
        
        flight_layer.add_to(flight_map)

    LayerControl().add_to(flight_map)
    flight_map.save(output_html_path)
    print(f"Visualization with {df['ID'].nunique()} flights saved to {output_html_path}")

if __name__ == '__main__':
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
        sys.exit(1)

    max_flights_arg = None
    if len(sys.argv) > 1:
        try:
            max_flights_arg = int(sys.argv[1])
            if max_flights_arg <= 0: raise ValueError
        except ValueError:
            print("Error: max_flights argument must be a positive integer.")
            sys.exit(1)

    # Create output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "trajectories")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(INPUT_CSV_PATH))[0]
    output_path = os.path.join(output_dir, f"flight_paths_{base_name}.html")

    print(f"Reading from: {INPUT_CSV_PATH}")
    create_flight_visualization(INPUT_CSV_PATH, output_path, max_flights=max_flights_arg)
