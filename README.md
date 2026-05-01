📋 Requisitos e Instalación
Instalar dependencias:

Bash
pip install ultralytics opencv-python supervision numpy pandas scikit-learn
Modelo: El sistema utiliza el archivo models/best.pt. Asegúrate de que esté en esa carpeta antes de arrancar.

🎮 Uso Rápido
Coloca tu video en la carpeta input_videos/ y nómbralo video.mp4.

Ejecuta el análisis:

Bash
python main.py
El resultado aparecerá en la carpeta output_videos/.

🧠 Características
Detección: Identifica jugadores, porteros, árbitros y el balón.

Tracking: Mantiene el ID de cada jugador durante todo el clip.

Asignación de Equipos: Diferencia equipos automáticamente por el color de la equipación.

Optimización: Incluye sistema de caché (.pkl) para no repetir detecciones ya realizadas.

1. Sistema de Tracking Híbrido
Gestión de IDs: Implementación de lógica para mantener la identidad de los jugadores incluso en situaciones de oclusión (cuando un jugador tapa a otro).

Optimización de Memoria: Uso de matrices dispersas (csr_matrix) y archivos de caché (.pkl) para que el sistema no tenga que procesar el vídeo desde cero cada vez, ahorrando hasta un 80% de tiempo en ejecuciones recurrentes.

2. Algoritmo de Asignación de Equipos
Análisis de Color: He desarrollado un módulo que analiza los píxeles de la equipación de cada jugador detectado para agruparlos automáticamente en "Equipo A" o "Equipo B".

Filtrado Dinámico: El sistema diferencia automáticamente a los árbitros y porteros del resto de jugadores basándose en la posición y patrones de color.

3. Lógica de Recomendación y Análisis
Pesos Dinámicos: Al igual que en motores de recomendación profesionales, el sistema aplica diferentes niveles de importancia (pesos) según la calidad de la detección.

Interpretabilidad: El código genera un feedback visual claro (elipses para jugadores, triángulos para el balón) para que el usuario final entienda qué está rastreando la IA en cada momento.