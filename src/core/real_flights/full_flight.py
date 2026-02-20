"""
Program to calculate flight duration and mean duration of the flights on a given csv file stated in variable
"filtered_file", file must contain colum "Time Over"
"""

import pandas as pd
"""
"ECTRL ID","Sequence Number","Time Over","Flight Level","Latitude","Longitude"
"""

filtered_file = '../../../data/raw/201912/Flight_Points_Actual_20191201_20191231.csv'

df = pd.read_csv(filtered_file)

df['Time Over'] = pd.to_datetime(df['Time Over'], errors='coerce', dayfirst=True)

# Agrupaciones por ID
duraciones = (
    df.groupby("ECTRL ID")['Time Over']
      .agg(inicio='min', fin='max')
      .reset_index()
)

duraciones['Duracion'] = duraciones['fin'] - duraciones['inicio']
duracion_media = duraciones['Duracion'].mean()

# Pasamos a Horas/Mins
duraciones['Duracion_horas'] = duraciones['Duracion'].dt.total_seconds() / 3600
duracion_media_horas = duracion_media.total_seconds() / 3600

# Printeadas
# Por vuelo
print('Duracion de cada vuelo')
#print(duraciones[['ECTRL ID', 'Duracion']])
# Media
print('Duracion Media de los vuelos')
print(duracion_media)