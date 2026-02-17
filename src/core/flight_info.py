"""
 This code is part of the Thesis Project "NAME-TBD"
 Universidad Autonoma de Madrid, 2025/26
 Author: Alejandro Milikowsky 
 Contact: alejandro.milikowsky@uam.es / alejandro.milikowsky@estudiante.uam.es
 All code written and verified by the author.
 For academic use only.

The code scraps some important information from a self-hosted
LittleNav Map instance flight plan, focusing mainly in:
    - Expcted Total Distance
    - Expected time Enroute
    - Cruise Altitude
    - Expected consumed Fuel
"""

import re, requests
from bs4 import BeautifulSoup as BS
import json
import os

URL = "http://localhost:8965/html/flightplan_doc.html"
num = lambda s: int(''.join(filter(str.isdigit, s))) # eliminamos , . y unidades

html = requests.get(URL, timeout=5).text # realizamos el request
soup = BS(html, "lxml") # preparamos la soup

# Totales del parrafo inicial
# Buscamos, en el html como texto plano: Distancia, Tiempo estimado de vuelo y altitud de crucero
# Updated to handle the actual HTML structure from Little Navmap
try:
    p = next(p for p in soup.find_all("p") if "Distance" in p.text)
except StopIteration:
    # If we can't find Distance in a paragraph, search in the entire HTML
    p_text = soup.get_text()
    if "Distance" not in p_text:
        raise Exception("Could not find flight plan data in Little Navmap HTML")
    p = type('MockP', (), {'text': p_text})()

dist = num(re.search(r'Distance\s+([0-9.,]+)\s*NM', p.text)[1])
h, m = map(int, re.search(r'(\d+)\s*h\s*(\d+)\s*m', p.text).groups())
alt  = num(re.search(r'Cruising altitude\s+([0-9.,]+)\s*ft', p.text)[1])

# Combustible usado = primera – ultima celda “Fuel Rem. lbs” (15.ª col.) ─> Ver flight_plan_sim_sample.html
# para ver la estructura
fuel = [num(td.text) for td in soup.select("table tr td:nth-of-type(15)") if td.text.strip()]
fuel_used = fuel[0] - fuel[-1]

print(f"Distancia: {dist} NM")
print(f"ETE      : {h:02d}:{m:02d}")
print(f"Cruise   : {alt} ft")
print(f"Fuel     : {fuel_used} lb")
# Create a dictionary with the flight data
flight_data = {
    "distance_nm": dist,
    "ete_hours": h,
    "ete_minutes": m,
    "cruise_altitude_ft": alt,
    "fuel_used_lb": fuel_used
}

# Define the output file path in the current directory
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flight_data.json")

# Save the data to a JSON file
with open(output_file, "w") as f:
    json.dump(flight_data, f, indent=4)

print(f"Flight data saved to {output_file}")