import networkx as nx
import math

# Configuration variables
OUTPUT_FILE = "../../outputs/trajectories/path_coordinates_astar.txt"
START_NODE = "66968"
END_NODE = "40867"

# Load the graph from the GML file
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

def haversine_distance(u, v):
    """
    Heuristic function for A* using Haversine distance.
    Estimates the great-circle distance between two nodes (points on Earth).
    """
    node_u_data = graph.nodes[u]
    node_v_data = graph.nodes[v]
    
    lon1, lat1 = node_u_data.get('poslong', 0), node_u_data.get('poslat', 0)
    lon2, lat2 = node_v_data.get('poslong', 0), node_v_data.get('poslat', 0)
    
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in the same units as the graph weights is needed for an
    # admissible and consistent heuristic. Assuming weights are in nautical miles.
    # Radius of Earth in nautical miles is approx 3440.065
    r = 3440.065
    return c * r

def astar_shortest_path(graph, start_node=START_NODE, end_node=END_NODE):
    """
    Find shortest path using A* algorithm
    """
    try:
        # Use NetworkX's built-in A* implementation with weights and a heuristic
        path = nx.astar_path(graph, source=start_node, target=end_node, heuristic=haversine_distance, weight='weight')
        # Calculate path length from the path found to avoid a second search
        distance = sum(graph[u][v]['weight'] for u, v in zip(path, path[1:]))
        
        return path, distance
    
    except nx.NetworkXNoPath:
        return None, float('inf')
    except nx.NodeNotFound as e:
        print(f"Node not found: {e}")
        return None, None

def write_coordinates_to_file(graph, path, filename=OUTPUT_FILE):
    """
    Write the coordinates of nodes in the path to a file
    """
    with open(filename, 'w') as f:
        for node in path:
            node_data = graph.nodes[node]
            lat = node_data.get('poslat', 0)
            lon = node_data.get('poslong', 0)
            
            formatted_lat = format_coordinate(lat, is_latitude=True)
            formatted_lon = format_coordinate(lon, is_latitude=False)
            
            f.write(f"{formatted_lat}{formatted_lon}\n")

def main():
    """
    Main function to execute the A* algorithm on the graph.
    """
    path, distance = astar_shortest_path(graph)

    if path is not None:
        print(f"Shortest path from '{START_NODE}' to '{END_NODE}' using A*: {path}")
        print(f"Total distance: {distance} units")
        
        # Write coordinates to file
        write_coordinates_to_file(graph, path)
        print(f"Coordinates written to '{OUTPUT_FILE}'")
    else:
        print("No path found or an error occurred.")

if __name__ == "__main__":
    main()