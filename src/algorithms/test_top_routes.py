#!/usr/bin/env python3
"""
Quick test script to verify the top routes saving functionality
"""
import json
import os

def test_optimization_results():
    """Test if optimization results are saved correctly"""
    results_file = "../../outputs/logs/optimization_results.json"
    
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        print("=== OPTIMIZATION RESULTS TEST ===")
        print(f"Total routes tested: {data['optimization_summary']['total_routes_tested']}")
        print(f"Altitudes tested: {data['optimization_summary']['altitudes_tested']}")
        print(f"Global best ETE: {data['optimization_summary']['global_best_ete_min']} min")
        print(f"Global best altitude: {data['optimization_summary']['global_best_altitude_ft']} ft")
        
        print(f"\n=== TOP 5 ROUTES ===")
        for route in data['top_5_routes']:
            print(f"Rank {route['rank']}: {route['ete_minutes']:.1f} min at FL{route['flight_level']} "
                  f"({route['num_nodes']} nodes)")
        
        # Check for coordinate files
        print(f"\n=== COORDINATE FILES ===")
        for i in range(1, 6):
            coord_file = f"../../outputs/trajectories/top_{i}_route_coordinates.txt"
            if os.path.exists(coord_file):
                print(f"✓ {coord_file} exists")
            else:
                print(f"✗ {coord_file} missing")
    else:
        print("optimization_results.json not found")

if __name__ == "__main__":
    test_optimization_results()
