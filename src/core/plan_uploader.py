import subprocess

def run_flight_plan():
    """
    Reads coordinates from a file, constructs a command,
    and executes it in the terminal.
    """
    coordinates_file = "../../outputs/trajectories/path_coordinates.txt"
    performance_file = "../../aircraft_performance/a320.lnmperf"
    
    try:
        with open(coordinates_file, 'r') as f:
            # Read and strip any leading/trailing whitespace
            coordinates = f.read().strip()

        if not coordinates:
            print("Error: The coordinates file is empty.")
            return

        # Construct the full command
        command = f'littlenavmap -d "{coordinates}" -a {performance_file}'

        # Execute the command
        subprocess.run(command, shell=True, check=True)
        print("\nPlan Uploaded successfully.")

    except FileNotFoundError:
        print(f"Error: The file '{coordinates_file}' was not found.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_flight_plan()