#!/bin/bash
echo "--- Configurando Entorno Experimental TFG ---"

# 1. Crear entorno virtual (opcional si usas conda)
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 3. Crear carpetas necesarias si no existen
mkdir -p data/raw data/processed outputs/graphs outputs/trajectories outputs/logs

# 4. Verificación de Little Navmap
if command -v littlenavmap &> /dev/null
then
    echo "✓ Little Navmap detectado."
else
    echo "! Advertencia: Asegúrate de que 'littlenavmap' esté en tu PATH o configurado en config.py"
fi

echo "--- Instalación completada. Usa 'source venv/bin/activate' para empezar. ---"