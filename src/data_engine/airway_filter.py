import csv
import sys

# --- Configuration ---
# Input CSV file containing all airways
# Expected header: airway_id,airway_name,airway_type,route_type,airway_fragment_no,sequence_no,from_waypoint_id,to_waypoint_id,direction,minimum_altitude,maximum_altitude,left_lonx,top_laty,right_lonx,bottom_laty,from_lonx,from_laty,to_lonx,to_laty
INPUT_CSV_FILE = '../../data/raw/ALL_airways.csv'

# Output CSV file for the filtered airways
OUTPUT_CSV_FILE = '../../data/processed/filtered_airways_LEMD-UUEE.csv'

# Bounding Box Coordinates MADRID–MOSCÚ (in Decimal Degrees)
# Top right – 56°19'59.3"N 38°03'31.3"E
# Top left  – 56°19'59.3"N  4°02'04.3"W
# Bot right – 40°06'42.7"N 38°03'31.3"E
# Bot left  – 40°06'42.7"N  4°02'04.3"W
MAX_LAT  = 56.333140
MIN_LAT  = 40.111860
MAX_LON  = 38.058696
MIN_LON  = -4.034539


# Column indices for coordinates in the airways CSV
FROM_LON_COL = 15  # from_lonx
FROM_LAT_COL = 16  # from_laty
TO_LON_COL = 17    # to_lonx
TO_LAT_COL = 18    # to_laty
# --- End of Configuration ---

def is_point_in_bbox(lon, lat):
    """Check if a point is within the bounding box."""
    return (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON)

def filter_airways_by_bbox():
    """
    Reads airways from an input CSV, filters them based on a
    geographical bounding box, and writes the result to a new CSV file.
    An airway is included if both its from and to waypoints are within the bounding box.
    """
    print(f"Reading airways from '{INPUT_CSV_FILE}'...")
    
    try:
        with open(INPUT_CSV_FILE, mode='r', newline='', encoding='utf-8') as infile, \
             open(OUTPUT_CSV_FILE, mode='w', newline='', encoding='utf-8') as outfile:

            # Try comma delimiter first, then tab
            reader = csv.reader(infile, delimiter=',')
            writer = csv.writer(outfile, delimiter=',')

            # Read and write the header row to the output file
            try:
                header = next(reader)
                print(f"Header: {header}")
                print(f"Number of columns: {len(header)}")
                writer.writerow(header)
            except StopIteration:
                print("Error: Input CSV file is empty.")
                return

            airways_in_box = 0
            total_airways = 0
            
            for row in reader:
                total_airways += 1
                try:
                    # Debug: print first few rows to check format
                    if total_airways <= 3:
                        print(f"Row {total_airways}: {row} (length: {len(row)})")
                    
                    # Extract coordinates from both waypoints
                    from_lon = float(row[FROM_LON_COL])
                    from_lat = float(row[FROM_LAT_COL])
                    to_lon = float(row[TO_LON_COL])
                    to_lat = float(row[TO_LAT_COL])

                    # Debug: print coordinates for first few rows
                    if total_airways <= 3:
                        print(f"  Coordinates: from ({from_lon}, {from_lat}) to ({to_lon}, {to_lat})")
                        print(f"  In bbox: from={is_point_in_bbox(from_lon, from_lat)}, to={is_point_in_bbox(to_lon, to_lat)}")

                    # Check if both waypoints are within the bounding box
                    if (is_point_in_bbox(from_lon, from_lat) and 
                        is_point_in_bbox(to_lon, to_lat)):
                        writer.writerow(row)
                        airways_in_box += 1
                        
                except (ValueError, IndexError) as e:
                    print(f"Skipping row {total_airways + 1} due to a data error: {e}. Row: {row}", file=sys.stderr)

        print("\nFiltering complete.")
        print(f"Total airways processed: {total_airways}")
        print(f"Airways found within bounding box: {airways_in_box}")
        print(f"Filtered data saved to '{OUTPUT_CSV_FILE}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{INPUT_CSV_FILE}'", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    filter_airways_by_bbox()