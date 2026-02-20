#!/usr/bin/env python3
"""
Flight Path Visualization Tool

This script creates an interactive visualization of flight paths from a CSV file.

Usage:
    python positioning_visual.py [max_flights]

    [max_flights] (optional): Maximum number of unique flights to process.
"""
import os
import sys

import pandas as pd
import folium
from folium import LayerControl
from tqdm import tqdm

import matplotlib.cm as cm
import matplotlib.colors as mcolors

# --- Configuration ---
INPUT_CSV_PATH = '../../../data/processed/filtered_flights_LEMD-UUEE.csv'
REQUIRED_COLUMNS = ['ID', 'Flight Level', 'Latitude', 'Longitude', 'Timestamp']


def dms_to_dd(dms):
    """Converts DMS coordinate string (e.g., "40 55 44N") to decimal degrees."""
    try:
        return float(dms)
    except (ValueError, TypeError):
        try:
            dms = str(dms).strip()
            parts = dms[:-1].strip().split()
            if len(parts) != 3:
                return None

            dd = float(parts[0]) + float(parts[1]) / 60 + float(parts[2]) / 3600
            if dms[-1].upper() in ['S', 'W']:
                dd *= -1
            return dd
        except (ValueError, IndexError):
            return None


def build_flight_color_map(flight_ids, cmap_name='hsv'):
    """
    Assign a unique color (HEX) to each flight_id using a colormap.
    cmap_name options: 'hsv' (/ matlab-ish)
    """
    flight_ids = list(flight_ids)
    n = len(flight_ids)
    if n == 0:
        return {}

    cmap = cm.get_cmap(cmap_name, n)  # discrete colormap with n distinct colors
    color_map = {}
    for i, fid in enumerate(flight_ids):
        rgba = cmap(i)  # (r,g,b,a) in [0,1]
        color_map[fid] = mcolors.to_hex(rgba, keep_alpha=False)  # '#RRGGBB'
    return color_map


def create_flight_visualization(csv_path, output_html_path, max_flights=None, cmap_name='hsv'):
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

    # Drop rows without valid coordinates/time (avoid folium crashing / weird lines)
    df = df.dropna(subset=['ID', 'Time Over', 'Latitude', 'Longitude'])

    if df.empty:
        print("No valid rows after cleaning (missing ID/Time/Lat/Lon).")
        return

    if max_flights and max_flights > 0:
        flight_counts = df['ID'].value_counts()
        selected_ids = flight_counts.head(max_flights).index.tolist()
        print(f"Selected flights with most data points: {selected_ids}")
        df = df[df['ID'].isin(selected_ids)]
        print(f"Processing {len(selected_ids)} flights (max_flights={max_flights}).")

    # Determine final flight IDs (sorted for stable color assignment)
    flight_ids = sorted(df['ID'].unique().tolist())
    flight_color = build_flight_color_map(flight_ids, cmap_name=cmap_name)

    # Create map centered on the data
    flight_map = folium.Map(
        location=[df['Latitude'].mean(), df['Longitude'].mean()],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    # Group data by flight ID and draw paths
    for flight_id, group in tqdm(df.groupby('ID'), desc="Processing flights"):
        group = group.sort_values(by='Time Over')
        flight_layer = folium.FeatureGroup(name=f"Flight {flight_id}")

        color = flight_color.get(flight_id, '#FF0000')  # fallback red
        avg_fl = group['Flight Level'].mean()
        popup_fl_info = f"Avg. FL: {avg_fl:.0f}" if pd.notna(avg_fl) else "Avg. FL: N/A"

        if len(group) >= 2:
            coords = group[['Latitude', 'Longitude']].values.tolist()
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=2.5,
                opacity=0.85,
                popup=f"Flight ID: {flight_id}<br>{popup_fl_info}"
            ).add_to(flight_layer)
        else:
            row = group.iloc[0]
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=5,
                color=color,
                fill=True,
                fillOpacity=0.85,
                popup=f"Flight ID: {flight_id}<br>FL: {row['Flight Level']}"
            ).add_to(flight_layer)

        flight_layer.add_to(flight_map)

    LayerControl().add_to(flight_map)
    flight_map.save(output_html_path)
    print(f"Visualization with {df['ID'].nunique()} flights saved to {output_html_path}")
    print(f"Colormap used: {cmap_name}")


if __name__ == '__main__':
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
        sys.exit(1)

    max_flights_arg = None
    if len(sys.argv) > 1:
        try:
            max_flights_arg = int(sys.argv[1])
            if max_flights_arg <= 0:
                raise ValueError
        except ValueError:
            print("Error: max_flights argument must be a positive integer.")
            sys.exit(1)

    # Create output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "real_filtered_trajectories")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(INPUT_CSV_PATH))[0]
    output_path = os.path.join(output_dir, f"flight_paths_{base_name}.html")

    print(f"Reading from: {INPUT_CSV_PATH}")

    # Choose colormap: 'hsv' (hue wheel like Matlab) or 'hot' (heatwave vibe)
    create_flight_visualization(
        INPUT_CSV_PATH,
        output_path,
        max_flights=max_flights_arg,
        cmap_name='hsv'
    )