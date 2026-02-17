import pandas as pd
from math import radians, cos, sin, asin, sqrt
import tqdm as tqdm
import os

# Usados como ejemplo, se pueden ajustar a los datos que se quieran utilizar
# LEMD (Aeropuerto Adolfo Suárez Madrid-Barajas)   = 40° 28' 20.45" N   3° 33' 39.34" W
# UUEE (Aeropuerto Internacional Moscú-Sheremétievo) = 55° 58' 22.0" N  37° 24' 53.0" E

# Coordinates configuration
# Departure: LEMD (Madrid)
DEPARTURE_LAT = 40.4723
DEPARTURE_LON = -3.5609
# Arrival: UUEE (Moscu)
ARRIVAL_LAT  = 55.972778
ARRIVAL_LON  = 37.414722
TOLERANCE_KM = 20        # Tolerance in kilometers

# File paths configuration
INPUT_CSV = '../../data/raw/coordinates_actual_flights.csv'
OUTPUT_CSV = '../../data/processed/filtered_flights_actual_LEMD-UUEE.csv'

def parse_coordinate(coord_str):
    """
    Parse coordinate string like "40 28 19N" or "003 33 38W" to decimal degrees
    """
    coord_str = coord_str.strip()
    
    # Extract direction (last character)
    direction = coord_str[-1]
    coord_numbers = coord_str[:-1].strip()
    
    # Split into degrees, minutes, seconds and handle leading zeros
    parts = coord_numbers.split()
    degrees = int(parts[0].lstrip('0') or '0')  # Handle leading zeros
    minutes = int(parts[1].lstrip('0') or '0')  # Handle leading zeros
    seconds = int(parts[2].lstrip('0') or '0')  # Handle leading zeros
    
    # Convert to decimal degrees
    decimal_degrees = degrees + minutes/60 + seconds/3600
    
    # Apply sign based on direction
    if direction in ['S', 'W']:
        decimal_degrees = -decimal_degrees
    
    return decimal_degrees

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert to float and then to radians 
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def filter_trajectories(input_csv, output_csv, departure_lat, departure_lon, 
                       arrival_lat, arrival_lon, tolerance_km=50):
    """
    Filter trajectories based on departure and arrival coordinates
    
    Parameters:
    - input_csv: path to input CSV file
    - output_csv: path to output CSV file
    - departure_lat, departure_lon: departure coordinates
    - arrival_lat, arrival_lon: arrival coordinates
    - tolerance_km: tolerance in kilometers for departure/arrival matching
    """
    
    # Display search coordinates
    print("=== TRAJECTORY FILTERING SEARCH PARAMETERS ===")
    print(f"Departure coordinates: {departure_lat:.6f}°, {departure_lon:.6f}°")
    print(f"Arrival coordinates: {arrival_lat:.6f}°, {arrival_lon:.6f}°")
    print(f"Tolerance: {tolerance_km} km")
    print("=" * 50)
    
    # Read the CSV file
    df = pd.read_csv(input_csv)
    print(f"Total flights in CSV: {df['ID'].nunique()}")
    # Convert coordinate strings to decimal degrees
    df['Latitude_decimal'] = df['Latitude'].apply(parse_coordinate)
    df['Longitude_decimal'] = df['Longitude'].apply(parse_coordinate)
    
    # Sort by ID and Timestamp to ensure proper sequence
    df = df.sort_values(['ID', 'Timestamp'])
    
    # Group by flight ID
    flight_groups = df.groupby('ID')
    
    filtered_flights = []
    
    for _, flight_data in tqdm.tqdm(flight_groups):
        # Get first and last points of the trajectory
        first_point = flight_data.iloc[0]
        last_point = flight_data.iloc[-1]
        
        # Calculate distances to departure and arrival points
        departure_distance = haversine(
            first_point['Longitude_decimal'], first_point['Latitude_decimal'],
            departure_lon, departure_lat
        )
        
        arrival_distance = haversine(
            last_point['Longitude_decimal'], last_point['Latitude_decimal'],
            arrival_lon, arrival_lat
        )
        
        # Check if flight matches criteria within tolerance
        if (departure_distance <= tolerance_km and 
            arrival_distance <= tolerance_km):
            filtered_flights.append(flight_data)
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Combine all filtered flights
    if filtered_flights:
        result_df = pd.concat(filtered_flights, ignore_index=True)
        result_df.to_csv(output_csv, index=False)
        print(f"Filtered {len(filtered_flights)} flights saved to {output_csv}")
    else:
        print("No flights found matching the criteria")
        # Create empty CSV with same structure
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df.to_csv(output_csv, index=False)
        empty_df.to_csv(output_csv, index=False)

# Example usage
if __name__ == "__main__":
    # Filter trajectories using the variables defined at the top
    filter_trajectories(
        input_csv=INPUT_CSV,
        output_csv=OUTPUT_CSV,
        departure_lat=DEPARTURE_LAT,
        departure_lon=DEPARTURE_LON,
        arrival_lat=ARRIVAL_LAT,
        arrival_lon=ARRIVAL_LON,
        tolerance_km=TOLERANCE_KM
    )
