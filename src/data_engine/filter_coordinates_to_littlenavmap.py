import numpy as np
import tqdm as tqdm
import csv

# Esta configuracion se puede ajustar a los datos que se quieran utilizar
# en este caso utilizamos los filed points (puntos esperados) de los vuelos, con fecha diciembre de 2019
# que se encuentran en el archivo Flight_Points_Filed_20191201_20191231.csv

flights_file = '../../data/raw/201912/Flight_Points_Filed_20191201_20191231.csv'
output_file = '../../data/processed/coordinates_filed_flights.csv'

def save_coordinates_to_csv(coordinates, filename):
    """
    Saves the list of coordinates to a CSV file.
    Adds a last column with lat and lon coordinates (no spaces, all together).
    Adds a column with flight level in M000FXXX format.
    Adds a column with timestamp from the original CSV.
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Sequence Number', 'Flight Level', 'Latitude', 'Longitude', 'LatLon', 'Flight Level Format', 'Timestamp'])
        for row in tqdm.tqdm(coordinates):
            if row[1] == 0:
                continue
            lat_str = row[3].replace(' ', '')
            lon_str = row[4].replace(' ', '')
            latlon = f"{lat_str}{lon_str}"
            
            # Format flight level as M000FXXX
            flight_level = row[2]
            flight_level_format = f"M000F{flight_level:03d}" if flight_level != 0 else ""
            
            timestamp = row[5] if len(row) > 5 else ""
            
            writer.writerow(list(row[:5]) + [latlon, flight_level_format, timestamp])


def decimal_to_navmap(coord, is_lat=True):
    """
    Converts decimal degrees to 'XX XX XXN' or 'XXX XX XXW' format.
    """
    direction = ''
    if is_lat:
        direction = 'N' if coord >= 0 else 'S'
    else:
        direction = 'E' if coord >= 0 else 'W'
    coord = abs(coord)
    degrees = int(coord)
    minutes_float = (coord - degrees) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)
    if is_lat:
        return f"{degrees:02d} {minutes:02d} {seconds:02d}{direction}"
    else:
        return f"{degrees:03d} {minutes:02d} {seconds:02d}{direction}"


def coordinates_to_littlenavmap(coordinates):
    """
    Converts a list of coordinates (id, sequence_number, flight_level, latitude, longitude, timestamp)
    to the format used by Little Navmap.
    """
    coordinates_after = []
    for entry in tqdm.tqdm(coordinates):
        id, sequence_number, flight_level, lat, lon, timestamp = entry
        if lat is None or lon is None:
            continue
        lat_str = decimal_to_navmap(lat, is_lat=True)
        lon_str = decimal_to_navmap(lon, is_lat=False)
        coordinates_after.append((id, sequence_number, flight_level, lat_str, lon_str, timestamp))
    return coordinates_after


def coordinates_extraction():
    """
    Extracts coordinates from a file and returns them as a list of tuples.
    The file should contain lines with latitude and longitude separated by a comma.
    File format:
    ECTRL ID	Sequence Number	Time Over	Flight Level	Latitude	Longitude
       0               1            2            3             4            5
    """

    coordinates_before = []
    not_valid_lines = 0
    with open(flights_file, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            try:
                parts = line.strip('').split(',')
                parts = [p.replace('"', '') for p in parts]
                id = int(parts[0])  # ECTRL ID
                sequence_number = int(parts[1])  # Sequence Number
                timestamp = parts[2] # Time Over
                flight_level = int(parts[3]) 
                lat = float(parts[4])
                lon = float(parts[5])
                coordinates_before.append((id, sequence_number, flight_level, lat, lon, timestamp))
                #print(f"Extracted coordinates: Flight Level {flight_level}, Latitude {lat}, Longitude {lon}")
            except Exception as e:
                #print(f"Error processing line: {line.strip()} with exception {e}")
                not_valid_lines += 1
                parts = line.strip('').split(',')
                parts = [p.replace('"', '') for p in parts]
                id = int(parts[0])  # ECTRL ID
                sequence_number = int(parts[1])  # Sequence Number
                timestamp = parts[2] # Time Over
                flight_level = int(parts[3]) 
                lat, lon = None, None
                coordinates_before.append((id, sequence_number, flight_level, lat, lon, timestamp))
        removed = 0
        for coordinate in tqdm.tqdm(coordinates_before):
            if coordinate[3] is None or coordinate[4] is None:
                incomplete_id = coordinate[0]
                for coord in coordinates_before:
                    if coord[0] == incomplete_id:
                        coordinates_before.remove(coord)
                        removed += 1
        print(f"Removed {removed} incomplete coordinates.")

    return coordinates_before
    # Output:
    # (id, sequence_number, flight_level, latitude, longitude, timestamp)


def main():
    coordinates_before = coordinates_extraction()
    print(f"Extracted {len(coordinates_before)} coordinates.")
    
    coordinates_after = coordinates_to_littlenavmap(coordinates_before)
    print(f"Transformed {len(coordinates_after)} coordinates to Little Navmap format.")

    save_coordinates_to_csv(coordinates_after, output_file)
    print(f"Saved transformed coordinates to {output_file}")

if __name__ == "__main__":
    main()