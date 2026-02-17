# Needs: networkx >= 2.8, pandas (only for pretty stats)

import networkx as nx, json, subprocess, time, pathlib, sys, statistics, pandas as pd, shutil
from itertools import islice
from tqdm import tqdm

# Configuration variables
G_PATH      = pathlib.Path("../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml")
DIJKSTRA    = pathlib.Path("./dijkstra.py")              # writes path_coordinates.txt
PLAN_UPLOAD = pathlib.Path("../core/plan_uploader.py")
FLIGHT_INFO = pathlib.Path("../core/flight_info.py")
FLIGHT_JSON = pathlib.Path("../../outputs/trajectories/flight_data.json")

K           = 15      # how many shortest paths we test each round
ALPHA_GOOD  = -0.05   # weight delta for edges on good paths   (negative = reward)
ALPHA_BAD   =  0.05   # weight delta for edges on bad paths    (positive = penalty)
BEAM        = 4       # keep this many best routes
MAX_ROUNDS  = 6       # stop afterwards even if not perfect
STOP_DELTA  = 1       # min difference (minutes) we still care about

# Altitude optimization settings
MIN_ALTITUDE = 32000  # minimum cruise altitude
MAX_ALTITUDE = 38000  # maximum cruise altitude
ALT_STEP     = 1000   # altitude step size

###############################################################################
def ete_real_minutes():
    subprocess.run([sys.executable, FLIGHT_INFO], check=True)
    j = json.load(open(FLIGHT_JSON))
    return j["ete_hours"] * 60 + j["ete_minutes"]

def apply_plan(path, altitude=36000):
    # 1) write coordinates via your existing dijkstra.py with specified altitude
    subprocess.run([sys.executable, DIJKSTRA, "--altitude", str(altitude)] + path, check=True)
    # 2) upload to LNM
    subprocess.run([sys.executable, PLAN_UPLOAD], check=True)

def yen_ksp(G, source, target, k, weight):
    """Wrapper around networkx shortest_simple_paths that yields the first k."""
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

def save_route_coordinates(path, altitude, rank):
    """Save coordinates for a specific route with rank identifier"""
    output_file = f"../../outputs/trajectories/top_{rank}_route_coordinates.txt"
    subprocess.run([sys.executable, DIJKSTRA, "--altitude", str(altitude)] + path, check=True)
    # Rename the output file to include rank
    import shutil
    shutil.move("path_coordinates.txt", output_file)
    return output_file

