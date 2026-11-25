"""Prueba local sin red: genera un Dataset falso con la estructura de ECMWF y corre productos."""
import shutil
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
import config, productos

RAIZ = Path(__file__).resolve().parents[1]
corrida = pd.Timestamp("2026-11-25 00:00")
pasos = pd.to_timedelta(config.PASOS, unit="h")
lat = np.arange(-10, -60.01, -0.25); lon = np.arange(-85, -60.01, 0.25)
rng = np.random.default_rng(1)
nt, ny, nx = len(pasos), len(lat), len(lon)
h = np.array(config.PASOS)[:, None, None]
LAT = lat[None, :, None]
t = 273.15 + 30 + (LAT + 17) * 0.5 + 8 * np.sin(2*np.pi*(h - 18)/24) + rng.normal(0, .5, (nt, ny, nx))
lluvia = np.clip(rng.gamma(0.3, 0.6, (nt, ny, nx)) * (LAT < -33) * 1e-3, 0, None)
tp = np.cumsum(lluvia, axis=0); tp[0] = 0
u = rng.normal(3, 2, (nt, ny, nx)); v = rng.normal(-2, 2, (nt, ny, nx))
msl = 101300 + rng.normal(0, 200, (nt, ny, nx))
dims = ("step", "latitude", "longitude")
ds = xr.Dataset({"t2m": (dims, t), "tp": (dims, tp), "u10": (dims, u), "v10": (dims, v), "msl": (dims, msl)},
                coords={"step": pasos, "latitude": lat, "longitude": lon + 360,
                        "time": corrida, "valid_time": ("step", corrida + pasos)})
ds = productos.preparar(ds)
sitio = RAIZ / "site"
if sitio.exists(): shutil.rmtree(sitio)
shutil.copytree(RAIZ / "web", sitio)
meta = productos.generar(ds, {"resolucion": "0.25 (SINTÉTICO)", "corrida": corrida.isoformat()}, sitio / "datos")
print(len(meta["ciudades"]), "ciudades,", len(meta["mapas"]), "mapas")
