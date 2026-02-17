import networkx as nx
import tqdm
import sys
import argparse
# Configuration variables
OUTPUT_FILE = "../../outputs/trajectories/path_coordinates_dijkstra.txt"
START_NODE = "67318"
END_NODE = "41203"
DEFAULT_ALTITUDE = 36000
DEPARTURE_TRANSITION_BASE = "LEMD/36L PINA2N N450A{}" # SID TRANS, altitude will be inserted
ARRIVAL_TRANSITION = "UUEE/SUSOR.I06L" # Standar Approach Transition, checkear tambien especificacion con documentacion LNM

graph = nx.read_gml('../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml')

def format_coordinate(coord, is_latitude=True):
    """
    Format coordinate to the specified format: XXXXXX[N/S] or XXXXXXX[E/W]
    """
    abs_coord = abs(coord)
    degrees = int(abs_coord)
    minutes = int((abs_coord - degrees) * 60)
    seconds = int(((abs_coord - degrees) * 60 - minutes) * 60)
    
    if is_latitude:
        direction = 'N' if coord >= 0 else 'S'
        return f"{degrees:02d}{minutes:02d}{seconds:02d}{direction}"
    else:
        direction = 'E' if coord >= 0 else 'W'
        return f"{degrees:03d}{minutes:02d}{seconds:02d}{direction}"

def dijkstra_shortest_path(graph, start_node=START_NODE, end_node=END_NODE):
    """
    Find shortest path using Dijkstra's algorithm
    """
    try:
        # Check if time-based weights ('w') exist, otherwise use distance weights ('weight')
        weight_attr = 'w' if any('w' in graph[u][v] for u, v in graph.edges()) else 'weight'
        print(f"Using weight attribute: '{weight_attr}'")
        
        # Use NetworkX's built-in Dijkstra implementation with weights
        path = nx.shortest_path(graph, source=start_node, target=end_node, weight=weight_attr)
        distance = nx.shortest_path_length(graph, source=start_node, target=end_node, weight=weight_attr)
        
        return path, distance
    
    except nx.NetworkXNoPath:
        return None, float('inf')
    except nx.NodeNotFound as e:
        print(f"Node not found: {e}")
        return None, None

def write_coordinates_to_file(graph, path, departure, arrival, filename=OUTPUT_FILE):
    """
    Write the departure, coordinates of nodes in the path, and arrival to a file
    """
    with open(filename, 'w') as f:
        if departure:
            f.write(f"{departure} ")

        for node in tqdm.tqdm(path):
            node_data = graph.nodes[node]
            lat = node_data.get('poslat', 0)
            lon = node_data.get('poslong', 0)
            
            formatted_lat = format_coordinate(lat, is_latitude=True)
            formatted_lon = format_coordinate(lon, is_latitude=False)
            
            f.write(f"{formatted_lat}{formatted_lon} ")

        if arrival:
            f.write(arrival)


def main():
    """
    Main function to execute the Dijkstra's algorithm on the graph.
    """
    parser = argparse.ArgumentParser(description='Find shortest path with specified cruise altitude')
    parser.add_argument('--altitude', type=int, default=DEFAULT_ALTITUDE, 
                       help=f'Cruise altitude (default: {DEFAULT_ALTITUDE})')
    parser.add_argument('path_nodes', nargs='*', 
                       help='Optional path nodes to override automatic shortest path calculation')
    
    args = parser.parse_args()
    altitude = args.altitude
    
    # Generate departure transition with specified altitude (convert feet to flight level format)
    flight_level = altitude // 100  # Convert feet to flight level (e.g., 34000 -> 340)
    departure_transition = DEPARTURE_TRANSITION_BASE.format(flight_level)
    
    if args.path_nodes:
        # Use provided path nodes
        path = args.path_nodes
        print(f"Using provided path: {path}")
        distance = "N/A (provided path)"
    else:
        # Calculate shortest path
        path, distance = dijkstra_shortest_path(graph)

    if path is not None:
        print(f"Path from '{START_NODE}' to '{END_NODE}': {path}")
        print(f"Total distance: {distance} units")
        print(f"Cruise altitude: {altitude} ft")
        
        # Write coordinates to file
        write_coordinates_to_file(graph, path, departure_transition, ARRIVAL_TRANSITION)
        print(f"Coordinates written to '{OUTPUT_FILE}'")
    else:
        print("No path found or an error occurred.")

if __name__ == "__main__":
    main()