###############################################################################
def main():
    G = nx.read_gml(G_PATH)

    # initial guess: speed 450 kt → hours
    for u, v, d in tqdm(G.edges(data=True), desc="Initializing weights"):
        d["w"] = d["weight"] / 450

    src, dst = "67318", "41203"
    global_best_ete = float('inf')
    global_best_path = None
    global_best_altitude = None
    
    # Track top 5 best routes across all altitudes and rounds
    top_routes = []  # List of tuples: (ete, path, altitude, round_info)
    
    # Test different altitudes
    altitudes = range(MIN_ALTITUDE, MAX_ALTITUDE + 1, ALT_STEP)
    
    for altitude in tqdm(altitudes, desc="Testing altitudes"):
        print(f"\n======= TESTING ALTITUDE {altitude} ft =======")
        
        best_ete = None
        prev_best = float('inf')

        for rnd in tqdm(range(1, MAX_ROUNDS + 1), desc=f"Rounds at {altitude}ft"):
            print(f"\n=== Round {rnd} (Alt: {altitude}ft)")

            paths = yen_ksp(G, src, dst, K, weight="w")
            scored = []

            for i, path in enumerate(tqdm(paths, desc="Testing paths"), 1):
                apply_plan(path, altitude)       # writes + uploads with altitude
                ete = ete_real_minutes()         # run flight_info
                scored.append((ete, path, altitude))
                
                # Add to top routes list with additional info
                route_info = {
                    'round': rnd,
                    'altitude': altitude,
                    'path_index': i,
                    'nodes': len(path)
                }
                top_routes.append((ete, path, altitude, route_info))
                
                print(f"  {i:>2}/{K}: ETE {ete:.1f} min  (#nodes {len(path)}) Alt: {altitude}ft")

            # keep best BEAM routes
            scored.sort()
            best_ete, best_path, _ = scored[0]
            print(f"→ best this round: {best_ete:.1f} min at {altitude}ft")
            
            # Update global best
            if best_ete < global_best_ete:
                global_best_ete = best_ete
                global_best_path = best_path
                global_best_altitude = altitude
                print(f"*** NEW GLOBAL BEST: {global_best_ete:.1f} min at {global_best_altitude}ft ***")

            if rnd > 1 and abs(prev_best - best_ete) < STOP_DELTA:
                print("ΔETE < threshold → done with this altitude")
                break
            prev_best = best_ete

            # rank threshold = median of the beam
            beam = scored[:BEAM]
            median = statistics.median([ete for ete, _, _ in beam])

            # update weights
            for ete, path, _ in tqdm(beam, desc="Updating weights"):
                delta = ALPHA_GOOD if ete <= median else ALPHA_BAD
                for u, v in zip(path, path[1:]):
                    G[u][v]["w"] = max(0.001, G[u][v]["w"] + delta)

            # simple monitoring
            df = pd.DataFrame({
                "ETE": [ete for ete, _, _ in beam],
                "Len": [len(p) for _, p, _ in beam],
                "Alt": [alt for _, _, alt in beam]})
            print(df.describe().round(2))

    # Final results
    print(f"\n======= OPTIMIZATION COMPLETE =======")
    print(f"Global best ETE: {global_best_ete:.1f} min")
    print(f"Best altitude: {global_best_altitude} ft")
    print(f"Best path: {global_best_path}")
    
    # Sort and get top 5 routes
    top_routes.sort(key=lambda x: x[0])  # Sort by ETE
    top_5_routes = top_routes[:5]
    
    print(f"\n======= TOP 5 ROUTES =======")
    for i, (ete, path, altitude, info) in enumerate(top_5_routes, 1):
        print(f"{i}. ETE: {ete:.1f} min, Alt: {altitude}ft, Nodes: {info['nodes']}, "
              f"Round: {info['round']}, Path: {info['path_index']}")
    
    # Save top 5 routes to JSON file
    routes_data = {
        "optimization_summary": {
            "total_routes_tested": len(top_routes),
            "altitudes_tested": list(altitudes),
            "global_best_ete_min": global_best_ete,
            "global_best_altitude_ft": global_best_altitude
        },
        "top_5_routes": []
    }
    
    for i, (ete, path, altitude, info) in enumerate(top_5_routes, 1):
        route_data = {
            "rank": i,
            "ete_minutes": ete,
            "cruise_altitude_ft": altitude,
            "flight_level": altitude // 100,
            "path_nodes": path,
            "num_nodes": len(path),
            "optimization_info": info
        }
        routes_data["top_5_routes"].append(route_data)
    
    # Save to JSON file
    results_file = pathlib.Path("optimization_results.json")
    with open(results_file, 'w') as f:
        json.dump(routes_data, f, indent=2)
    print(f"\nTop 5 routes saved to {results_file}")
    
    # Save coordinate files for top 5 routes
    print(f"\nSaving coordinate files for top 5 routes...")
    for i, (ete, path, altitude, info) in enumerate(top_5_routes, 1):
        coord_file = save_route_coordinates(path, altitude, i)
        print(f"Route {i} coordinates saved to {coord_file}")
    
    # Apply the final best solution
    if global_best_path and global_best_altitude:
        apply_plan(global_best_path, global_best_altitude)
        print(f"Final best plan applied with altitude {global_best_altitude}ft")

    out = G_PATH.with_stem(G_PATH.stem + "_reinforced")
    nx.write_gml(G, out)
    print(f"\nReinforced graph saved to {out}")

if __name__ == "__main__":
    main()
