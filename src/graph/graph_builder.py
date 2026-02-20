import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import great_circle
from tqdm import tqdm
import numpy as np
from sklearn.neighbors import NearestNeighbors

# Config
# Radius in kilometers to connect nearby waypoints
RADIUS = 5
# Minimum connections per node
MIN_CONNECTIONS = 25

# Input files
WAYPOINTS_INPUT_FILE = '../../data/processed/filtered_waypoints_LEMD-UUEE.csv'
AIRWAYS_INPUT_FILE = '../../data/processed/filtered_airways_LEMD-UUEE.csv'
# Output files
OUTPUT_GRAPH_FILE = '../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml'
OUTPUT_PLOT_FILE = '../../outputs/graphs/waypoints_graph_LEMD-UUEE.png'


def load_data(file_path):
    """Load data from a CSV file."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

def ensure_minimum_connectivity(G, min_connections=MIN_CONNECTIONS):
    """
    Ensure each node has at least min_connections connections using KNN approach.
    """
    print(f"Ensuring minimum connectivity of {min_connections} connections per node...")
    
    # Get all nodes with their positions
    nodes_list = list(G.nodes())
    positions = np.array([[G.nodes[node]['poslong'], G.nodes[node]['poslat']] for node in nodes_list])
    
    # Convert longitude/latitude to approximate distances for KNN
    # Note: This is an approximation, but sufficient for finding nearest neighbors
    positions_scaled = positions.copy()
    positions_scaled[:, 0] = positions[:, 0] * np.cos(np.radians(positions[:, 1]))  # Adjust longitude by latitude
    
    # Build KNN model
    knn = NearestNeighbors(n_neighbors=min(min_connections + 1, len(nodes_list)), metric='euclidean')
    knn.fit(positions_scaled)
    
    edges_added = 0
    
    for i, node in enumerate(tqdm(nodes_list)):
        current_degree = G.degree(node)
        
        if current_degree < min_connections:
            # Find nearest neighbors
            needed_connections = min_connections - current_degree
            # Get more neighbors than needed to account for existing connections
            n_neighbors = min(needed_connections + current_degree + 5, len(nodes_list))
            
            distances, indices = knn.kneighbors([positions_scaled[i]], n_neighbors=n_neighbors)
            
            connections_added = 0
            for j, neighbor_idx in enumerate(indices[0]):
                if neighbor_idx == i:  # Skip self
                    continue
                    
                neighbor_node = nodes_list[neighbor_idx]
                
                # Skip if edge already exists
                if G.has_edge(node, neighbor_node):
                    continue
                
                # Calculate actual distance using great circle
                lon1, lat1 = G.nodes[node]['poslong'], G.nodes[node]['poslat']
                lon2, lat2 = G.nodes[neighbor_node]['poslong'], G.nodes[neighbor_node]['poslat']
                distance = great_circle((lat1, lon1), (lat2, lon2)).kilometers
                
                # Add edge
                G.add_edge(node, neighbor_node, weight=distance, type='knn')
                edges_added += 1
                connections_added += 1
                
                if connections_added >= needed_connections:
                    break
    
    print(f"Added {edges_added} edges to ensure minimum connectivity")
    return G

def create_graph(waypoints_df, airways_df):
    """
    Create a graph from waypoints and airways.
    Nodes are waypoints. Edges are defined by airways and proximity.
    """
    G = nx.Graph()

    if waypoints_df is None:
        return G

    # Add nodes to the graph from the waypoints dataframe
    print("Adding waypoints as nodes...")
    for _, row in tqdm(waypoints_df.iterrows(), total=waypoints_df.shape[0]):
        G.add_node(row['waypoint_id'], poslong=row['lonx'], poslat=row['laty'], ident=row['ident'])

    # Add edges based on the airways file
    if airways_df is not None:
        print("Adding edges from airways...")
        for _, row in tqdm(airways_df.iterrows(), total=airways_df.shape[0]):
            from_wp = row['from_waypoint_id']
            to_wp = row['to_waypoint_id']
            # Ensure both waypoints exist in the graph before adding an edge
            if G.has_node(from_wp) and G.has_node(to_wp):
                lon1, lat1 = G.nodes[from_wp]['poslong'], G.nodes[from_wp]['poslat']
                lon2, lat2 = G.nodes[to_wp]['poslong'], G.nodes[to_wp]['poslat']
                distance = great_circle((lat1, lon1), (lat2, lon2)).kilometers
                G.add_edge(from_wp, to_wp, weight=distance, type='airway')

    # Add edges based on proximity (within RADIUS)
    print("Adding edges based on proximity...")
    # Create a list of nodes with their coordinates for efficient iteration
    nodes_with_coords = [(n, (d['poslong'], d['poslat'])) for n, d in G.nodes(data=True)]
    
    for i in tqdm(range(len(nodes_with_coords))):
        for j in range(i + 1, len(nodes_with_coords)):
            id1, pos1 = nodes_with_coords[i]
            id2, pos2 = nodes_with_coords[j]

            # Add edge only if it doesn't already exist from airways
            if not G.has_edge(id1, id2):
                distance = great_circle((pos1[1], pos1[0]), (pos2[1], pos2[0])).kilometers
                if distance <= RADIUS:
                    G.add_edge(id1, id2, weight=distance, type='proximity')
    
    # Ensure minimum connectivity using KNN approach
    G = ensure_minimum_connectivity(G)
    
    return G

def analyze_connectivity(G):
    """Analyze and print connectivity statistics."""
    degrees = dict(G.degree())
    degree_values = list(degrees.values())
    
    print("\n--- Connectivity Analysis ---")
    print(f"Average degree: {np.mean(degree_values):.2f}")
    print(f"Minimum degree: {np.min(degree_values)}")
    print(f"Maximum degree: {np.max(degree_values)}")
    print(f"Nodes with degree < {MIN_CONNECTIONS}: {sum(1 for d in degree_values if d < MIN_CONNECTIONS)}")
    
    # Count edges by type
    edge_types = {}
    for _, _, data in G.edges(data=True):
        edge_type = data.get('type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    print("\n--- Edge Types ---")
    for edge_type, count in edge_types.items():
        print(f"{edge_type.capitalize()}: {count}")

def save_graph(G, output_file):
    """Save the graph to a GML file."""
    print(f"Saving graph to {output_file}...")
    nx.write_gml(G, output_file)

def plot_graph(G, output_plot_file):
    """Plot the graph and save the figure."""
    print(f"Generating and saving graph plot to {output_plot_file}...")
    pos = {node: (data['poslong'], data['poslat']) for node, data in G.nodes(data=True)}
    
    plt.figure(figsize=(20, 15))
    
    # Draw the graph with smaller nodes and no labels for clarity
    nx.draw(G, pos, with_labels=False, node_size=5, width=0.5, edge_color='gray')
    
    plt.title('Airspace Graph (Waypoints and Airways)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(output_plot_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to run the graph building process."""
    print("Constructing Graph")
    
    # Load data
    waypoints = load_data(WAYPOINTS_INPUT_FILE)
    airways = load_data(AIRWAYS_INPUT_FILE)

    if waypoints is None:
        print("ERROR: Could not load waypoints.")
        return

    # Create graph
    G = create_graph(waypoints, airways)
    
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    
    # Analyze connectivity
    analyze_connectivity(G)
    
    if G.number_of_nodes() > 0:
        # Save graph to file
        save_graph(G, OUTPUT_GRAPH_FILE)

        # Plot graph
        plot_graph(G, OUTPUT_PLOT_FILE)
    else:
        print("Graph is empty. Nothing to save or plot.")

    print("\n Graph Built")

if __name__ == "__main__":
    main()