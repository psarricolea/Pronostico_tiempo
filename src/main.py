"""Punto de entrada: descarga la última corrida y genera el sitio en ./site."""
import shutil
from pathlib import Path

import descargar
import productos

RAIZ = Path(__file__).resolve().parents[1]
GRIB = RAIZ / "tmp" / "ifs.grib2"
SITIO = RAIZ / "site"


def main():
    info = descargar.descargar(GRIB)
    ds = productos.leer_grib(GRIB)
    if SITIO.exists():
        shutil.rmtree(SITIO)
    shutil.copytree(RAIZ / "web", SITIO)
    meta = productos.generar(ds, info, SITIO / "datos")
    print(f"[ok] {len(meta['ciudades'])} meteogramas, {len(meta['mapas'])} mapas")


if __name__ == "__main__":
    main()
