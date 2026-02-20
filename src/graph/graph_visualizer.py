import networkx as nx
import folium
from tqdm import tqdm
import webbrowser
import os
import ast

# --- Configuration ---
INPUT_GRAPH_FILE = '../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml'
OUTPUT_MAP_FILE = '../../outputs/graphs/graph_map_LEMD-UUEE.html'

def destringizer(s):
    """Safely convert a string representation of a Python literal back to the literal."""
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s

def visualize_graph_on_map(graph_file, output_file):
    """
    Loads a graph from a GML file and visualizes it on an interactive Folium map.
    """
    print(f"Loading graph from {graph_file}...")
    try:
        G = nx.read_gml(graph_file, label='id', destringizer=destringizer)
    except FileNotFoundError:
        print(f"Error: Graph file not found at {graph_file}")
        return

    if G.number_of_nodes() == 0:
        print("Graph is empty. Cannot generate map.")
        return

    # --- DEBUGGING STEP ---
    # Check the attributes of the first node to ensure they loaded correctly.
    if G.number_of_nodes() > 0:
        first_node = list(G.nodes())[0]
        node_data = G.nodes[first_node]
        print("\n--- Debugging Info ---")
        print(f"Data for first node ({first_node}): {node_data}")
        if 'poslong' in node_data and 'poslat' in node_data:
            poslong_attr = node_data['poslong']
            poslat_attr = node_data['poslat']
            print(f"Type of 'poslong' attribute: {type(poslong_attr)}")
            print(f"Type of 'poslat' attribute: {type(poslat_attr)}")
            print(">>> Position attributes found successfully.")
        else:
            print("First node does not have 'poslong' and/or 'poslat' attributes.")
        print("----------------------\n")
    # --- END DEBUGGING STEP ---

    print("Calculating map center...")
    lats = [data['poslat'] for _, data in G.nodes(data=True) if 'poslat' in data]
    lons = [data['poslong'] for _, data in G.nodes(data=True) if 'poslong' in data]
    
    if not lats or not lons:
        print("No valid node positions found in graph. Cannot generate map.")
        return
        
    map_center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=map_center, zoom_start=5, tiles='CartoDB positron')

    airway_edges_group = folium.FeatureGroup(name='Airway Edges (Blue)', show=True).add_to(m)
    proximity_edges_group = folium.FeatureGroup(name='Proximity Edges (Gray)', show=False).add_to(m)
    nodes_group = folium.FeatureGroup(name='Waypoints (Red)', show=True).add_to(m)

    print("Adding edges to the map...")
    for u, v, data in tqdm(G.edges(data=True), total=G.number_of_edges()):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        
        if 'poslong' in u_data and 'poslat' in u_data and 'poslong' in v_data and 'poslat' in v_data:
            loc_u = (u_data['poslat'], u_data['poslong'])
            loc_v = (v_data['poslat'], v_data['poslong'])
            edge_type = data.get('type', 'unknown')
            
            if edge_type == 'airway':
                folium.PolyLine([loc_u, loc_v], color='blue', weight=1.5, opacity=0.8).add_to(airway_edges_group)
            else:
                folium.PolyLine([loc_u, loc_v], color='gray', weight=1, opacity=0.6).add_to(proximity_edges_group)

    print("Adding nodes to the map...")
    for node, data in tqdm(G.nodes(data=True), total=G.number_of_nodes()):
        if 'poslong' in data and 'poslat' in data:
            ident = data.get('ident', 'N/A')
            loc = (data['poslat'], data['poslong'])
            popup_html = f"<b>ID:</b> {node}<br><b>Ident:</b> {ident}"
            folium.CircleMarker(
                location=loc, radius=2, popup=popup_html, color='red',
                fill=True, fill_color='darkred', fill_opacity=0.7
            ).add_to(nodes_group)

    folium.LayerControl().add_to(m)
    print(f"Saving map to {output_file}...")
    m.save(output_file)
    print("Map saved successfully.")
    return output_file

def main():
    """Main function to generate and open the map."""
    print("--- Starting Map Generation ---")
    map_file = visualize_graph_on_map(INPUT_GRAPH_FILE, OUTPUT_MAP_FILE)
    
    if map_file:
        full_path = os.path.abspath(map_file)
        print(f"Opening {full_path} in your web browser...")
        webbrowser.open(f'file://{full_path}')
        
    print("\n--- Process Finished ---")

if __name__ == "__main__":
    main()
