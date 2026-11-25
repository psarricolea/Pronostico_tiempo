"""Descarga la última corrida IFS de ECMWF Open Data (sin cuenta, CC-BY-4.0)."""
import sys
from pathlib import Path

from ecmwf.opendata import Client

import config


def descargar(destino: Path) -> dict:
    destino.parent.mkdir(parents=True, exist_ok=True)
    ultimo_error = None
    for resol in config.RESOLUCIONES:
        try:
            cliente = Client(source="ecmwf", model="ifs", resol=resol)
            # Última corrida que ya tenga publicado el horizonte completo
            fecha = cliente.latest(type="fc", step=max(config.PASOS), param="2t")
            print(f"[descarga] resol={resol} corrida={fecha:%Y-%m-%d %H}z", flush=True)
            cliente.retrieve(
                date=fecha.strftime("%Y%m%d"),
                time=fecha.hour,
                type="fc",
                step=config.PASOS,
                param=config.PARAMETROS,
                target=str(destino),
            )
            return {"resolucion": resol.replace("p", "."), "corrida": fecha.isoformat()}
        except Exception as e:  # 0.1° puede no estar disponible aún para la corrida
            print(f"[descarga] falló resol={resol}: {e}", file=sys.stderr, flush=True)
            ultimo_error = e
    raise RuntimeError(f"No se pudo descargar ninguna resolución: {ultimo_error}")
