# Pronóstico del tiempo para Chile (ECMWF IFS)

Sistema automático que dos veces al día descarga la última corrida del modelo
**IFS de ECMWF** (Open Data, gratuito, sin cuenta, licencia CC-BY-4.0), recorta Chile
y publica en **GitHub Pages**:

- Meteogramas de 10 días para 16 ciudades (T 2 m, precipitación, viento 10 m, PNM).
- Tabla diaria de máx./mín./precipitación por ciudad.
- Mapas diarios (7 días) de precipitación acumulada y temperatura máxima.

Intenta primero la resolución **0,1°** y, si aún no está publicada, usa **0,25°**.

## Puesta en marcha

1. Crear un repositorio nuevo en GitHub y subir estos archivos.
2. *Settings → Pages → Build and deployment → Source:* **GitHub Actions**.
3. *Actions → Pronóstico ECMWF → Run workflow* para la primera corrida.
4. El sitio queda en `https://<usuario>.github.io/<repo>/` y se actualiza
   a las 10:20 y 22:20 UTC.

Los GRIB no se guardan en el repositorio: se descargan, se procesan y se descartan
en cada corrida. Solo se publican PNG y un JSON.

## Estructura

```
src/config.py     dominio, ciudades, pasos, variables
src/descargar.py  descarga con ecmwf-opendata (0,1° → 0,25°)
src/productos.py  lectura GRIB, meteogramas, mapas y JSON
src/main.py       orquestación → ./site
src/prueba_sintetica.py  prueba local sin red con datos falsos
web/index.html    página (selector de ciudad + mapas por día)
```

Para agregar ciudades o cambiar el dominio, editar `src/config.py`.

## Prueba local

```bash
pip install -r requirements.txt
cd src && python main.py          # con datos reales
# o: python prueba_sintetica.py   # sin red
python -m http.server -d ../site  # abrir http://localhost:8000
```

## Notas

- Valores en el punto de grilla más cercano a cada ciudad, sin corrección de sesgo.
  En ciudades costeras o de valle angosto el punto puede caer en el mar o en ladera.
- La T máx. de los mapas sale de las salidas de 3/6 h y subestima levemente la máxima real.
- Día de los mapas: 03 h a 03 h de Chile (06 a 06 UTC).

## Próximos pasos posibles

- Anomalías respecto de la climatología **ERA5** 1991–2020 (requiere clave CDS
  como *secret* `CDSAPI_KEY` y un archivo de climatología precalculado).
- Ensamble IFS/AIFS ENS: probabilidad de lluvia > 1 mm y percentiles de temperatura.
- Verificación contra estaciones (DMC, red Ecowitt).

Fuente: *Adapted from ECMWF IFS forecast data by ECMWF, licensed under CC BY 4.0.*
