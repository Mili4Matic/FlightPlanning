import os
from pathlib import Path

# --- RUTAS DE DIRECTORIOS ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "outputs"
PERFORMANCE_DIR = BASE_DIR / "aircraft_performance"

# --- CONFIGURACIÓN LITTLE NAVMAP ---
# 'utilizamos ./littlenavmap' si está en el PATH o ruta completa o la ejecucion no funciona
LNM_EXE = "littlenavmap" 
DEFAULT_AIRCRAFT = PERFORMANCE_DIR / "a320.lnmperf"
LNM_URL = "http://localhost:8965/html/flightplan_doc.html"

# --- ESCENARIO: LEMD (Madrid) -> UUEE (Moscú) ---
# Bounding Box para filtrado de Waypoints/Airways
BBOX = {
    "MAX_LAT": 56.333140,
    "MIN_LAT": 40.111860,
    "MAX_LON": 38.058696,
    "MIN_LON": -4.034539
}

# Diccionario de procedimientos SID (Salida)
SIDS = {
    "PINA2N": {"exit_node": "67318", "string": "LEMD/36L PINA2N"},
    "BARA2N": {"exit_node": "67441", "string": "LEMD/36L BARA2N"}
}

# Diccionario de procedimientos STAR (Llegada)
STARS = {
    "SUSOR1": {"entry_node": "41203", "string": "UUEE/SUSOR.I06L"},
    "GEKLA1": {"entry_node": "40867", "string": "UUEE/GEKLA.I06L"}
}

# Selección actual para la ejecución
ACTIVE_SID = "PINA2N"
ACTIVE_STAR = "SUSOR1"

# --- PARÁMETROS DE OPTIMIZACIÓN ---
K_PATHS = 15
ALPHA_GOOD = -0.05
ALPHA_BAD = 0.05
DEFAULT_ALTITUDE = 36000 # ft