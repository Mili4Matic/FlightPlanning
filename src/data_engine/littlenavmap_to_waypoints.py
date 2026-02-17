"""Ruta al archivo
SQL que contiene los Waypoints en
LittleNavMap
~/.config/ABarthel/little_navmap_db/little_navmap_navigraph.sqlite
"""

""" Este script se encarga de extraer los waypoints de la base de datos SQLite de Little Navmap y guardarlos en un archivo CSV.
Dentro del directorio /little_navmap_db/ se encuentran distintos archivos SQLite:
little_navmap_.sqlite                  little_navmap_navigraph.sqlite     little_navmap_userdata.sqlite
little_navmap_logbook.sqlite           little_navmap_onlinedata.sqlite    little_navmap_userdata_backup.sqlite
little_navmap_logbook_backup.sqlite    little_navmap_track.sqlite         little_navmap_userdata_backup.sqlite.1
little_navmap_logbook_backup.sqlite.1  little_navmap_userairspace.sqlite
"""

import sqlite3
import pandas as pd

# Ruta al archivo SQLite de Little Navmap
# este es el default path de instalacion en WSL
db_path = "~/.config/ABarthel/little_navmap_db/little_navmap_navigraph.sqlite"
output_csv = "../../data/processed/waypoints.csv"
#output_csv = "./data/waypoints.csv"

# Conectar a la base de datos SQLite
conn = sqlite3.connect(db_path)

# Consulta SQL para obtener los waypoints
query = "SELECT * FROM waypoints"

# Leer los datos en un DataFrame de pandas
df = pd.read_sql_query(query, conn)
df.to_csv(output_csv, index=False)

print(f"{len(df)} Waypoints exportados a {output_csv}")
