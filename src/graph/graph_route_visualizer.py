import networkx as nx
import folium
from tqdm import tqdm
import webbrowser
import os
import sys
import ast
import re
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# --- Configuration ---
INPUT_GRAPH_FILE = '../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml'
OUTPUT_MAP_FILE = '../../outputs/graphs/graph_route_map_LEMD-UUEE.html'
OUTPUT_PLOT_FILE = '../../outputs/graphs/graph_route_plot_LEMD-UUEE.png'
DEFAULT_ROUTE_FILE = '../../outputs/trajectories/path_coordinates.txt'

# Regex pattern for coordinate tokens: DDMMSS[N/S]DDDMMSS[E/W]
COORD_PATTERN = re.compile(r'^(\d{6}[NS])(\d{7}[EW])$')


def destringizer(s):
    """Safely convert a string representation of a Python literal back to the literal."""
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s


def parse_dms_token(token):
    """
    Parse a coordinate token like '405849N0023557W' into (lat_dd, lon_dd).
    Format: DDMMSS[N/S]DDDMMSS[E/W]
    Returns (lat, lon) in decimal degrees, or None if not a valid coordinate.
    """
    m = COORD_PATTERN.match(token)
    if not m:
        return None

    lat_str, lon_str = m.group(1), m.group(2)

    # Latitude: DDMMSS + direction
    lat_deg = int(lat_str[0:2])
    lat_min = int(lat_str[2:4])
    lat_sec = int(lat_str[4:6])
    lat_dir = lat_str[6]
    lat_dd = lat_deg + lat_min / 60 + lat_sec / 3600
    if lat_dir == 'S':
        lat_dd *= -1

    # Longitude: DDDMMSS + direction
    lon_deg = int(lon_str[0:3])
    lon_min = int(lon_str[3:5])
    lon_sec = int(lon_str[5:7])
    lon_dir = lon_str[7]
    lon_dd = lon_deg + lon_min / 60 + lon_sec / 3600
    if lon_dir == 'W':
        lon_dd *= -1

    return (lat_dd, lon_dd)


def load_route_coordinates(route_file):
    """
    Load route coordinates from a .txt file.
    Supports two formats:
      - Single line with departure/arrival tokens and coordinates (e.g. top_X_route_coordinates.txt)
      - One coordinate per line (e.g. path_coordinates_astar.txt)
    Returns a list of (lat, lon) tuples in decimal degrees.
    """
    with open(route_file, 'r') as f:
        content = f.read().strip()

    # Try single-line format first (space-separated tokens on one line)
    if '\n' not in content:
        tokens = content.split()
    else:
        tokens = content.splitlines()

    coords = []
    for token in tokens:
        token = token.strip()
        result = parse_dms_token(token)
        if result:
            coords.append(result)

    return coords


def visualize_graph_with_route(graph_file, route_file, output_file):
    """
    Loads a graph from a GML file, loads a route from a .txt file,
    and visualizes the full graph with the route highlighted on an interactive Folium map.
    """
    # --- Load Graph ---
    print(f"Loading graph from {graph_file}...")
    try:
        G = nx.read_gml(graph_file, label='id', destringizer=destringizer)
    except FileNotFoundError:
        print(f"Error: Graph file not found at {graph_file}")
        return

    if G.number_of_nodes() == 0:
        print("Graph is empty. Cannot generate map.")
        return

    # --- Load Route ---
    print(f"Loading route from {route_file}...")
    try:
        route_coords = load_route_coordinates(route_file)
    except FileNotFoundError:
        print(f"Error: Route file not found at {route_file}")
        return

    if not route_coords:
        print("No valid coordinates found in route file.")
        return

    print(f"Route loaded: {len(route_coords)} waypoints")

    # --- Calculate map center ---
    print("Calculating map center...")
    lats = [data['poslat'] for _, data in G.nodes(data=True) if 'poslat' in data]
    lons = [data['poslong'] for _, data in G.nodes(data=True) if 'poslong' in data]

    if not lats or not lons:
        print("No valid node positions found in graph. Cannot generate map.")
        return

    map_center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=map_center, zoom_start=5, tiles='CartoDB positron')

    # --- Feature Groups ---
    airway_edges_group = folium.FeatureGroup(name='Airway Edges (Blue)', show=True).add_to(m)
    proximity_edges_group = folium.FeatureGroup(name='Proximity Edges (Gray)', show=False).add_to(m)
    nodes_group = folium.FeatureGroup(name='Waypoints (Red)', show=True).add_to(m)
    route_group = folium.FeatureGroup(name='Route (Green)', show=True).add_to(m)

    # --- Draw Graph Edges ---
    print("Adding graph edges to the map...")
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

    # --- Draw Graph Nodes ---
    print("Adding graph nodes to the map...")
    for node, data in tqdm(G.nodes(data=True), total=G.number_of_nodes()):
        if 'poslong' in data and 'poslat' in data:
            ident = data.get('ident', 'N/A')
            loc = (data['poslat'], data['poslong'])
            popup_html = f"<b>ID:</b> {node}<br><b>Ident:</b> {ident}"
            folium.CircleMarker(
                location=loc, radius=1, popup=popup_html, color='red',
                fill=True, fill_color='darkred', fill_opacity=0.4
            ).add_to(nodes_group)

    # --- Draw Route ---
    print("Adding route to the map...")
    route_name = os.path.basename(route_file)

    # Route polyline
    folium.PolyLine(
        locations=route_coords,
        color='limegreen',
        weight=4,
        opacity=0.9,
        popup=f"Route: {route_name}"
    ).add_to(route_group)

    # Route waypoint markers
    for i, (lat, lon) in enumerate(route_coords):
        label = "START" if i == 0 else ("END" if i == len(route_coords) - 1 else str(i))
        color = 'green' if i == 0 else ('darkred' if i == len(route_coords) - 1 else 'orange')
        radius = 6 if i == 0 or i == len(route_coords) - 1 else 3

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=f"<b>Route WP {label}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}"
        ).add_to(route_group)

    # --- Finalize ---
    folium.LayerControl().add_to(m)
    print(f"Saving map to {output_file}...")
    m.save(output_file)
    print(f"Map saved successfully with route '{route_name}' highlighted.")
    return output_file


