"""
Program to calculate flight duration and mean duration of the flights on a given csv file stated in variable
"filtered_file", file must contain colum "Timestamp"
"""

import pandas as pd
import json
import os
"""
ID | Sequence Number | Flight Level | Latitude | Longitude | LatLon | Flight Level Format | Timestamp | Latitude_decimal | Longitude_decimal
"""

filtered_file = '../../data/processed/filtered_flights_actual_LEMD-UUEE.csv'

df = pd.read_csv(filtered_file)

df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce', dayfirst=True)

# Agrupaciones por ID
duraciones = (
  df.groupby("ID")['Timestamp']
    .agg(inicio='min', fin='max')
    .reset_index()
)

duraciones['Duracion'] = duraciones['fin'] - duraciones['inicio']
duracion_media = duraciones['Duracion'].mean()
duracion_maxima = duraciones['Duracion'].max()
duracion_minima = duraciones['Duracion'].min()

# Pasamos a Horas/Mins
duraciones['Duracion_horas'] = duraciones['Duracion'].dt.total_seconds() / 3600
duracion_media_horas = duracion_media.total_seconds() / 3600
duracion_maxima_horas = duracion_maxima.total_seconds() / 3600
duracion_minima_horas = duracion_minima.total_seconds() / 3600

# Printeadas
# Por vuelo
print('Duracion de cada vuelo')
print(duraciones[['ID', 'Duracion']])
# Media
print('Duracion Media de los vuelos')
print(duracion_media)
# Máxima
print('Duracion Maxima de los vuelos')
print(duracion_maxima)
# Mínima
print('Duracion Minima de los vuelos')
print(duracion_minima)

# Crear directorio si no existe
os.makedirs('./trajectories', exist_ok=True)

# Preparar datos para JSON
output_data = {
    "duracion_por_vuelo": [
        {
            "ID": row['ID'],
            "duracion": str(row['Duracion']),
            "duracion_horas": row['Duracion_horas']
        }
        for _, row in duraciones.iterrows()
    ],
    "estadisticas": {
        "duracion_media": str(duracion_media),
        "duracion_media_horas": duracion_media_horas,
        "duracion_maxima": str(duracion_maxima),
        "duracion_maxima_horas": duracion_maxima_horas,
        "duracion_minima": str(duracion_minima),
        "duracion_minima_horas": duracion_minima_horas
    }
}

# Guardar en JSON
with open('./trajectories/duracion_vuelos.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print("\nDatos guardados en ./trajectories/duracion_vuelos.json")
