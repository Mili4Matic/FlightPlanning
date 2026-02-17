import csv
import sys

# --- Configuration ---
# Input CSV file containing all waypoints
# Expected header: waypoint_id,file_id,nav_id,ident,name,region,airport_id,airport_ident,artificial,type,arinc_type,num_victor_airway,num_jet_airway,mag_var,lonx,laty
INPUT_CSV_FILE = '../../data/raw/waypoints.csv'
# Output CSV file for the filtered waypoints
OUTPUT_CSV_FILE = '../../data/processed/filtered_waypoints_LEMD-UUEE.csv'

# Bounding Box Coordinates MADRID–MOSCÚ (in Decimal Degrees)
# Top right – 56°19'59.3"N 38°03'31.3"E
# Top left  – 56°19'59.3"N  4°02'04.3"W
# Bot right – 40°06'42.7"N 38°03'31.3"E
# Bot left  – 40°06'42.7"N  4°02'04.3"W
MAX_LAT  = 56.333140
MIN_LAT  = 40.111860
MAX_LON  = 38.058696
MIN_LON  = -4.034539


# Column indices for longitude and latitude in the input CSV
# Based on the header provided, 'lonx' is the 15th column (index 14)
# and 'laty' is the 16th column (index 15).
LON_COL_INDEX = 14
LAT_COL_INDEX = 15
# --- End of Configuration ---

def filter_waypoints_by_bbox():
    """
    Reads waypoints from an input CSV, filters them based on a
    geographical bounding box, and writes the result to a new CSV file
    with alternated coordinate columns.
    """
    print(f"Reading waypoints from '{INPUT_CSV_FILE}'...")
    
    try:
        with open(INPUT_CSV_FILE, mode='r', newline='', encoding='utf-8') as infile, \
             open(OUTPUT_CSV_FILE, mode='w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Read and write the header row to the output file with swapped coordinate headers
            try:
                header = next(reader)
                # Swap the coordinate column headers
                header[LON_COL_INDEX], header[LAT_COL_INDEX] = header[LAT_COL_INDEX], header[LON_COL_INDEX]
                writer.writerow(header)
            except StopIteration:
                print("Error: Input CSV file is empty.")
                return

            waypoints_in_box = 0
            total_waypoints = 0
            
            for row in reader:
                total_waypoints += 1
                try:
                    # Extract longitude and latitude from the correct columns
                    lon = float(row[LON_COL_INDEX])
                    lat = float(row[LAT_COL_INDEX])

                    # Check if the waypoint is within the bounding box
                    if (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON):
                        # Swap the coordinate values in the output row
                        row[LON_COL_INDEX], row[LAT_COL_INDEX] = row[LAT_COL_INDEX], row[LON_COL_INDEX]
                        writer.writerow(row)
                        waypoints_in_box += 1
                except (ValueError, IndexError) as e:
                    print(f"Skipping row {total_waypoints + 1} due to a data error: {e}. Row: {row}", file=sys.stderr)

        print("\nFiltering complete.")
        print(f"Total waypoints processed: {total_waypoints}")
        print(f"Waypoints found within bounding box: {waypoints_in_box}")
        print(f"Filtered data saved to '{OUTPUT_CSV_FILE}' with alternated coordinates")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{INPUT_CSV_FILE}'", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    filter_waypoints_by_bbox()