def plot_graph_with_route(graph_file, route_file, output_plot_file):
    """
    Generates a static PNG plot of the graph with the route highlighted,
    rendered on a cartopy geographic map (same style as graph_builder_alter).
    """
    print(f"Loading graph from {graph_file}...")
    try:
        G = nx.read_gml(graph_file, label='id', destringizer=destringizer)
    except FileNotFoundError:
        print(f"Error: Graph file not found at {graph_file}")
        return

    print(f"Loading route from {route_file}...")
    try:
        route_coords = load_route_coordinates(route_file)
    except FileNotFoundError:
        print(f"Error: Route file not found at {route_file}")
        return

    if not route_coords:
        print("No valid coordinates found in route file.")
        return

    pos = {node: (data['poslong'], data['poslat']) for node, data in G.nodes(data=True)}

    # Bounding box with padding
    lons = [coord[0] for coord in pos.values()]
    lats = [coord[1] for coord in pos.values()]
    lon_pad = (max(lons) - min(lons)) * 0.05 + 0.5
    lat_pad = (max(lats) - min(lats)) * 0.05 + 0.5

    fig = plt.figure(figsize=(20, 15))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([min(lons) - lon_pad, max(lons) + lon_pad,
                   min(lats) - lat_pad, max(lats) + lat_pad],
                  crs=ccrs.PlateCarree())

    # Map features
    ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
    ax.add_feature(cfeature.OCEAN, facecolor='#c6e2ff')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    ax.add_feature(cfeature.LAKES, facecolor='#c6e2ff', edgecolor='gray', linewidth=0.3)
    ax.add_feature(cfeature.RIVERS, edgecolor='#c6e2ff', linewidth=0.3)
    ax.gridlines(draw_labels=True, linewidth=0.3, color='gray', alpha=0.5, linestyle='--')

    # Draw graph edges
    print("Drawing graph edges...")
    for u, v, data in tqdm(G.edges(data=True), total=G.number_of_edges()):
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        ax.plot(x, y, color='gray', linewidth=0.3, alpha=0.4, transform=ccrs.PlateCarree())

    # Draw graph nodes
    node_lons = [pos[n][0] for n in G.nodes()]
    node_lats = [pos[n][1] for n in G.nodes()]
    ax.scatter(node_lons, node_lats, s=3, c='steelblue', alpha=0.5, zorder=5, transform=ccrs.PlateCarree())

    # Draw route
    print("Drawing route...")
    route_lats = [c[0] for c in route_coords]
    route_lons = [c[1] for c in route_coords]
    ax.plot(route_lons, route_lats, color='limegreen', linewidth=2.5, zorder=10, transform=ccrs.PlateCarree(), label='Route')
    ax.scatter(route_lons, route_lats, s=15, c='limegreen', edgecolors='darkgreen', linewidths=0.5, zorder=11, transform=ccrs.PlateCarree())

    # Start and end markers
    ax.scatter([route_lons[0]], [route_lats[0]], s=80, c='green', marker='^', edgecolors='black',
               linewidths=0.8, zorder=12, transform=ccrs.PlateCarree(), label='Start')
    ax.scatter([route_lons[-1]], [route_lats[-1]], s=80, c='red', marker='v', edgecolors='black',
               linewidths=0.8, zorder=12, transform=ccrs.PlateCarree(), label='End')

    route_name = os.path.basename(route_file)
    ax.set_title(f'Airspace Graph with Route: {route_name}', fontsize=14)
    ax.legend(loc='upper left', fontsize=10)

    print(f"Saving plot to {output_plot_file}...")
    plt.savefig(output_plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print("Plot saved successfully.")
    return output_plot_file


def main():
    """Main function to generate and open the map with a route overlay."""
    route_file = DEFAULT_ROUTE_FILE

    # Accept route file as command-line argument
    if len(sys.argv) > 1:
        route_file = sys.argv[1]

    if not os.path.exists(route_file):
        print(f"Error: Route file not found at {route_file}")
        sys.exit(1)

    print("--- Starting Route Visualization ---")
    print(f"Graph: {INPUT_GRAPH_FILE}")
    print(f"Route: {route_file}")

    map_file = visualize_graph_with_route(INPUT_GRAPH_FILE, route_file, OUTPUT_MAP_FILE)
    plot_file = plot_graph_with_route(INPUT_GRAPH_FILE, route_file, OUTPUT_PLOT_FILE)

    if map_file:
        full_path = os.path.abspath(map_file)
        print(f"Opening {full_path} in your web browser...")
        webbrowser.open(f'file://{full_path}')

    if plot_file:
        print(f"PNG plot saved at: {os.path.abspath(plot_file)}")

    print("\n--- Process Finished ---")


if __name__ == "__main__":
    main()
