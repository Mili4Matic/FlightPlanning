# Assumes:  graph at ../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml
#           usa -> dijkstra.py   writes path_coordinates.txt
#           plan_uploader.py  consumes that file
#           flight_info.py    writes flight_data.json

import networkx as nx, json, subprocess, time, pathlib, sys

# Get the directory of the current script
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

# Paths assuming we run from algorithms directory
GRAPH_FILE   = SCRIPT_DIR / "../../outputs/graphs/waypoints_graph_LEMD-UUEE.gml"
DIJKSTRA_PY  = SCRIPT_DIR / "./dijkstra.py"  # dijkstra.py is in same directory when run from algorithms
PLAN_UPLOADER_PY = SCRIPT_DIR / "../core/plan_uploader.py"
FLIGHT_INFO_PY = SCRIPT_DIR / "../core/flight_info.py"
FLIGHT_DATA_JSON = SCRIPT_DIR / "../core/flight_data.json"

ALPHA        = 0.3          # learning-rate
MAX_ITER     = 50
CRUISE_KT    = 450          # first-guess groundspeed
STOP_THRESH  = 2            # minutes of ETE error at which we stop

# ------------------------------------------------------------------ helpers
def to_hours(dist_nm, gskt=CRUISE_KT):
    return dist_nm / gskt

def ete_pred(path, G):
    return sum(G[u][v]["w"] for u, v in zip(path, path[1:]))

def eto_real():
    """Run flight_info.py and read the freshly written JSON."""
    subprocess.run([sys.executable, str(FLIGHT_INFO_PY)], check=True)
    with open(FLIGHT_DATA_JSON) as f:
        j = json.load(f)
    return j["ete_hours"] * 60 + j["ete_minutes"]          # minutes

def distribute_error(path, delta_min, G, alpha=ALPHA):
    delta_h = delta_min / 60
    per_edge = delta_h / (len(path) - 1)
    min_weight = 0.001  # Minimum weight to prevent negative values
    
    for u, v in zip(path, path[1:]):
        # Apply the weight update
        new_weight = G[u][v]["w"] + alpha * per_edge
        # Ensure weight doesn't go below minimum threshold
        G[u][v]["w"] = max(new_weight, min_weight)

# ------------------------------------------------------------------ main
def main():
    G = nx.read_gml(str(GRAPH_FILE))

    # 0) initial weight = time (h) from distance_nm
    for u, v, d in G.edges(data=True):
        d["w"] = to_hours(d["weight"])   # 'weight' was distance (km or NM) – adapt!

    for it in range(1, MAX_ITER + 1):
        print(f"\n── Iteration {it}")

        # 1) shortest path with current weights
        path = nx.dijkstra_path(G, "67318", "41203", weight="w")
        print("  nodes:", len(path), " → writing to coordinates file")
        
        # Debug: show some weight info
        avg_weight = sum(G[u][v]["w"] for u, v in zip(path, path[1:])) / (len(path) - 1)
        print(f"  average edge weight on path: {avg_weight:.4f} hours")
        
        subprocess.run([sys.executable, str(DIJKSTRA_PY)], check=True)

        # 2) upload plan (assumes plan_uploader.py handles coordinates)
        subprocess.run([sys.executable, str(PLAN_UPLOADER_PY)], check=True)

        # 3) let Little Navmap refresh (adjust if LNM needs longer)
        time.sleep(2)

        # 4) read real ETE
        ete_real_min = eto_real()
        ete_pred_min = ete_pred(path, G) * 60
        err = ete_real_min - ete_pred_min
        print(f"  ETE real {ete_real_min:.1f} min   •   pred {ete_pred_min:.1f} min   →  δ = {err:+.1f}")

        if abs(err) < STOP_THRESH:
            print("  error below threshold – stopping")
            break

        # 5) update weights along the path
        distribute_error(path, err, G)
        print("  weights updated")

    # Save tuned graph
    tuned = pathlib.Path(GRAPH_FILE).with_stem(pathlib.Path(GRAPH_FILE).stem + "_tuned")
    nx.write_gml(G, str(tuned))
    print(f"\nTuned graph saved to {tuned}")

if __name__ == "__main__":
    main()
