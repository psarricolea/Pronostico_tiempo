"""Configuración del sistema de pronóstico."""

# Dominio de recorte (Chile continental + margen)
LAT_N, LAT_S = -17.0, -56.5
LON_W, LON_E = -78.0, -65.0

# Resolución: se intenta 0.1° y, si no está disponible, 0.25°
RESOLUCIONES = ["0p1", "0p25"]

# Horizonte: 10 días. IFS HRES: cada 3 h hasta 144 h, luego cada 6 h.
PASOS = list(range(0, 145, 3)) + list(range(150, 241, 6))

# Variables (nombres ECMWF Open Data)
PARAMETROS = ["2t", "tp", "10u", "10v", "msl"]

# Día "local" para acumulados: de 06 UTC a 06 UTC (03 a 03 hora de Chile).
# 06 UTC existe tanto en pasos de 3 h como de 6 h para corridas 00z y 12z.
HORA_CORTE_UTC = 6
DIAS_MAPA = 7

ZONA_HORARIA = "America/Santiago"

CIUDADES = {
    "Arica": (-18.48, -70.31),
    "Iquique": (-20.21, -70.15),
    "Antofagasta": (-23.65, -70.40),
    "Copiapó": (-27.37, -70.33),
    "La Serena": (-29.90, -71.25),
    "Valparaíso": (-33.05, -71.62),
    "Santiago": (-33.45, -70.66),
    "Rancagua": (-34.17, -70.74),
    "Talca": (-35.43, -71.66),
    "Chillán": (-36.61, -72.10),
    "Concepción": (-36.83, -73.05),
    "Temuco": (-38.74, -72.60),
    "Valdivia": (-39.81, -73.25),
    "Puerto Montt": (-41.47, -72.94),
    "Coyhaique": (-45.57, -72.07),
    "Punta Arenas": (-53.16, -70.92),
}

# Ciudades secundarias: punto más pequeño y nombre solo al pasar el cursor
CIUDADES_SECUNDARIAS = {
    "Putre": (-18.20, -69.56),
    "Calama": (-22.46, -68.93),
    "San Pedro de Atacama": (-22.91, -68.20),
    "Tocopilla": (-22.09, -70.20),
    "Vallenar": (-28.58, -70.76),
    "Ovalle": (-30.60, -71.20),
    "Los Andes": (-32.83, -70.60),
    "San Antonio": (-33.59, -71.61),
    "San Fernando": (-34.59, -70.99),
    "Curicó": (-34.98, -71.24),
    "Linares": (-35.85, -71.59),
    "Los Ángeles": (-37.47, -72.35),
    "Angol": (-37.80, -72.71),
    "Villarrica": (-39.28, -72.23),
    "Osorno": (-40.57, -73.13),
    "Castro": (-42.48, -73.76),
    "Chaitén": (-42.92, -72.71),
    "Puerto Aysén": (-45.40, -72.69),
    "Cochrane": (-47.25, -72.57),
    "Puerto Natales": (-51.73, -72.51),
    "Puerto Williams": (-54.93, -67.61),
}
